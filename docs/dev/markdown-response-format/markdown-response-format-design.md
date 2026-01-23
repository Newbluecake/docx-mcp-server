# 技术设计文档: Markdown Response Format

> **功能标识**: markdown-response-format
> **复杂度**: complex
> **设计版本**: v1.0
> **设计时间**: 2026-01-23

---

## 1. 架构设计

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Tool Layer (51 tools)                 │
│  paragraph_tools.py, table_tools.py, run_tools.py, etc.    │
└────────────────────────┬────────────────────────────────────┘
                         │ calls
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              Response Formatting Layer (NEW)                 │
│                  response.py (refactored)                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ create_markdown_response()                           │  │
│  │  - Formats metadata (status, element_id, operation)  │  │
│  │  - Calls visualizer for context rendering           │  │
│  │  - Calls diff_renderer for change tracking          │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │ uses
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              Visualization Layer (NEW)                       │
│                  visualizer.py (new module)                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ DocumentVisualizer                                   │  │
│  │  - render_paragraph()    → ASCII box with content    │  │
│  │  - render_table()        → ASCII table grid          │  │
│  │  - render_context()      → One-page context view    │  │
│  │  - render_image()        → [IMG: filename.png]       │  │
│  │  - render_cursor()       → >>> [CURSOR] <<<          │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ DiffRenderer                                         │  │
│  │  - render_diff()         → Git-style diff output     │  │
│  │  - _compute_line_diff()  → Line-by-line comparison   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 核心组件

#### 1.2.1 Response Formatting Layer

**文件**: `src/docx_mcp_server/core/response.py`

**职责**:
- 提供统一的 Markdown 响应格式化接口
- 协调 visualizer 和 diff_renderer 的调用
- 管理响应的整体结构（metadata + context + changes）

**核心函数**:
```python
def create_markdown_response(
    session,
    message: str,
    element_id: Optional[str] = None,
    operation: Optional[str] = None,
    status: str = "success",
    show_context: bool = True,
    show_diff: bool = False,
    old_content: Optional[str] = None,
    new_content: Optional[str] = None,
    **extra_metadata
) -> str:
    """Create a Markdown-formatted response with ASCII visualization.

    Args:
        session: Session object
        message: Human-readable message
        element_id: Created/modified element ID
        operation: Operation name (e.g., "Insert Paragraph")
        status: "success" or "error"
        show_context: Whether to include document context visualization
        show_diff: Whether to show before/after diff
        old_content: Old content for diff (if show_diff=True)
        new_content: New content for diff (if show_diff=True)
        **extra_metadata: Additional metadata fields

    Returns:
        Markdown-formatted string
    """
```

**响应结构**:
```markdown
# 操作结果: {operation}

**Status**: ✅ Success / ❌ Error
**Element ID**: {element_id}
**Operation**: {operation}
{extra_metadata fields}

---

## 📄 Document Context

{ASCII visualization of document context}

---

## 🔄 Changes (if show_diff=True)

{Git-style diff}
```

#### 1.2.2 Visualization Layer

**文件**: `src/docx_mcp_server/core/visualizer.py` (新建)

**职责**:
- 渲染文档元素为 ASCII 可视化
- 提供上下文范围控制（一页内容）
- 处理内容截断和省略标记

**核心类**:

```python
class DocumentVisualizer:
    """ASCII visualization renderer for document elements."""

    def __init__(self, session):
        self.session = session
        self.max_width = 80  # Maximum line width
        self.context_range = 7  # Elements before/after current

    def render_paragraph(self, paragraph, element_id: str,
                        highlight: bool = False) -> str:
        """Render a paragraph as ASCII box.

        Args:
            paragraph: Paragraph object
            element_id: Element ID
            highlight: Whether to mark as current/new

        Returns:
            ASCII box representation
        """

    def render_table(self, table, element_id: str,
                    highlight: bool = False) -> str:
        """Render a table as ASCII grid.

        Args:
            table: Table object
            element_id: Element ID
            highlight: Whether to mark as current/new

        Returns:
            ASCII table representation
        """

    def render_context(self, element_id: str,
                      context_range: Optional[int] = None) -> str:
        """Render document context around an element.

        Args:
            element_id: Current element ID
            context_range: Number of elements before/after (default: 7)

        Returns:
            ASCII visualization of context
        """

    def render_image(self, image_path: str, element_id: str) -> str:
        """Render image placeholder.

        Returns:
            [IMG: filename.png]
        """

    def render_cursor(self) -> str:
        """Render cursor marker.

        Returns:
            >>> [CURSOR] <<<
        """
```

