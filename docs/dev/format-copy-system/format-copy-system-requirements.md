---
feature: format-copy-system
complexity: complex
generated_by: clarify
generated_at: 2026-01-21T10:30:00Z
version: 1
---

# 需求文档: Word 文档格式复制与模板系统

> **功能标识**: format-copy-system
> **复杂度**: complex
> **生成方式**: clarify
> **生成时间**: 2026-01-21

## 1. 概述

### 1.1 一句话描述

建立统一的格式复制和模板系统,支持从示例章节提取格式并应用到新章节,包含原子化工具、批量操作引擎和格式模板管理器。

### 1.2 核心价值

**解决的问题**:
- **格式不一致**: 手动创建多个相似章节时,格式难以保持一致
- **效率低下**: 逐个设置段落、标题、表格的格式费时费力
- **工具不全**: 现有 MCP 工具仅支持表格复制,缺少段落、标题等元素的复制能力

**带来的价值**:
- **一键模板复制**: 从示例章节一键生成格式一致的新章节
- **格式可复用**: 提取格式为模板,跨文档、跨会话复用
- **批量操作**: 支持选定区间批量复制多个元素

### 1.3 目标用户

- **主要用户**: Claude AI (通过 MCP 工具调用)
- **次要用户**: 使用 docx-mcp-server 的开发者和最终用户

---

## 2. 需求与用户故事

### 2.1 需求清单

| ID | 需求点 | 优先级 | 用户故事 |
|----|--------|--------|----------|
| R-001 | 原子化复制工具 | P0 | As a user, I want to copy individual elements (paragraph, heading), so that I can reuse them with full formatting |
| R-002 | 批量区间复制 | P0 | As a user, I want to copy a range of elements (from start to end), so that I can duplicate entire sections efficiently |
| R-003 | 格式模板系统 | P1 | As a user, I want to extract format as a template and apply it to other elements, so that I can share formatting across documents |
| R-004 | 递归子元素复制 | P0 | As a system, I SHALL copy all child elements (e.g., runs in paragraph) when copying parent elements |
| R-005 | 批量文本替换 | P1 | As a user, I want to replace multiple keywords in one call, so that I can efficiently update content after copying |
| R-006 | 仅格式模式 | P2 | As a user, I want to copy only formatting without content, so that I can create empty templates |
| R-007 | 元素来源追踪 | P2 | As a developer, I want to track the source element ID after copying, so that I can maintain relationships |

### 2.2 验收标准

#### R-001: 原子化复制工具

- **WHEN** 调用 `docx_copy_paragraph(session_id, paragraph_id)`, **THEN** 系统 **SHALL** 返回新段落 ID,新段落保留所有格式(字体、对齐、缩进、行距)和内容(包含所有 runs)
- **WHEN** 调用 `docx_copy_heading(session_id, heading_id)`, **THEN** 系统 **SHALL** 返回新标题 ID,标题级别和样式完全一致

#### R-002: 批量区间复制

- **WHEN** 调用 `docx_copy_elements_range(session_id, start_element_id, end_element_id)`, **THEN** 系统 **SHALL**:
  1. 自动检测区间内所有元素类型(段落、表格、标题)
  2. 按文档顺序逐个复制
  3. 返回 JSON 列表 `[{"original_id": "para_1", "new_id": "para_123"}, ...]`

#### R-003: 格式模板系统

- **WHEN** 调用 `docx_extract_format_template(session_id, element_id)`, **THEN** 系统 **SHALL** 返回 JSON 格式模板,包含:
  - 元素类型 (paragraph/heading/table)
  - 字体属性 (font family, size, bold, italic, color)
  - 段落格式 (alignment, indentation, spacing)
  - 表格样式 (borders, shading) (如适用)

- **WHEN** 调用 `docx_apply_format_template(session_id, element_id, template_json)`, **THEN** 系统 **SHALL** 将模板格式应用到目标元素,保留原有内容

#### R-004: 递归子元素复制

- **WHEN** 复制段落时, **THEN** 系统 **SHALL** 递归复制所有 runs 及其格式
- **WHEN** 复制表格时, **THEN** 系统 **SHALL** 递归复制所有单元格、段落和 runs

#### R-005: 批量文本替换

- **WHEN** 调用 `docx_batch_replace_text(session_id, replacements_json, scope_id=None)`, **THEN** 系统 **SHALL**:
  - 支持 JSON 格式: `{"old1": "new1", "old2": "new2"}`
  - 在指定范围内(或全文档)批量替换
  - 返回替换统计: `{"old1": 3, "old2": 5}` (替换次数)

#### R-006: 仅格式模式

- **WHEN** 调用 `docx_copy_paragraph(session_id, paragraph_id, format_only=True)`, **THEN** 系统 **SHALL** 创建空段落仅保留格式,不复制文本内容

