---
feature: element-id-enhancement
version: 1
created_at: 2026-01-23
status: draft
---

# 技术设计文档: Element ID Enhancement

> **功能标识**: element-id-enhancement
> **复杂度**: complex
> **设计版本**: v1
> **设计日期**: 2026-01-23

## 1. 架构设计

### 1.1 系统架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Tools Layer                          │
├─────────────────────────────────────────────────────────────┤
│  docx_extract_template_structure()                          │
│  docx_get_structure_summary()                               │
│  docx_read_content()                                        │
│  docx_get_table_structure()                                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                  Core Parser Layer                          │
├─────────────────────────────────────────────────────────────┤
│  TemplateParser.extract_heading_structure()                 │
│  TemplateParser.extract_paragraph_structure()               │
│  TemplateParser.extract_table_structure()                   │
│  TableStructureAnalyzer.detect_irregular_structure()        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                  Session Layer                              │
├─────────────────────────────────────────────────────────────┤
│  Session.register_object()                                  │
│  Session._get_element_id(auto_register=True)               │
│  Session.object_registry                                    │
│  Session._element_id_cache                                  │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 核心设计原则

1. **自动注册优先**: 所有返回 element_id 的地方必须自动注册元素到 session
2. **向后兼容**: 只添加新字段，不删除或重命名现有字段
3. **统一命名**: 所有 ID 字段统一命名为 `element_id`（段落、表格）或 `cell_id`（单元格）
4. **性能优化**: 利用 `_element_id_cache` 避免重复注册
5. **最小侵入**: 尽量在现有代码基础上扩展，避免大规模重构

### 1.3 ID 前缀规范

| 元素类型 | ID 前缀 | 示例 | 说明 |
|---------|---------|------|------|
| Paragraph | `para_` | `para_a1b2c3d4` | 包括普通段落和标题 |
| Table | `table_` | `table_e5f6g7h8` | 表格对象 |
| Cell | `cell_` | `cell_i9j0k1l2` | 表格单元格 |
| Run | `run_` | `run_m3n4o5p6` | 文本块（本次不涉及）|

## 2. 组件设计

### 2.1 TemplateParser 增强

#### 2.1.1 修改方法签名

**现有方法**：
```python
def extract_heading_structure(self, paragraph: Paragraph) -> Dict[str, Any]:
def extract_paragraph_structure(self, paragraph: Paragraph) -> Dict[str, Any]:
def extract_table_structure(self, table: Table) -> Dict[str, Any]:
```

**新增参数**：
```python
def extract_heading_structure(
    self,
    paragraph: Paragraph,
    session: Optional[Session] = None
) -> Dict[str, Any]:

def extract_paragraph_structure(
    self,
    paragraph: Paragraph,
    session: Optional[Session] = None
) -> Dict[str, Any]:

def extract_table_structure(
    self,
    table: Table,
    session: Optional[Session] = None
) -> Dict[str, Any]:
```

**设计说明**：
- `session` 参数为可选，保持向后兼容
- 当 `session` 为 `None` 时，不添加 `element_id` 字段（兼容旧代码）
- 当 `session` 不为 `None` 时，自动注册元素并添加 `element_id` 字段

#### 2.1.2 返回值增强

**extract_heading_structure() 返回值**：
```python
{
    "type": "heading",
    "level": 1,
    "text": "Chapter 1",
    "style": {...},
    "element_id": "para_a1b2c3d4"  # 新增字段
}
```

**extract_paragraph_structure() 返回值**：
```python
{
    "type": "paragraph",
    "text": "This is a paragraph.",
    "style": {...},
    "element_id": "para_e5f6g7h8"  # 新增字段
}
```

**extract_table_structure() 返回值**：
```python
{
    "type": "table",
    "rows": 5,
    "cols": 3,
    "header_row": 0,
    "headers": ["Name", "Age", "City"],
    "style": {...},
    "element_id": "table_i9j0k1l2"  # 新增字段
}
```

### 2.2 TableStructureAnalyzer 增强

#### 2.2.1 修改方法签名

**现有方法**：
```python
@staticmethod
def detect_irregular_structure(table: Table) -> Dict[str, Any]:
```

**新增参数**：
```python
@staticmethod
def detect_irregular_structure(
    table: Table,
    session: Optional[Session] = None
) -> Dict[str, Any]:
```