**辅助函数**:
```python
def _extract_text_with_format(paragraph) -> str:
    """Extract paragraph text with Markdown formatting.

    Converts:
    - Bold runs → **text**
    - Italic runs → *text*
    - Colors → [红色] prefix (optional)
    """

def _truncate_text(text: str, max_length: int = 80) -> str:
    """Truncate text and add ellipsis if needed."""

def _draw_box(content: str, title: str, highlight: bool = False) -> str:
    """Draw ASCII box around content.

    Example:
    ┌─────────────────────────────────────────┐
    │ Paragraph (para_123) ⭐ NEW             │
    ├─────────────────────────────────────────┤
    │ Content line 1                          │
    │ Content line 2                          │
    └─────────────────────────────────────────┘
    """
```

#### 1.2.3 Diff Rendering

**文件**: `src/docx_mcp_server/core/visualizer.py` (同一文件)

**核心类**:
```python
class DiffRenderer:
    """Git-style diff renderer for content changes."""

    def render_diff(self, old_content: str, new_content: str,
                   element_id: str, element_type: str = "Paragraph") -> str:
        """Render Git-style diff.

        Args:
            old_content: Original content
            new_content: Modified content
            element_id: Element ID
            element_type: Type of element (Paragraph, Table, etc.)

        Returns:
            Markdown-formatted diff
        """

    def _compute_line_diff(self, old_lines: List[str],
                          new_lines: List[str]) -> List[Tuple[str, str]]:
        """Compute line-by-line diff.

        Returns:
            List of (prefix, line) tuples where prefix is ' ', '-', or '+'
        """
```

### 1.3 数据流

#### 1.3.1 创建操作流程

```
Tool (e.g., docx_insert_paragraph)
    ↓
1. Create element (paragraph)
2. Register element → element_id
3. Update session context
    ↓
create_markdown_response(
    session=session,
    message="Paragraph created successfully",
    element_id=element_id,
    operation="Insert Paragraph",
    show_context=True,
    show_diff=False
)
    ↓
DocumentVisualizer.render_context(element_id)
    ↓
Return Markdown string
```

#### 1.3.2 更新操作流程

```
Tool (e.g., docx_update_paragraph_text)
    ↓
1. Get element by element_id
2. Capture old_content
3. Update element content
4. Capture new_content
    ↓
create_markdown_response(
    session=session,
    message="Paragraph updated successfully",
    element_id=element_id,
    operation="Update Paragraph Text",
    show_context=True,
    show_diff=True,
    old_content=old_content,
    new_content=new_content
)
    ↓
DiffRenderer.render_diff(old_content, new_content)
    ↓
DocumentVisualizer.render_context(element_id)
    ↓
Return Markdown string
```

---

## 2. 接口设计

### 2.1 Response API

#### 2.1.1 create_markdown_response

**签名**:
```python
def create_markdown_response(
    session,
    message: str,
    element_id: Optional[str] = None,
    operation: Optional[str] = None,
    status: str = "success",
    show_context: bool = True,
    show_diff: bool = False,
    old_content: Optional[str] = None,
    new_content: Optional[str] = None,
    **extra_metadata
) -> str
```

**参数说明**:
- `session`: Session 对象，用于访问文档和上下文
- `message`: 人类可读的消息（如 "Paragraph created successfully"）
- `element_id`: 创建或修改的元素 ID
- `operation`: 操作名称（如 "Insert Paragraph"）
- `status`: 状态，"success" 或 "error"
- `show_context`: 是否显示文档上下文（默认 True）
- `show_diff`: 是否显示变更对比（默认 False）
- `old_content`: 旧内容（仅当 show_diff=True 时需要）
- `new_content`: 新内容（仅当 show_diff=True 时需要）
- `**extra_metadata`: 额外的元数据字段（如 dimensions, position 等）

**返回值**:
Markdown 格式的字符串

**使用示例**:
```python
# 创建操作
return create_markdown_response(
    session=session,
    message="Paragraph created successfully",
    element_id=para_id,
    operation="Insert Paragraph",
    position="end:document_body"
)

# 更新操作
return create_markdown_response(
    session=session,
    message="Paragraph text updated",
    element_id=para_id,
    operation="Update Paragraph Text",
    show_diff=True,
    old_content=old_text,
    new_content=new_text
)

# 错误响应
return create_markdown_response(
    session=None,
    message=f"Session {session_id} not found",
    status="error",
    show_context=False,
    error_type="SessionNotFound"
)
```

