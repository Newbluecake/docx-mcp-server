---
feature: docx-full-features
review_date: 2026-01-20
reviewer: spec-plan-reviewer
status: needs-revision
---

# 计划评审报告：Docx MCP Server 全功能重构

## 概要

| 项目 | 内容 |
|------|------|
| **计划名称** | docx-full-features |
| **评审日期** | 2026-01-20 |
| **整体评估** | ⚠️ 需修改 |
| **风险等级** | 中 |

**总体评价**：该设计方案在架构层面有创新，混合上下文和属性引擎的设计理念合理。但存在若干技术实现细节遗漏、MCP 协议兼容性问题以及模板填充场景覆盖不完整的情况。建议在实施前完善以下关键问题。

---

## 1. 架构合理性评审

### 1.1 混合上下文 (Hybrid Context) 设计

**优点**：
- 减少 Token 消耗，提升 LLM 调用效率
- 符合 "连续操作" 的自然工作流

**问题与建议**：

#### [问题 A-1] 上下文歧义风险 - 中等风险

**问题描述**：设计中 `last_created_id` 和 `last_accessed_id` 两个指针可能导致歧义。当 Claude 执行一系列混合操作时，难以预测哪个 ID 会被使用。

**示例场景**：
```python
# 步骤1: 创建段落 -> last_created_id = para_1
para_id = docx_add_paragraph(session_id, "Hello")
# 步骤2: 读取另一个表格 -> last_accessed_id = table_1
table_info = docx_get_table(session_id, index=0)
# 步骤3: 添加 run，不传 parent_id
# 问题: 应该用 last_created_id (para_1) 还是 last_accessed_id (table_1)?
run_id = docx_add_run(session_id, text="World")  # 设计说用 last_created_id
```

**建议方案**：
1. 明确文档化规则：创建类操作用 `last_created_id`，修改类操作用 `last_accessed_id`
2. 在返回值中包含当前上下文状态，便于 Claude 追踪：
   ```json
   {"element_id": "para_1", "context": {"last_created": "para_1", "last_accessed": "para_1"}}
   ```
3. 考虑增加 `docx_get_context(session_id)` 工具，让 Claude 可以查询当前上下文状态

#### [问题 A-2] 类型安全检查不足 - 低风险

**问题描述**：设计文档提到 "需类型检查"，但未详细说明检查机制。当 `last_created_id` 指向 Table 而调用 `docx_add_run()` 时，如何处理？

**建议方案**：
在 `Session` 类中增加类型元数据：
```python
class Session:
    object_registry: Dict[str, Any]
    object_types: Dict[str, str]  # {"para_1": "Paragraph", "table_1": "Table"}
    
    def get_object_with_type_check(self, obj_id: str, expected_type: str) -> Any:
        obj = self.object_registry.get(obj_id)
        if obj and self.object_types.get(obj_id) != expected_type:
            raise TypeError(f"Expected {expected_type}, got {self.object_types.get(obj_id)}")
        return obj
```

### 1.2 属性引擎 (Property Engine) 设计

**优点**：
- 统一接口减少工具数量
- 符合 python-docx 对象模型

**问题与建议**：

#### [问题 A-3] 属性映射表不完整 - 中等风险

**问题描述**：设计文档中的 `MAP` 示例过于简略，未覆盖 python-docx 的常用属性。

**建议补充的属性映射**：

| 类别 | 属性 | python-docx 路径 | 类型转换 |
|------|------|------------------|----------|
| Font | `name` | `run.font.name` | str |
| Font | `size` | `run.font.size` | Pt() |
| Font | `underline` | `run.font.underline` | WD_UNDERLINE / bool |
| Font | `strike` | `run.font.strike` | bool |
| Font | `subscript` | `run.font.subscript` | bool |
| Font | `superscript` | `run.font.superscript` | bool |
| Paragraph | `first_line_indent` | `paragraph_format.first_line_indent` | Pt() |
| Paragraph | `left_indent` | `paragraph_format.left_indent` | Pt() |
| Paragraph | `line_spacing` | `paragraph_format.line_spacing` | float / Pt() |
| Paragraph | `space_before` | `paragraph_format.space_before` | Pt() |
| Paragraph | `space_after` | `paragraph_format.space_after` | Pt() |
| Table | `autofit` | `table.autofit` | bool |
| Cell | `vertical_alignment` | `cell.vertical_alignment` | WD_CELL_VERTICAL_ALIGNMENT |
| Cell | `width` | `cell.width` | Inches() / Pt() |