#### 2.2.2 返回值增强

**现有返回值**：
```python
{
    "is_irregular": False,
    "merged_cells": [],
    "grid_structure": [[...]]
}
```

**增强后返回值**：
```python
{
    "is_irregular": False,
    "merged_cells": [],
    "grid_structure": [
        [
            {
                "row": 0,
                "col": 0,
                "text": "Name",
                "cell_id": "cell_a1b2c3d4"  # 新增字段
            },
            ...
        ],
        ...
    ]
}
```

### 2.3 工具层修改

#### 2.3.1 docx_extract_template_structure()

**修改点**：
1. 在调用 `TemplateParser` 时传入 `session` 对象
2. 确保所有元素自动注册

**实现伪代码**：
```python
def docx_extract_template_structure(session_id: str, ...) -> str:
    session = session_manager.get_session(session_id)
    parser = TemplateParser()

    # 传入 session 以启用自动注册
    structure = parser.extract_structure(session.document, session=session)

    return json.dumps(structure, indent=2, ensure_ascii=False)
```

#### 2.3.2 docx_get_structure_summary()

**修改点**：
1. 在遍历元素时调用 `session._get_element_id(auto_register=True)`
2. 为每个 heading、table、paragraph 添加 `element_id` 字段

**实现伪代码**：
```python
def docx_get_structure_summary(session_id: str, ...) -> str:
    session = session_manager.get_session(session_id)

    for element in doc.element.body:
        if element.tag.endswith('p'):
            para = ...
            if para.style.name.startswith('Heading'):
                heading_info = {
                    "level": ...,
                    "style": ...,
                    "element_id": session._get_element_id(para, auto_register=True)  # 新增
                }
                structure["headings"].append(heading_info)

    return json.dumps(structure, ensure_ascii=False, indent=2)
```

#### 2.3.3 docx_read_content()

**修改点**：
1. 将 `include_ids` 参数默认值从 `False` 改为 `True`
2. 保持现有逻辑不变（已经支持 `include_ids`）

**修改前**：
```python
def docx_read_content(
    session_id: str,
    ...,
    include_ids: bool = False,  # 默认 False
    ...
) -> str:
```

**修改后**：
```python
def docx_read_content(
    session_id: str,
    ...,
    include_ids: bool = True,  # 默认 True
    ...
) -> str:
```

#### 2.3.4 docx_get_table_structure()

**修改点**：
1. 在调用 `TableStructureAnalyzer.detect_irregular_structure()` 时传入 `session`
2. 确保返回的 `structure_info` 包含 `cell_id`

**实现伪代码**：
```python
def docx_get_table_structure(session_id: str, table_id: str) -> str:
    session = session_manager.get_session(session_id)
    table = session.get_object(table_id)

    # 传入 session 以启用 cell_id 生成
    structure_info = TableStructureAnalyzer.detect_irregular_structure(
        table,
        session=session
    )

    return create_success_response(
        message="Table structure retrieved successfully",
        element_id=table_id,
        structure_info=structure_info,
        ...
    )
```

## 3. 数据流设计

### 3.1 docx_extract_template_structure 数据流

```
User Call
    ↓
docx_extract_template_structure(session_id)
    ↓
session = session_manager.get_session(session_id)
    ↓
parser = TemplateParser()
    ↓
parser.extract_structure(document, session=session)
    ↓
for element in document.element.body:
    ├─ if heading:
    │   ├─ para = Paragraph(element, document)
    │   ├─ element_id = session._get_element_id(para, auto_register=True)
    │   └─ return {"type": "heading", ..., "element_id": element_id}
    │
    ├─ if paragraph:
    │   ├─ para = Paragraph(element, document)
    │   ├─ element_id = session._get_element_id(para, auto_register=True)
    │   └─ return {"type": "paragraph", ..., "element_id": element_id}
    │
    └─ if table:
        ├─ table = Table(element, document)
        ├─ element_id = session._get_element_id(table, auto_register=True)
        └─ return {"type": "table", ..., "element_id": element_id}
    ↓
return JSON with element_ids
```

### 3.2 自动注册机制