#### 2.1.2 create_error_response (简化版)

**签名**:
```python
def create_error_response(message: str, error_type: Optional[str] = None) -> str
```

**说明**:
简化的错误响应，不需要 session 对象。

**返回格式**:
```markdown
# 操作结果: Error

**Status**: ❌ Error
**Error Type**: {error_type}
**Message**: {message}
```

### 2.2 Visualizer API

#### 2.2.1 DocumentVisualizer.render_context

**签名**:
```python
def render_context(self, element_id: str, context_range: Optional[int] = None) -> str
```

**算法**:
1. 获取文档的所有顶层元素（paragraphs + tables）
2. 找到 element_id 对应元素的索引位置
3. 计算上下文范围：[index - context_range, index + context_range]
4. 遍历范围内的元素，调用对应的 render 方法
5. 标记当前元素（⭐ CURRENT / ⭐ NEW / ⭐ UPDATED）
6. 在边界处添加省略标记（... (N more elements above/below) ...）
7. 标记光标位置（>>> [CURSOR] <<<）

**输出示例**:
```
📄 Document Context (showing 10 elements around para_123)

  ... (5 more elements above) ...

  ┌─────────────────────────────────────────┐
  │ Paragraph (para_120)                    │
  │ Previous paragraph content...           │
  └─────────────────────────────────────────┘

  ┌─────────────────────────────────────────┐
  │ Paragraph (para_121)                    │
  │ Another paragraph...                    │
  └─────────────────────────────────────────┘

>>> [CURSOR] <<<

  ┌─────────────────────────────────────────┐
  │ Paragraph (para_123) ⭐ NEW             │
  │ This is the newly inserted paragraph.   │
  └─────────────────────────────────────────┘

  ┌─────────────────────────────────────────┐
  │ Paragraph (para_124)                    │
  │ Next paragraph...                       │
  └─────────────────────────────────────────┘

  ... (5 more elements below) ...
```

#### 2.2.2 DiffRenderer.render_diff

**签名**:
```python
def render_diff(self, old_content: str, new_content: str,
               element_id: str, element_type: str = "Paragraph") -> str
```

**算法**:
1. 将 old_content 和 new_content 按行分割
2. 使用 difflib.SequenceMatcher 计算差异
3. 生成带前缀的行列表：
   - ` ` (空格): 不变的行
   - `-`: 删除的行
   - `+`: 新增的行
4. 包含前后各 2-3 行的上下文
5. 用 ASCII box 包裹

**输出示例**:
```
🔄 Changes

  ┌─────────────────────────────────────────┐
  │ Paragraph (para_123)                    │
  ├─────────────────────────────────────────┤
  │ Context line before change.             │
- │ Old text content here.                  │
+ │ New text content here.                  │
  │ Context line after change.              │
  └─────────────────────────────────────────┘
```

---

## 3. 数据设计

### 3.1 Markdown 响应格式规范

#### 3.1.1 成功响应

```markdown
# 操作结果: {operation}

**Status**: ✅ Success
**Element ID**: {element_id}
**Operation**: {operation}
**{Extra Field 1}**: {value1}
**{Extra Field 2}**: {value2}

---

## 📄 Document Context

{ASCII visualization}

---

## 🔄 Changes (optional)

{Git-style diff}
```

#### 3.1.2 错误响应

```markdown
# 操作结果: Error

**Status**: ❌ Error
**Error Type**: {error_type}
**Message**: {message}
```

### 3.2 ASCII 字符集

**边框字符**:
- 横线: `─`
- 竖线: `│`
- 左上角: `┌`
- 右上角: `┐`
- 左下角: `└`
- 右下角: `┘`
- 左T形: `├`
- 右T形: `┤`
- 上T形: `┬`
- 下T形: `┴`
- 十字: `┼`

**标记符号**:
- 当前元素: `⭐`
- 光标: `>>> [CURSOR] <<<`
- 图片: `[IMG: filename.png]`
- 省略: `... (N more elements) ...`

**Diff 前缀**:
- 不变: ` ` (空格)
- 删除: `-`
- 新增: `+`

---

## 4. 安全考量

### 4.1 内容截断

