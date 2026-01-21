---
feature: cursor-context-awareness
complexity: standard
generated_by: clarify
generated_at: 2026-01-21T14:00:00+08:00
version: 1
---

# 需求文档: Cursor Context Awareness

> **功能标识**: cursor-context-awareness
> **复杂度**: standard
> **生成方式**: clarify
> **生成时间**: 2026-01-21 14:00:00

## 1. 概述

### 1.1 一句话描述

在所有 MCP 工具的返回消息中自动附加 cursor 位置和周围元素的上下文信息，让 AI 模型能够感知文档的当前编辑位置和布局状态。

### 1.2 核心价值

**解决的问题**：
- 模型在调用 `docx_copy_table` 等操作后，不知道新元素被插入到文档的哪个位置
- 模型无法感知 cursor 周围的文档结构，导致后续操作缺乏上下文

**带来的价值**：
- 提升模型对文档编辑状态的感知能力
- 减少模型需要额外调用 `docx_cursor_get()` 的次数
- 让模型能够基于上下文做出更智能的编辑决策

### 1.3 目标用户

- **主要用户**：调用 docx-mcp-server 的 AI 模型（如 Claude）
- **次要用户**：使用 docx-mcp-server 的开发者（通过更清晰的返回消息理解操作结果）

---

## 2. 需求与用户故事

### 2.1 需求清单

| ID | 需求点 | 优先级 | 用户故事 |
|----|--------|--------|----------|
| R-001 | 统一返回消息格式 | P0 | As an AI model, I want all tool responses to include cursor context, so that I always know where I am in the document |
| R-002 | 显示前后元素概要 | P0 | As an AI model, I want to see 2 elements before and after the cursor, so that I understand the surrounding document structure |
| R-003 | 准确描述 cursor 位置 | P0 | As an AI model, I want to know the exact cursor position (element_id + position), so that I can plan my next operation |
| R-004 | 处理边界情况 | P1 | As an AI model, I want graceful handling when cursor is at document start/end, so that I don't get confusing error messages |
| R-005 | 内容截断规则 | P1 | As an AI model, I want long element content to be truncated reasonably, so that the context info is concise and readable |
| R-006 | 嵌套结构处理 | P1 | As an AI model, I want to understand cursor position in nested structures (tables, cells), so that I can navigate complex documents |

### 2.2 验收标准

#### R-001: 统一返回消息格式
- **WHEN** 任何 MCP 工具执行成功, **THEN** 系统 **SHALL** 在返回消息末尾附加 cursor 上下文信息
- **WHEN** 工具执行失败, **THEN** 系统 **SHALL NOT** 附加 cursor 信息（避免干扰错误消息）

#### R-002: 显示前后元素概要
- **WHEN** cursor 周围有足够元素, **THEN** 系统 **SHALL** 显示前 2 个和后 2 个元素的概要
- **WHEN** 元素概要包含, **THEN** 系统 **SHALL** 显示：元素类型、元素 ID、内容预览（截断到 50 字符）、样式信息（可选）

#### R-003: 准确描述 cursor 位置
- **WHEN** 返回 cursor 位置, **THEN** 系统 **SHALL** 使用格式 "Cursor: {position} {element_type} {element_id}"
- **WHEN** position 为 "after", **THEN** 系统 **SHALL** 描述为 "after Paragraph para_abc123"
- **WHEN** position 为 "inside_end", **THEN** 系统 **SHALL** 描述为 "inside Cell cell_xyz (at end)"

#### R-004: 处理边界情况
- **WHEN** cursor 在文档开头, **THEN** 系统 **SHALL** 显示 "[Document Start]" 而非前置元素
- **WHEN** cursor 在文档结尾, **THEN** 系统 **SHALL** 显示 "[Document End]" 而非后续元素
- **WHEN** 文档为空, **THEN** 系统 **SHALL** 显示 "Cursor: at empty document start"

#### R-005: 内容截断规则
- **WHEN** 元素内容超过 50 字符, **THEN** 系统 **SHALL** 截断并添加 "..."
- **WHEN** 元素内容包含换行符, **THEN** 系统 **SHALL** 替换为空格或 "↵"
- **WHEN** 元素为表格, **THEN** 系统 **SHALL** 显示 "Table (3x2)" 而非内容