**建议方案**：
1. 创建完整的属性映射配置文件（如 `property_map.yaml`）
2. 实现属性发现机制，对未知属性返回明确错误而非静默忽略

#### [问题 A-4] 复杂属性的嵌套处理 - 低风险

**问题描述**：设计中提到 "递归设值逻辑"，但未说明如何处理多层嵌套属性，如 `font.color.rgb`。

**建议方案**：
```python
def set_nested_attr(obj, path: str, value):
    """递归设置嵌套属性，如 'font.color.rgb'"""
    parts = path.split('.')
    for part in parts[:-1]:
        obj = getattr(obj, part)
    setattr(obj, parts[-1], value)
```

---

## 2. MCP 协议兼容性评审

### 2.1 JSON 参数结构

#### [问题 M-1] 复杂 JSON 结构对 LLM 的挑战 - 高风险

**问题描述**：`docx_set_properties` 接受嵌套的 JSON 对象作为参数。根据 MCP 最佳实践，复杂的嵌套结构可能增加 LLM 生成错误的概率。

**设计示例**：
```json
{
  "font": {
    "name": "Arial",
    "size": 12,
    "bold": true,
    "color": "FF0000"
  },
  "paragraph_format": {
    "alignment": "center",
    "space_after": 12
  }
}
```

**风险分析**：
- LLM 可能遗漏必要的嵌套层级
- 拼写错误（如 `paragrph_format`）会导致静默失败
- 数值类型容易混淆（size 是 pt 还是像素？）

**建议方案**：
1. **保留简化版快捷工具**：为最常用的操作保留独立工具（如 `docx_set_bold`），与 `docx_set_properties` 并存
2. **严格的 JSON Schema 验证**：在工具定义中提供详细的 JSON Schema：
   ```python
   @mcp.tool(
       input_schema={
           "type": "object",
           "properties": {
               "session_id": {"type": "string"},
               "element_id": {"type": "string"},
               "properties": {
                   "type": "object",
                   "properties": {
                       "font": {
                           "type": "object",
                           "properties": {
                               "bold": {"type": "boolean"},
                               "size": {"type": "number", "description": "Font size in points (e.g., 12)"},
                               # ...
                           }
                       }
                   }
               }
           },
           "required": ["session_id", "properties"]
       }
   )
   def docx_set_properties(...):
   ```
3. **提供清晰的错误消息**：对无效属性名返回建议：
   ```
   Error: Unknown property 'paragrph_format'. Did you mean 'paragraph_format'?
   ```

#### [问题 M-2] 工具描述不够详细 - 中等风险

**问题描述**：设计文档未包含完整的工具描述（docstring），而 MCP 协议要求清晰的描述帮助 LLM 理解如何使用工具。

**建议方案**：
为每个新工具提供详细描述，包含：
- 功能说明
- 参数说明（含类型、取值范围、默认值）
- 返回值说明
- 使用示例

**示例**：
```python
@mcp.tool()
def docx_set_properties(
    session_id: str,
    properties: dict,
    element_id: str = None
) -> str:
    """
    Set multiple properties on a document element (Run, Paragraph, Table, Cell).
    
    This tool allows batch property updates in a single call, reducing token usage.
    If element_id is not provided, operates on the last accessed element.
    
    Args:
        session_id: The active session ID.
        properties: A dictionary of properties to set. Supported keys:
            - font: {bold: bool, italic: bool, size: float (pt), color: "RRGGBB", name: str}
            - paragraph_format: {alignment: "left"|"center"|"right"|"justify", 
                                 space_before: float (pt), space_after: float (pt)}
        element_id: Optional. The element to modify. Defaults to last_accessed_id.
    
    Returns:
        str: Success message with list of applied properties.
    
    Example:
        docx_set_properties(session_id, {"font": {"bold": true, "size": 14}})
    """
```

### 2.2 工具命名规范

**评估**：当前设计的工具命名符合 MCP 规范（`docx_` 前缀 + 动词）。

**建议**：保持一致性，确保所有新工具遵循相同模式。

---

## 3. 实现可行性评审

### 3.1 任务拆分评估

| 任务 | 评估 | 风险点 |
|------|------|--------|
| T-001: 混合上下文 | 可行 | 需补充类型检查逻辑 |
| T-002: 属性引擎 | 可行 | 需完善属性映射表 |
| T-003: 工具重构 | 可行 | 需考虑向后兼容 |
| T-004: set_properties | 可行 | 需完善 JSON Schema |
| T-005: 导航工具 | 可行 | 安全检查需详细设计 |
| T-006: 表格高级操作 | **需补充** | 深拷贝实现有技术挑战 |
| T-007: 图片和替换 | **需补充** | 替换逻辑需处理 Run 分割问题 |
| T-008: E2E 测试 | 可行 | - |