#### R-007: 元素来源追踪

- **WHEN** 调用复制工具时传入 `track_source=True`, **THEN** 系统 **SHALL**:
  - 在新元素的元数据中记录 `source_element_id`
  - 提供 `docx_get_element_source(session_id, element_id)` 查询来源

---

## 3. 功能验收清单

| ID | 功能点 | 验收步骤 | 优先级 | 关联需求 | 通过 |
|----|--------|----------|--------|----------|------|
| F-001 | docx_copy_paragraph | 1. 调用工具复制段落 2. 验证新段落格式一致 3. 验证所有 runs 被复制 | P0 | R-001, R-004 | ☐ |
| F-002 | docx_copy_heading | 1. 复制各级标题 (Heading 1-9) 2. 验证标题级别和样式 | P0 | R-001 | ☐ |
| F-003 | docx_copy_elements_range | 1. 指定起止元素 2. 验证自动检测类型 3. 验证按序复制 4. 验证返回映射列表 | P0 | R-002 | ☐ |
| F-004 | docx_extract_format_template | 1. 提取段落模板 2. 提取标题模板 3. 提取表格模板 4. 验证 JSON 结构 | P1 | R-003 | ☐ |
| F-005 | docx_apply_format_template | 1. 应用段落模板 2. 验证格式正确,内容保留 3. 跨元素类型应用(可能失败) | P1 | R-003 | ☐ |
| F-006 | docx_batch_replace_text | 1. 批量替换多个关键词 2. 验证替换次数统计 3. 限定范围替换 | P1 | R-005 | ☐ |
| F-007 | format_only 模式 | 1. 使用 format_only=True 复制 2. 验证段落为空 3. 验证格式保留 | P2 | R-006 | ☐ |
| F-008 | 元素来源追踪 | 1. 复制时启用 track_source 2. 查询新元素来源 3. 验证元数据正确 | P2 | R-007 | ☐ |

---

## 4. 技术约束

### 4.1 技术栈

- **核心框架**: python-docx (现有依赖)
- **MCP 框架**: FastMCP (现有依赖)
- **ID 映射**: Session.object_registry (现有机制)

### 4.2 架构设计要点

#### 4.2.1 格式模板管理器 (TemplateManager)

**位置**: `src/docx_mcp_server/utils/format_template.py`

**核心类**:
```python
class FormatTemplate:
    """格式模板数据类"""
    element_type: str  # "paragraph" | "heading" | "table" | "run"
    font: dict         # {"name": "Arial", "size": 12, "bold": True, ...}
    paragraph_format: dict  # {"alignment": "left", "left_indent": 0, ...}
    table_format: dict | None  # 仅表格有此字段

class TemplateManager:
    @staticmethod
    def extract_template(element) -> FormatTemplate:
        """从 python-docx 元素提取格式"""
        pass

    @staticmethod
    def apply_template(element, template: FormatTemplate):
        """将模板应用到元素"""
        pass

    @staticmethod
    def to_json(template: FormatTemplate) -> str:
        """序列化为 JSON"""
        pass

    @staticmethod
    def from_json(json_str: str) -> FormatTemplate:
        """从 JSON 反序列化"""
        pass
```

#### 4.2.2 批量复制引擎 (CopyEngine)

**位置**: `src/docx_mcp_server/utils/copy_engine.py`

**核心类**:
```python
class CopyEngine:
    @staticmethod
    def copy_element(session, element_id, format_only=False, track_source=False):
        """复制单个元素(通用入口,自动检测类型)"""
        pass

    @staticmethod
    def copy_range(session, start_id, end_id) -> list[dict]:
        """批量复制区间,返回 [{"original_id": ..., "new_id": ...}]"""
        pass

    @staticmethod
    def _copy_paragraph_recursive(paragraph) -> Paragraph:
        """递归复制段落及其所有 runs"""
        pass

    @staticmethod
    def _copy_table_recursive(table) -> Table:
        """递归复制表格及其所有单元格"""
        pass
```

#### 4.2.3 扩展 Session 类

**修改**: `src/docx_mcp_server/core/session.py`

```python
class Session:
    # 新增字段
    element_metadata: dict[str, dict]  # 存储元素元数据(如 source_element_id)

    def register_object(self, obj, prefix: str, metadata: dict = None) -> str:
        """扩展注册方法,支持元数据"""
        element_id = f"{prefix}_{uuid.uuid4().hex[:8]}"
        self.object_registry[element_id] = obj
        if metadata:
            self.element_metadata[element_id] = metadata
        return element_id

    def get_metadata(self, element_id: str) -> dict:
        """获取元素元数据"""
        return self.element_metadata.get(element_id, {})
```

### 4.3 集成点