#### R-006: 嵌套结构处理
- **WHEN** cursor 在表格单元格内, **THEN** 系统 **SHALL** 显示单元格内的前后元素，而非表格外的
- **WHEN** cursor 在单元格内且无前后元素, **THEN** 系统 **SHALL** 显示 "[Cell Start]" 或 "[Cell End]"
- **WHEN** 需要显示父容器, **THEN** 系统 **SHALL** 在上下文信息中添加 "Parent: Cell cell_xyz in Table table_abc"

---

## 3. 功能验收清单

| ID | 功能点 | 验收步骤 | 优先级 | 关联需求 | 通过 |
|----|--------|----------|--------|----------|------|
| F-001 | 基础上下文显示 | 1. 调用 `docx_add_paragraph()` 2. 检查返回消息包含 "Cursor: after Paragraph para_xxx" 3. 检查包含前后元素概要 | P0 | R-001, R-002, R-003 | ☐ |
| F-002 | 文档开头边界 | 1. 创建新文档 2. 调用 `docx_add_paragraph()` 3. 检查显示 "[Document Start]" | P1 | R-004 | ☐ |
| F-003 | 文档结尾边界 | 1. 在文档末尾添加段落 2. 检查显示 "[Document End]" | P1 | R-004 | ☐ |
| F-004 | 内容截断 | 1. 添加超过 50 字符的段落 2. 检查内容被截断为 "Long text content..." | P1 | R-005 | ☐ |
| F-005 | 表格内 cursor | 1. 在表格单元格内添加段落 2. 检查显示单元格内的上下文，而非表格外 | P1 | R-006 | ☐ |
| F-006 | 拷贝操作上下文 | 1. 调用 `docx_copy_table()` 2. 检查返回消息包含新表格的 cursor 位置和周围元素 | P0 | R-001, R-002 | ☐ |
| F-007 | 错误时不显示上下文 | 1. 调用工具时传入无效 session_id 2. 检查错误消息不包含 cursor 信息 | P0 | R-001 | ☐ |

---

## 4. 技术约束

### 4.1 技术栈
- **核心实现**：在 `src/docx_mcp_server/core/session.py` 的 `Session` 类中新增方法
- **工具层修改**：所有 `src/docx_mcp_server/tools/*.py` 中的工具返回消息需要调用统一接口
- **不修改**：`docx_cursor_get()` 工具的返回结构保持不变

### 4.2 集成点
- **Session.get_cursor_context()**：新增方法，返回格式化的上下文字符串
- **工具返回消息**：在成功返回时调用 `session.get_cursor_context()` 并附加到消息末尾

### 4.3 性能要求
- 上下文收集不应显著增加工具响应时间（< 10ms）
- 避免递归遍历整个文档树

---

## 5. 排除项

- ❌ **不修改 `docx_cursor_get()` 的返回结构**：该工具保持原有 JSON 格式，仅在其他工具的返回消息中附加上下文
- ❌ **不显示层级结构路径**：不显示 "Document > Table > Cell > Paragraph" 这样的完整路径（除非在嵌套结构中需要说明父容器）
- ❌ **不在失败消息中附加上下文**：工具执行失败时，返回消息仅包含错误信息，不附加 cursor 上下文

---

## 6. 实现细节建议

### 6.1 返回消息格式示例

**基础格式**（文档中间位置）：
```
Paragraph added successfully.

Cursor: after Paragraph para_abc123
Context:
  [-2] Heading h1_xyz: "Chapter 1" (Heading 1, bold)
  [-1] Paragraph para_prev: "This is the introduction..." (Normal)
  [Current] Paragraph para_abc123: "New paragraph content" (Normal)
  [+1] Table table_def: "Table (3x2)"
  [+2] Paragraph para_next: "Conclusion section starts..." (Normal)
```

**文档开头**：
```
Paragraph added successfully.

Cursor: after Paragraph para_abc123
Context:
  [Document Start]
  [Current] Paragraph para_abc123: "First paragraph" (Normal)
  [+1] Paragraph para_next: "Second paragraph..." (Normal)
  [+2] Table table_def: "Table (2x3)"
```