### 3.2 遗漏的关键步骤

#### [问题 I-1] 表格深拷贝实现细节缺失 - 高风险

**问题描述**：`docx_copy_table` 的实现未在设计中详细说明。python-docx 没有内置的表格克隆方法。

**技术调研结果**：
根据 [Stack Overflow 讨论](https://stackoverflow.com)，python-docx 中复制表格需要：
1. 深拷贝底层 XML 元素 (`_tbl`)
2. 将新 XML 元素插入文档

**建议实现方案**：
```python
import copy
from docx.oxml.table import CT_Tbl

def copy_table(document, table):
    """深度复制表格"""
    tbl = table._tbl
    new_tbl = copy.deepcopy(tbl)
    
    # 找到原表格位置并在其后插入
    paragraph = document.add_paragraph()  # 创建占位段落
    paragraph._p.addnext(new_tbl)
    paragraph._element.getparent().remove(paragraph._element)
    
    # 返回新表格对象
    return Table(new_tbl, document)
```

**风险**：
- 依赖 python-docx 内部 API (`_tbl`)，可能在库升级时失效
- 需要处理表格样式引用

**建议**：在任务 T-006 中添加子任务，专门研究和测试表格复制方案。

#### [问题 I-2] 文本替换的 Run 分割问题 - 高风险

**问题描述**：`docx_replace_text` 需要处理占位符被 Word 分割到多个 Run 中的情况。

**示例**：
用户在 Word 中输入 `{{name}}`，但 Word 可能将其存储为：
- Run 1: `{{na`
- Run 2: `me}}`

**技术调研结果**：
根据 [python-docx 相关讨论](https://github.com)，这是一个常见问题，解决方案包括：
1. 在模板制作时确保占位符不被分割（用户教育）
2. 实现跨 Run 的文本搜索和替换

**建议实现方案**：
```python
def replace_text_in_paragraph(paragraph, old_text, new_text):
    """处理跨 Run 的文本替换"""
    # 方案1: 简单替换（仅当占位符在单个 Run 中）
    for run in paragraph.runs:
        if old_text in run.text:
            run.text = run.text.replace(old_text, new_text)
            return True
    
    # 方案2: 跨 Run 替换（需要合并后替换，可能丢失部分格式）
    full_text = paragraph.text
    if old_text in full_text:
        # 清除所有 runs 并重建
        # 注意：这会丢失原有格式！
        paragraph.clear()
        paragraph.add_run(full_text.replace(old_text, new_text))
        return True
    
    return False
```

**建议**：
1. 在需求文档中明确说明模板制作规范（占位符需为连续文本）
2. 提供两种替换模式：`strict`（保留格式，仅处理单 Run）和 `lenient`（跨 Run，可能丢失格式）
3. 在任务 T-007 中添加详细的实现方案和测试用例

#### [问题 I-3] 自动保存的性能影响未评估 - 低风险

**问题描述**：`auto_save` 功能会在每次修改后触发文件写入，可能影响性能。

**建议方案**：
1. 采用防抖（debounce）机制，延迟 N 毫秒后保存
2. 或采用脏标记机制，仅在确实有修改时保存
3. 在文档中说明性能影响

---

## 4. 模板填充场景覆盖评审

### 4.1 场景需求回顾

用户强调的 "模板填充" 场景核心需求：
1. 打开现有 .docx 模板
2. 定位特定位置（表格、占位符）
3. 填充数据
4. 保存结果

### 4.2 覆盖情况分析

| 需求点 | 是否覆盖 | 相关工具/需求 |
|--------|----------|---------------|
| 打开现有文件 | 是 | `docx_create(file_path)` |
| 按索引定位表格 | 是 | R-006: `docx_get_table(index)` |
| 按内容查找表格 | 是 | R-006: `docx_find_table(text)` |
| 全局文本替换 | 是 | R-007: `docx_replace_text` |
| 复制表格结构 | 是 | R-008: `docx_copy_table` |
| **定位特定行/列** | **部分** | 需要增强 |
| **批量填充表格数据** | **否** | 需要新增 |
| **条件性内容保留/删除** | **否** | 需要新增 |

### 4.3 遗漏场景与建议

#### [遗漏 S-1] 表格行级操作不完整 - 中等风险

**场景描述**：用户需要在模板表格的特定行后插入新行并填充数据。

**当前支持**：R-005 提到 `docx_add_table_row/col`，但未详细设计。

**建议补充**：
- `docx_insert_row(session_id, table_id, after_row_index)` - 在指定行后插入
- `docx_delete_row(session_id, table_id, row_index)` - 删除指定行
- `docx_get_row_cells(session_id, table_id, row_index)` - 获取一行的所有单元格 ID

#### [遗漏 S-2] 批量表格数据填充 - 高风险

**场景描述**：用户经常需要将多行数据一次性填入表格，而非逐个单元格操作。

**当前问题**：填充一个 5x5 表格需要调用 25 次 `docx_add_paragraph_to_cell`，效率极低。

**建议新增工具**：
```python
@mcp.tool()
def docx_fill_table(
    session_id: str,
    table_id: str,
    data: list,  # [[row1_col1, row1_col2], [row2_col1, row2_col2], ...]
    start_row: int = 0,
    start_col: int = 0
) -> str:
    """
    Batch fill table cells with data.
    
    Args:
        session_id: The active session ID.
        table_id: The ID of the table.
        data: 2D list of values to fill. Each inner list is a row.
        start_row: Starting row index (0-based).
        start_col: Starting column index (0-based).
    
    Returns:
        str: Success message with number of cells filled.
    """
```

#### [遗漏 S-3] 段落/表格删除功能 - 中等风险

**场景描述**：模板中可能有条件性内容（如 "如果没有附件，删除此段落"）。

**当前状态**：设计中未提及删除操作。

**建议新增工具**：
- `docx_delete_paragraph(session_id, paragraph_id)`
- `docx_delete_table(session_id, table_id)`

#### [遗漏 S-4] 表格样式查询 - 低风险

**场景描述**：用户可能需要获取表格的当前样式以便复制时保持一致。

**建议新增工具**：
- `docx_get_properties(session_id, element_id)` - 读取元素的当前属性

---

## 5. 风险矩阵

| 风险 | 可能性 | 影响程度 | 缓解措施 |
|------|--------|----------|----------|
| 表格深拷贝失败 | 中 | 高 | 提前进行技术验证，准备备选方案 |
| 文本替换丢失格式 | 高 | 中 | 明确文档约束，提供多种替换模式 |
| 复杂 JSON 导致 LLM 错误 | 中 | 中 | 保留简化工具，提供详细 Schema |
| 自动保存性能问题 | 低 | 低 | 采用防抖机制 |
| 上下文歧义导致误操作 | 中 | 中 | 增加 `get_context` 工具，完善文档 |

---

## 6. 实施建议

### P0 - 必须解决（阻塞实施）

1. **完善表格深拷贝方案** (I-1)
   - 在 T-006 开始前，先创建 POC 验证技术可行性
   - 准备基于 XML 操作的实现方案

2. **设计文本替换的 Run 分割处理策略** (I-2)
   - 明确模板制作规范
   - 实现并测试跨 Run 替换逻辑

3. **新增批量表格填充工具** (S-2)
   - 这是模板填充场景的核心需求

### P1 - 重要（强烈建议）

4. **完善 JSON Schema 定义** (M-1)
   - 为 `docx_set_properties` 提供详细的输入校验
   - 对无效属性返回友好错误消息

5. **增加删除操作支持** (S-3)
   - `docx_delete_paragraph`
   - `docx_delete_table`

6. **补充上下文查询工具** (A-1)
   - `docx_get_context(session_id)`

### P2 - 建议（可延后）

7. **完善属性映射表** (A-3)
8. **增加表格行级操作** (S-1)
9. **增加属性读取工具** (S-4)

---

## 7. 附录：技术参考

### 7.1 python-docx 表格复制参考

- [Stack Overflow: Copy table in python-docx](https://stackoverflow.com)
- [Medium: Working with python-docx](https://medium.com)

### 7.2 MCP 协议最佳实践

- [MCP Official Documentation](https://modelcontextprotocol.io)
- [MCP Tool Design Best Practices](https://modelcontextprotocol.info)

### 7.3 文本替换参考

- [python-docx-template library](https://github.com)
- [Stack Overflow: Replace text preserve formatting](https://stackoverflow.com)

---

**评审结论**：设计方案整体方向正确，但需要在实施前解决上述 P0 级问题。建议将 T-006（表格高级操作）和 T-007（文本替换）的技术方案细化后再开始编码。

**下一步行动**：
1. 针对 P0 问题更新设计文档
2. 创建表格深拷贝和文本替换的技术 POC
3. 更新 tasks.md，补充遗漏的任务项