```
session._get_element_id(element, auto_register=True)
    ↓
element_key = id(element._element)
    ↓
if element_key in _element_id_cache:
    return _element_id_cache[element_key]  # 缓存命中，直接返回
    ↓
if auto_register:
    ├─ prefix = determine_prefix(element)  # "para", "table", "cell"
    ├─ element_id = register_object(element, prefix)
    ├─ _element_id_cache[element_key] = element_id
    └─ return element_id
```

## 4. 接口设计

### 4.1 TemplateParser 接口变更

#### extract_structure()

**新增参数**：
```python
def extract_structure(
    self,
    document: DocumentType,
    session: Optional[Session] = None  # 新增
) -> Dict[str, Any]:
```

**行为变更**：
- 当 `session` 不为 `None` 时，调用子方法时传入 `session`
- 子方法自动注册元素并添加 `element_id` 字段

#### extract_heading_structure()

**新增参数**：
```python
def extract_heading_structure(
    self,
    paragraph: Paragraph,
    session: Optional[Session] = None  # 新增
) -> Dict[str, Any]:
```

**返回值变更**：
```python
# 当 session 不为 None 时
{
    "type": "heading",
    "level": 1,
    "text": "...",
    "style": {...},
    "element_id": "para_xxx"  # 新增
}
```

#### extract_paragraph_structure()

**新增参数**：
```python
def extract_paragraph_structure(
    self,
    paragraph: Paragraph,
    session: Optional[Session] = None  # 新增
) -> Dict[str, Any]:
```

**返回值变更**：
```python
# 当 session 不为 None 时
{
    "type": "paragraph",
    "text": "...",
    "style": {...},
    "element_id": "para_xxx"  # 新增
}
```

#### extract_table_structure()

**新增参数**：
```python
def extract_table_structure(
    self,
    table: Table,
    session: Optional[Session] = None  # 新增
) -> Dict[str, Any]:
```

**返回值变更**：
```python
# 当 session 不为 None 时
{
    "type": "table",
    "rows": 5,
    "cols": 3,
    "headers": [...],
    "style": {...},
    "element_id": "table_xxx"  # 新增
}
```

### 4.2 TableStructureAnalyzer 接口变更

#### detect_irregular_structure()

**新增参数**：
```python
@staticmethod
def detect_irregular_structure(
    table: Table,
    session: Optional[Session] = None  # 新增
) -> Dict[str, Any]:
```

**返回值变更**：
```python
# 当 session 不为 None 时
{
    "is_irregular": False,
    "merged_cells": [...],
    "grid_structure": [
        [
            {
                "row": 0,
                "col": 0,
                "text": "...",
                "cell_id": "cell_xxx"  # 新增
            },
            ...
        ],
        ...
    ]
}
```

### 4.3 MCP 工具接口变更

#### docx_read_content()

**参数变更**：
```python
def docx_read_content(
    session_id: str,
    max_paragraphs: Optional[int] = None,
    start_from: int = 0,
    include_tables: bool = False,
    return_json: bool = False,
    include_ids: bool = True,  # 默认值从 False 改为 True
    ...
) -> str:
```

**行为变更**：
- 默认返回 `element_id`
- 用户可以通过 `include_ids=False` 禁用（向后兼容）

#### 其他工具

**docx_extract_template_structure()**, **docx_get_structure_summary()**, **docx_get_table_structure()** 的参数签名保持不变，只修改内部实现。

## 5. 性能优化设计

### 5.1 缓存机制

**问题**：重复调用 `register_object()` 会导致同一元素生成多个 ID。

**解决方案**：利用 `Session._element_id_cache` 缓存。

```python
# Session._get_element_id() 实现
def _get_element_id(self, element: Any, auto_register: bool = True) -> Optional[str]:
    if not hasattr(element, '_element'):
        return None

    element_key = id(element._element)

    # 缓存命中，直接返回
    if element_key in self._element_id_cache:
        return self._element_id_cache[element_key]

    # 缓存未命中，自动注册
    if auto_register:
        prefix = determine_prefix(element)
        element_id = self.register_object(element, prefix)
        return element_id  # register_object 已更新缓存

    return None
```

### 5.2 性能指标

| 指标 | 目标 | 测量方法 |
|------|------|----------|
| 内存增长 | < 10% | 对比修改前后的 `object_registry` 大小 |
| 调用延迟 | < 5% | 对比修改前后的工具调用时间 |
| 大文档处理 | < 10% | 测试 1000+ 段落文档的处理时间 |