**表格单元格内**：
```
Paragraph added to cell successfully.

Cursor: inside Cell cell_xyz (at end)
Parent: Cell cell_xyz in Table table_abc (row 0, col 1)
Context:
  [Cell Start]
  [Current] Paragraph para_abc123: "Cell content" (Normal)
  [Cell End]
```

### 6.2 核心实现逻辑

```python
# 在 Session 类中新增方法
def get_cursor_context(self, num_before=2, num_after=2) -> str:
    """
    获取 cursor 周围的上下文信息

    Args:
        num_before: 显示前面多少个元素
        num_after: 显示后面多少个元素

    Returns:
        格式化的上下文字符串
    """
    cursor = self.cursor
    if not cursor.parent_id:
        return "Cursor: at empty document start"

    # 获取父容器
    parent = self.get_object(cursor.parent_id)

    # 获取当前元素
    current_element = None
    if cursor.element_id:
        current_element = self.get_object(cursor.element_id)

    # 获取前后元素
    siblings = self._get_siblings(parent)
    current_index = self._find_element_index(siblings, current_element)

    before_elements = siblings[max(0, current_index - num_before):current_index]
    after_elements = siblings[current_index + 1:current_index + 1 + num_after]

    # 格式化输出
    lines = [f"\nCursor: {self._format_cursor_position(cursor)}"]

    # 如果在嵌套结构中，显示父容器
    if self._is_nested_structure(parent):
        lines.append(f"Parent: {self._format_parent_info(parent)}")

    lines.append("Context:")

    # 前置元素
    if not before_elements and current_index == 0:
        lines.append("  [Document Start]" if not self._is_nested_structure(parent) else "  [Cell Start]")
    else:
        for i, elem in enumerate(before_elements):
            lines.append(f"  [{-(len(before_elements) - i)}] {self._format_element_summary(elem)}")

    # 当前元素
    if current_element:
        lines.append(f"  [Current] {self._format_element_summary(current_element)}")

    # 后续元素
    if not after_elements:
        lines.append("  [Document End]" if not self._is_nested_structure(parent) else "  [Cell End]")
    else:
        for i, elem in enumerate(after_elements, 1):
            lines.append(f"  [+{i}] {self._format_element_summary(elem)}")

    return "\n".join(lines)

def _format_element_summary(self, element) -> str:
    """格式化元素概要信息"""
    elem_type = type(element).__name__
    elem_id = self._get_element_id(element)

    # 获取内容预览
    if hasattr(element, 'text'):
        content = element.text[:50]
        if len(element.text) > 50:
            content += "..."
        content = content.replace('\n', ' ')
    elif elem_type == 'Table':
        rows = len(element.rows)
        cols = len(element.columns)
        content = f"Table ({rows}x{cols})"
    else:
        content = f"{elem_type}"

    # 获取样式信息（可选）
    style_info = ""
    if hasattr(element, 'style') and element.style:
        style_info = f" ({element.style.name})"

    return f"{elem_type} {elem_id}: \"{content}\"{style_info}"
```

### 6.3 工具层调用示例

```python
# 在每个工具的返回消息中附加上下文
def docx_add_paragraph(session_id: str, text: str, style: str = None, parent_id: str = None) -> str:
    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    # 原有逻辑
    paragraph = session.document.add_paragraph(text, style)
    para_id = session.register_object(paragraph, "para")

    # 更新 cursor
    session.cursor.move_to(para_id, "after")

    # 构建返回消息（附加上下文）
    base_message = f"Paragraph {para_id} added successfully."
    context = session.get_cursor_context()

    return base_message + context
```

---

## 7. 下一步

✅ 需求已澄清，在新会话中执行：

```bash
/clouditera:dev:spec-dev cursor-context-awareness --skip-requirements
```

或者，如果希望在隔离的 worktree 中开发：

```bash
# 创建 worktree 并切换
bash ~/.claude/skills/git-worktree/scripts/worktree-manager.sh create cursor-context-awareness
cd .worktrees/feature/cursor-context-awareness-20260121

# 在新会话中执行
/clouditera:dev:spec-dev cursor-context-awareness --skip-requirements
```

---

**文档生成时间**: 2026-01-21 14:00:00
**访谈轮次**: 5 轮
**复杂度评分**: 6/12 (standard)
