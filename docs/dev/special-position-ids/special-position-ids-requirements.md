---
feature: special-position-ids
complexity: standard
generated_by: clarify
generated_at: 2026-01-24T10:30:00Z
version: 1
---

# 需求文档: Special Position IDs

> **功能标识**: special-position-ids
> **复杂度**: standard
> **生成方式**: clarify
> **生成时间**: 2026-01-24T10:30:00Z

## 1. 概述

### 1.1 一句话描述

添加特殊位置 ID（`last_insert`、`last_update`、`cursor`/`current`）支持，允许在所有 `element_id` 参数中使用这些语义化标识符，简化 Agent 代码。

### 1.2 核心价值

**解决的问题**：
- 当前 Agent 需要手动提取每次操作返回的 `element_id`，然后在下一步操作中传递
- 代码冗长，需要使用正则表达式解析 Markdown 响应
- 连续操作时容易出错（忘记提取 ID 或传递错误的 ID）

**带来的价值**：
- **简化代码**：Agent 可以直接使用 `last_insert` 而不需要提取 ID
- **提高可读性**：`position="after:last_insert"` 比 `position="after:para_a1b2c3"` 更直观
- **减少错误**：避免 ID 提取和传递过程中的错误

### 1.3 目标用户

- **主要用户**：Claude Agent（通过 MCP 协议调用 docx-mcp-server 的 AI Agent）
- **次要用户**：人类开发者（通过命令行或脚本调用 MCP 工具）

---

## 2. 需求与用户故事

### 2.1 需求清单

| ID | 需求点 | 优先级 | 用户故事 |
|----|--------|--------|----------|
| R-001 | 支持 `last_insert` 特殊 ID | P0 | As an Agent, I want to use `last_insert` in any `element_id` parameter, so that I don't need to extract and store the ID from previous operations |
| R-002 | 支持 `last_update` 特殊 ID | P0 | As an Agent, I want to use `last_update` to reference the most recently modified element, so that I can continue operations after updates |
| R-003 | 支持 `cursor`/`current` 特殊 ID | P0 | As an Agent, I want to use `cursor` or `current` to reference the session's cursor position, so that I can work with the current context |
| R-004 | 在所有 element_id 参数中支持 | P0 | As an Agent, I want to use special IDs in all tools (not just position), so that I have consistent behavior across all operations |
| R-005 | 明确的错误处理 | P0 | As an Agent, I want clear error messages when special IDs cannot be resolved, so that I can handle edge cases properly |
| R-006 | 删除后的引用行为 | P1 | As an Agent, I want to know that `last_insert` will error if the element is deleted, so that I can detect invalid references |

### 2.2 验收标准

#### R-001: 支持 `last_insert` 特殊 ID

- **WHEN** Agent 调用 `docx_insert_paragraph(session_id, "Text", position="end:document_body")`, **THEN** 系统 **SHALL** 在 session 中记录该段落的 ID 为 `last_insert`
- **WHEN** Agent 随后调用 `docx_insert_run(session_id, "Run", position="inside:last_insert")`, **THEN** 系统 **SHALL** 解析 `last_insert` 为前一步创建的段落 ID
- **WHEN** Agent 在会话刚创建时使用 `last_insert`, **THEN** 系统 **SHALL** 返回错误 "Special ID 'last_insert' not available: no insert operation in this session"

#### R-002: 支持 `last_update` 特殊 ID

- **WHEN** Agent 调用 `docx_update_paragraph_text(session_id, "para_123", "New text")`, **THEN** 系统 **SHALL** 在 session 中记录 `para_123` 为 `last_update`
- **WHEN** Agent 随后调用 `docx_set_alignment(session_id, "last_update", "center")`, **THEN** 系统 **SHALL** 解析 `last_update` 为 `para_123`
- **WHEN** Agent 在会话刚创建时使用 `last_update`, **THEN** 系统 **SHALL** 返回错误 "Special ID 'last_update' not available: no update operation in this session"

#### R-003: 支持 `cursor`/`current` 特殊 ID

- **WHEN** Agent 调用 `docx_cursor_move(session_id, "para_123", "after")`, **THEN** 系统 **SHALL** 更新 session.cursor 指向 `para_123`
- **WHEN** Agent 随后调用 `docx_insert_paragraph(session_id, "Text", position="after:cursor")`, **THEN** 系统 **SHALL** 解析 `cursor` 为 `para_123`
- **WHEN** Agent 使用 `current` 而非 `cursor`, **THEN** 系统 **SHALL** 将其视为 `cursor` 的别名
- **WHEN** session.cursor 未初始化时使用 `cursor`, **THEN** 系统 **SHALL** 返回错误 "Special ID 'cursor' not available: cursor not initialized"

#### R-004: 在所有 element_id 参数中支持

- **WHEN** Agent 在 `position` 参数中使用特殊 ID（如 `"after:last_insert"`）, **THEN** 系统 **SHALL** 正确解析
- **WHEN** Agent 在非 position 的 element_id 参数中使用特殊 ID（如 `docx_update_paragraph_text(session_id, "last_insert", ...)`）, **THEN** 系统 **SHALL** 正确解析
- **WHEN** Agent 在 `docx_format_copy(session_id, "last_insert", "last_update")` 中同时使用多个特殊 ID, **THEN** 系统 **SHALL** 分别解析每个 ID

#### R-005: 明确的错误处理

- **WHEN** 特殊 ID 无法解析（如 `last_insert` 不存在）, **THEN** 系统 **SHALL** 返回 Markdown 格式的错误响应，包含：
  - `**Status**: ❌ Error`
  - `**Error Type**: SpecialIDNotAvailable`
  - `**Message**: Special ID 'last_insert' not available: [reason]`