**风险**: 长文本可能导致响应过大，消耗大量 tokens

**缓解措施**:
- 段落文本截断为 80 字符
- 表格单元格截断为 20 字符
- 表格行数限制为 20 行
- 表格列数限制为 10 列
- 上下文范围固定为 10-15 个元素

### 4.2 特殊字符处理

**风险**: 文档内容可能包含 Markdown 特殊字符（如 `*`, `#`, `|`）

**缓解措施**:
- 在 ASCII box 内部，特殊字符不需要转义（因为不会被解析为 Markdown）
- 在元数据字段中，转义特殊字符（如 `**` → `\*\*`）

### 4.3 性能考量

**风险**: 大文档渲染可能耗时较长

**缓解措施**:
- 仅渲染上下文范围内的元素（不渲染全文档）
- 使用缓存机制（如果需要）
- 渲染时间目标：< 100ms

---

## 5. 兼容性设计

### 5.1 破坏性变更

**移除的函数**:
- `create_success_response()` → 替换为 `create_markdown_response()`
- `create_context_aware_response()` → 合并到 `create_markdown_response()`
- `create_change_tracked_response()` → 合并到 `create_markdown_response()`

**移除的类**:
- `ToolResponse` dataclass
- `CursorInfo` dataclass

**原因**: 不再需要 JSON 结构化数据，所有信息通过 Markdown 文本传递

### 5.2 迁移策略

**工具层迁移**:
```python
# 旧代码
return create_success_response(
    message="Paragraph created",
    element_id=para_id
)

# 新代码
return create_markdown_response(
    session=session,
    message="Paragraph created successfully",
    element_id=para_id,
    operation="Insert Paragraph"
)
```

**测试层迁移**:
```python
# 旧代码
data = json.loads(response)
assert data["status"] == "success"
element_id = data["data"]["element_id"]

# 新代码
assert "✅ Success" in response
assert "**Element ID**: para_" in response
# 使用正则提取 element_id
import re
match = re.search(r'\*\*Element ID\*\*: (para_\w+)', response)
element_id = match.group(1)
```

---

## 6. 实施计划

### 6.1 阶段划分

**Phase 1: 核心架构**（2-3 天）
- 创建 `visualizer.py` 模块
- 实现 `DocumentVisualizer` 类
- 实现 `DiffRenderer` 类
- 重构 `response.py`，实现 `create_markdown_response()`

**Phase 2: 工具迁移**（3-4 天）
- 迁移 Session Tools (4 个)
- 迁移 Paragraph Tools (6 个)
- 迁移 Run Tools (3 个)
- 迁移 Table Tools (13 个)
- 迁移 Format Tools (6 个)
- 迁移 Advanced Tools (3 个)
- 迁移 Cursor Tools (4 个)
- 迁移 Copy Tools (2 个)
- 迁移 Content Tools (4 个)
- 迁移 Composite Tools (5 个)
- 迁移 System Tools (1 个)

**Phase 3: 测试更新**（2-3 天）
- 更新所有单元测试（约 50+ 个测试文件）
- 更新所有 E2E 测试（约 10+ 个测试文件）
- 更新集成测试

**Phase 4: 文档更新**（1 天）
- 更新 README.md
- 更新 CLAUDE.md
- 添加迁移指南

**Phase 5: 增强功能**（可选，1-2 天）
- 实现图片位置标记
- 实现文档结构树
- 优化表格渲染

### 6.2 风险与挑战

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 测试用例更新工作量大 | 高 | 编写脚本批量更新测试断言 |
| ASCII 绘制逻辑复杂 | 中 | 参考 `tabulate` 库的实现 |
| 性能问题（大文档） | 中 | 限制上下文范围，避免全文档渲染 |
| 特殊字符处理 | 低 | 在 ASCII box 内部不转义 |

---

## 7. 测试策略

### 7.1 单元测试

**测试文件**: `tests/unit/test_visualizer.py` (新建)

**测试用例**:
- `test_render_paragraph_basic()`: 基本段落渲染
- `test_render_paragraph_with_format()`: 带格式的段落（粗体、斜体）
- `test_render_paragraph_truncation()`: 长文本截断
- `test_render_table_basic()`: 基本表格渲染
- `test_render_table_large()`: 大表格截断
- `test_render_context_middle()`: 中间位置上下文
- `test_render_context_start()`: 文档开头上下文
- `test_render_context_end()`: 文档结尾上下文
- `test_render_diff_basic()`: 基本 diff 渲染
- `test_render_diff_multiline()`: 多行 diff