### 5.3 性能测试场景

1. **小文档**（10 段落，2 表格）：验证基本功能
2. **中文档**（100 段落，10 表格）：验证性能影响
3. **大文档**（1000+ 段落，50+ 表格）：验证内存和性能
4. **重复调用**：验证缓存机制有效性

## 6. 错误处理设计

### 6.1 错误场景

| 场景 | 错误类型 | 处理方式 |
|------|----------|----------|
| Session 不存在 | `SessionNotFound` | 返回标准错误响应 |
| 元素注册失败 | `RegistrationError` | 记录日志，返回不含 `element_id` 的结果 |
| 缓存不一致 | `CacheInconsistency` | 清除缓存，重新注册 |

### 6.2 降级策略

**原则**：即使 `element_id` 生成失败，也不应阻塞主流程。

**实现**：
```python
try:
    element_id = session._get_element_id(element, auto_register=True)
    result["element_id"] = element_id
except Exception as e:
    logger.warning(f"Failed to generate element_id: {e}")
    # 不添加 element_id 字段，继续返回其他信息
```

## 7. 测试策略

### 7.1 单元测试

**测试文件**：`tests/unit/test_element_id_enhancement.py`

**测试用例**：
1. `test_extract_template_structure_with_element_ids()`: 验证返回包含 `element_id`
2. `test_get_structure_summary_with_element_ids()`: 验证返回包含 `element_id`
3. `test_read_content_default_include_ids()`: 验证默认返回 `element_id`
4. `test_read_content_explicit_exclude_ids()`: 验证 `include_ids=False` 生效
5. `test_get_table_structure_with_cell_ids()`: 验证返回包含 `cell_id`
6. `test_element_id_reusability()`: 验证返回的 ID 可用于其他工具
7. `test_element_id_cache()`: 验证缓存机制
8. `test_backward_compatibility()`: 验证现有测试通过

### 7.2 E2E 测试

**测试文件**：`tests/e2e/test_element_id_workflow.py`

**测试场景**：
1. 提取结构 → 获取 ID → 修改元素
2. 读取内容 → 获取 ID → 更新段落
3. 获取表格结构 → 获取 cell_id → 修改单元格

### 7.3 性能测试

**测试文件**：`tests/performance/test_element_id_performance.py`

**测试场景**：
1. 小文档性能测试
2. 大文档性能测试
3. 内存占用测试
4. 缓存命中率测试

## 8. 部署计划

### 8.1 部署步骤

1. **阶段 1**：修改 `TemplateParser` 和 `TableStructureAnalyzer`
2. **阶段 2**：修改工具层（`content_tools.py`, `composite_tools.py`, `table_tools.py`）
3. **阶段 3**：更新单元测试
4. **阶段 4**：运行 E2E 测试
5. **阶段 5**：性能测试
6. **阶段 6**：更新文档（README.md, CLAUDE.md）

### 8.2 回滚计划

**触发条件**：
- 现有测试失败 > 5%
- 性能下降 > 10%
- 内存增长 > 15%

**回滚步骤**：
1. 恢复修改前的代码
2. 重新运行测试验证
3. 分析失败原因
4. 修复后重新部署

## 9. 风险评估

### 9.1 技术风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 缓存不一致 | 中 | 高 | 添加缓存验证逻辑 |
| 性能下降 | 低 | 中 | 性能测试 + 优化 |
| 内存泄漏 | 低 | 高 | 内存监控 + 清理机制 |
| 向后兼容性破坏 | 低 | 高 | 完整的回归测试 |

### 9.2 业务风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 用户代码破坏 | 低 | 高 | 保持参数签名不变 |
| 文档不同步 | 中 | 中 | 同步更新文档 |

## 10. 后续优化

### 10.1 短期优化（v1.1）

- 添加 `element_id` 批量查询接口
- 优化缓存清理策略

### 10.2 长期优化（v2.0）

- 支持 Run 级别的 `element_id`
- 支持跨 session 的 `element_id` 引用

---

**设计者**: AI Team
**审核者**: 待定
**批准者**: 待定
**版本历史**:
- v1 (2026-01-23): 初始设计