- **WHEN** 错误发生, **THEN** 系统 **SHALL NOT** 修改文档状态

#### R-006: 删除后的引用行为

- **WHEN** Agent 插入元素后删除它, **THEN** `last_insert` **SHALL** 仍然指向该元素的 ID（不自动更新）
- **WHEN** Agent 随后使用 `last_insert`, **THEN** 系统 **SHALL** 尝试解析该 ID，并返回 "Element 'para_123' not found" 错误（标准的 ElementNotFound 错误）

---

## 3. 功能验收清单

| ID | 功能点 | 验收步骤 | 优先级 | 关联需求 | 通过 |
|----|--------|----------|--------|----------|------|
| F-001 | last_insert 基本功能 | 1. 插入段落 2. 使用 `last_insert` 插入 Run 3. 验证 Run 在正确段落中 | P0 | R-001 | ☐ |
| F-002 | last_update 基本功能 | 1. 更新段落 2. 使用 `last_update` 设置对齐 3. 验证对齐应用到正确段落 | P0 | R-002 | ☐ |
| F-003 | cursor/current 基本功能 | 1. 移动 cursor 2. 使用 `cursor` 插入元素 3. 验证元素在正确位置 | P0 | R-003 | ☐ |
| F-004 | current 作为 cursor 别名 | 1. 移动 cursor 2. 使用 `current` 插入元素 3. 验证行为与 `cursor` 一致 | P0 | R-003 | ☐ |
| F-005 | position 参数中使用 | 1. 插入段落 2. 使用 `position="after:last_insert"` 插入下一个段落 3. 验证顺序正确 | P0 | R-004 | ☐ |
| F-006 | 非 position 参数中使用 | 1. 插入段落 2. 使用 `docx_update_paragraph_text(session_id, "last_insert", ...)` 3. 验证更新成功 | P0 | R-004 | ☐ |
| F-007 | 多个特殊 ID 同时使用 | 1. 插入段落 A 2. 更新段落 B 3. 使用 `docx_format_copy("last_insert", "last_update")` 4. 验证格式复制正确 | P0 | R-004 | ☐ |
| F-008 | 会话初始化时的错误 | 1. 创建新会话 2. 立即使用 `last_insert` 3. 验证返回明确错误 | P0 | R-005 | ☐ |
| F-009 | 元素删除后的错误 | 1. 插入段落 2. 删除该段落 3. 使用 `last_insert` 4. 验证返回 ElementNotFound 错误 | P1 | R-006 | ☐ |
| F-010 | 错误响应格式 | 1. 触发任意特殊 ID 错误 2. 验证响应包含 Status, Error Type, Message | P0 | R-005 | ☐ |

---

## 4. 技术约束

### 4.1 技术栈

- **语言**: Python 3.8+
- **依赖**: python-docx, mcp (Model Context Protocol)
- **架构**: 基于 Session 的状态管理

### 4.2 集成点

**修改的核心模块**：
1. **`src/docx_mcp_server/core/session.py`**
   - 添加 `last_insert_id`, `last_update_id` 属性
   - 添加 `resolve_special_id(special_id: str) -> str` 方法

2. **`src/docx_mcp_server/services/navigation.py`**
   - 修改 `PositionResolver.resolve()` 方法，支持特殊 ID 解析
   - 在解析 `target_id` 时调用 `session.resolve_special_id()`

3. **所有工具文件**（`src/docx_mcp_server/tools/*.py`）
   - 在接受 `element_id` 参数的地方，调用 `session.resolve_special_id()` 或 `session.get_object()`
   - `session.get_object()` 内部应自动处理特殊 ID

### 4.3 性能要求

- 特殊 ID 解析应为 O(1) 操作（直接查找 session 属性）
- 不应增加现有操作的延迟

### 4.4 兼容性

- **向后兼容**: 现有使用具体 element_id 的代码应继续工作
- **错误处理**: 新增的错误类型应遵循现有的 Markdown 响应格式

---

## 5. 排除项

- **不支持历史记录**：不支持 `last_insert[0]`, `last_insert[1]` 这样的历史索引
  - **原因**：增加复杂度，当前需求不需要
- **不支持自动 fallback**：当特殊 ID 无法解析时，不自动 fallback 到 `document_body` 或其他默认值
  - **原因**：明确的错误比隐式的 fallback 更安全
- **不支持选区（selection）**：暂不支持批量操作的选区概念
  - **原因**：需求优先级较低，可在后续版本添加
- **不自动同步 cursor 和 last_insert**：这两个是独立的跟踪机制
  - **原因**：保持灵活性，用户可能需要分别使用它们

---

## 6. 下一步

✅ 需求已澄清，建议在新会话中执行：

```bash
/clouditera:dev:spec-dev special-position-ids --skip-requirements
```

**或者使用 Worktree 隔离开发**：

```bash
# 选项 1: 创建 worktree 并在当前会话继续
# （Claude 会自动执行以下步骤）

# 选项 2: 手动创建 worktree，稍后执行
bash scripts/worktree-manager.sh create special-position-ids
cd .worktrees/feature/special-position-ids-$(date +%Y%m%d)
/clouditera:dev:spec-dev special-position-ids --skip-requirements
```

**预期输出**：
- `docs/dev/special-position-ids/special-position-ids-design.md` - 技术设计文档
- `docs/dev/special-position-ids/special-position-ids-tasks.md` - 任务分解
- 实现代码和测试