**测试文件**: `tests/unit/test_response_markdown.py` (新建)

**测试用例**:
- `test_create_markdown_response_success()`: 成功响应
- `test_create_markdown_response_error()`: 错误响应
- `test_create_markdown_response_with_diff()`: 带 diff 的响应
- `test_create_markdown_response_no_context()`: 不显示上下文

### 7.2 集成测试

**测试文件**: `tests/integration/test_markdown_workflow.py` (新建)

**测试场景**:
- 创建段落 → 验证 Markdown 输出
- 更新段落 → 验证 diff 输出
- 创建表格 → 验证 ASCII 表格
- 复杂文档操作 → 验证上下文范围

### 7.3 E2E 测试更新

**策略**:
- 所有现有 E2E 测试需要更新断言
- 从 `json.loads()` 改为正则匹配
- 验证 Markdown 格式的关键字（如 `✅ Success`, `**Element ID**`）

---

## 8. 性能指标

### 8.1 渲染性能

| 操作 | 目标时间 | 测量方法 |
|------|---------|----------|
| 渲染单个段落 | < 5ms | `time.time()` |
| 渲染单个表格 | < 20ms | `time.time()` |
| 渲染上下文（10 元素） | < 50ms | `time.time()` |
| 渲染 diff | < 10ms | `time.time()` |
| 完整响应生成 | < 100ms | `time.time()` |

### 8.2 Token 消耗

| 场景 | 预估 Token 增加 | 说明 |
|------|----------------|------|
| 简单段落插入 | +500 tokens | 包含上下文（10 元素） |
| 段落更新（带 diff） | +800 tokens | 包含 diff + 上下文 |
| 表格插入 | +1000 tokens | 包含 ASCII 表格 + 上下文 |
| 复杂操作 | +1500 tokens | 大表格或长上下文 |

**说明**: 用户已明确表示不关心 token 消耗，优先保证完整展示。

---

## 9. 附录

### 9.1 ASCII Box 绘制算法

```python
def _draw_box(content: str, title: str, highlight: bool = False) -> str:
    """Draw ASCII box around content.

    Algorithm:
    1. Split content into lines
    2. Calculate max width (max of title and content lines)
    3. Draw top border: ┌ + ─ * width + ┐
    4. Draw title line: │ + title + padding + │
    5. Draw separator: ├ + ─ * width + ┤
    6. Draw content lines: │ + line + padding + │
    7. Draw bottom border: └ + ─ * width + ┘
    """
    lines = content.split('\n')
    max_width = max(len(title), max(len(line) for line in lines))

    result = []
    result.append('┌' + '─' * (max_width + 2) + '┐')
    result.append('│ ' + title.ljust(max_width) + ' │')
    result.append('├' + '─' * (max_width + 2) + '┤')
    for line in lines:
        result.append('│ ' + line.ljust(max_width) + ' │')
    result.append('└' + '─' * (max_width + 2) + '┘')

    return '\n'.join(result)
```

### 9.2 表格渲染算法

```python
def render_table(self, table, element_id: str, highlight: bool = False) -> str:
    """Render table as ASCII grid.

    Algorithm:
    1. Extract table dimensions (rows, cols)
    2. Extract cell contents (truncate to 20 chars)
    3. Calculate column widths (max of cell contents)
    4. Draw top border: ┌ + ─ + ┬ + ─ + ┐
    5. For each row:
        a. Draw cell contents: │ + cell + │
        b. Draw separator: ├ + ─ + ┼ + ─ + ┤
    6. Draw bottom border: └ + ─ + ┴ + ─ + ┘
    """
```

### 9.3 上下文范围算法

```python
def render_context(self, element_id: str, context_range: Optional[int] = None) -> str:
    """Render document context.

    Algorithm:
    1. Get all top-level elements (paragraphs + tables)
    2. Find index of element_id
    3. Calculate range: [index - context_range, index + context_range]
    4. Clamp range to [0, len(elements))
    5. If start > 0, add "... (N more elements above) ..."
    6. For each element in range:
        a. Render element (paragraph or table)
        b. If element == current, add highlight marker
    7. If end < len(elements), add "... (N more elements below) ..."
    8. Add cursor marker before current element
    """
```

---

**文档版本**: v1.0
**最后更新**: 2026-01-23