- **现有工具扩展**:
  - `docx_copy_table()` 已存在,需保持接口一致性
  - 新增 `docx_copy_paragraph()`, `docx_copy_heading()`

- **格式工具增强**:
  - `docx_format_copy()` 已存在,可基于 TemplateManager 重构

### 4.4 性能要求

- 批量复制 100 个段落耗时 < 5 秒
- 格式模板提取/应用耗时 < 100ms

---

## 5. 排除项

- ❌ **图片复制**: 本次不支持复制图片及其格式,仅支持文本和表格
- ❌ **跨会话模板共享**: 模板仅在当前会话有效,不持久化到文件
- ❌ **自动章节识别**: 不自动识别"章节"概念,用户需明确指定起止元素
- ❌ **格式冲突解决**: 应用模板时如果格式冲突,直接覆盖,不提供冲突解决策略

---

## 6. 实施计划

### 6.1 架构设计阶段

- [ ] 设计 TemplateManager 类和 JSON schema
- [ ] 设计 CopyEngine 递归复制算法
- [ ] 扩展 Session 类支持元数据存储
- [ ] 定义 MCP 工具接口和参数

### 6.2 开发阶段(并行)

**Track 1: 格式模板系统**
- [ ] 实现 FormatTemplate 数据类
- [ ] 实现 TemplateManager.extract_template()
- [ ] 实现 TemplateManager.apply_template()
- [ ] 实现 JSON 序列化/反序列化

**Track 2: 批量复制引擎**
- [ ] 实现 CopyEngine.copy_element()
- [ ] 实现递归复制算法(_copy_paragraph_recursive, _copy_table_recursive)
- [ ] 实现 CopyEngine.copy_range()

**Track 3: MCP 工具集**
- [ ] 实现 docx_copy_paragraph()
- [ ] 实现 docx_copy_heading()
- [ ] 实现 docx_copy_elements_range()
- [ ] 实现 docx_extract_format_template()
- [ ] 实现 docx_apply_format_template()
- [ ] 实现 docx_batch_replace_text()
- [ ] 实现 docx_get_element_source()

### 6.3 测试阶段

- [ ] 单元测试: TemplateManager 各方法
- [ ] 单元测试: CopyEngine 递归复制
- [ ] 单元测试: 各 MCP 工具
- [ ] 格式保真度测试: 复制前后格式一致性
- [ ] E2E 测试: 完整工作流(复制章节 → 替换文本 → 保存文档)

---

## 7. 下一步

✅ 需求已澄清,在新会话中执行:

```bash
/clouditera:dev:spec-dev format-copy-system --skip-requirements
```

这将进入技术设计阶段(生成 design.md 和 tasks.md)。

---

## 附录: MCP 工具接口设计(草案)

### 原子化复制工具

```python
@mcp.tool()
def docx_copy_paragraph(
    session_id: str,
    paragraph_id: str,
    format_only: bool = False,
    track_source: bool = False
) -> str:
    """
    复制段落及其所有 runs,保留完整格式

    Returns:
        新段落的 element_id
    """
    pass

@mcp.tool()
def docx_copy_heading(
    session_id: str,
    heading_id: str,
    format_only: bool = False,
    track_source: bool = False
) -> str:
    """
    复制标题段落,保留标题级别和样式

    Returns:
        新标题的 element_id
    """
    pass
```

### 批量复制工具

```python
@mcp.tool()
def docx_copy_elements_range(
    session_id: str,
    start_element_id: str,
    end_element_id: str,
    format_only: bool = False
) -> str:
    """
    批量复制指定区间的所有元素

    Returns:
        JSON string: [{"original_id": "para_1", "new_id": "para_123"}, ...]
    """
    pass
```

### 格式模板工具

```python
@mcp.tool()
def docx_extract_format_template(
    session_id: str,
    element_id: str
) -> str:
    """
    提取元素格式为 JSON 模板

    Returns:
        JSON string: FormatTemplate
    """
    pass

@mcp.tool()
def docx_apply_format_template(
    session_id: str,
    element_id: str,
    template_json: str
) -> str:
    """
    将格式模板应用到目标元素

    Returns:
        Success message
    """
    pass
```

### 批量文本替换

```python
@mcp.tool()
def docx_batch_replace_text(
    session_id: str,
    replacements_json: str,  # {"old1": "new1", "old2": "new2"}
    scope_id: str | None = None  # 可选,限定替换范围
) -> str:
    """
    批量替换多个关键词

    Returns:
        JSON string: {"old1": 3, "old2": 5}  (替换次数统计)
    """
    pass
```

### 元素来源查询

```python
@mcp.tool()
def docx_get_element_source(
    session_id: str,
    element_id: str
) -> str:
    """
    查询元素的来源 element_id (如果有)

    Returns:
        source_element_id or "No source tracked"
    """
    pass
```
