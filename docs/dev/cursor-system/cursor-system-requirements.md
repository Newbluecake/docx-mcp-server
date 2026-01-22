---
feature: cursor-system
complexity: complex
generated_by: clarify
generated_at: 2026-01-21T10:00:00Z
version: 1
---

# 需求文档: Cursor 定位系统

> **功能标识**: cursor-system
> **复杂度**: complex
> **生成方式**: clarify
> **生成时间**: 2026-01-21

## 1. 概述

### 1.1 一句话描述
为 docx-mcp-server 引入基于 Cursor（光标）的定位系统，支持多光标管理、动态位置更新和锚点定位，使文档生成操作（如插入段落、表格）能够像文本编辑器一样在指定位置进行，而非仅能追加到末尾。

### 1.2 核心价值
- **复杂文档生成**：支持非线性写入（如先生成框架再填充内容），解决目录与正文交替生成的难题。
- **精细控制**：提供类似 IDE 的光标体验，支持光标的创建、移动、保存和恢复。
- **并发支持**：通过多光标机制，支持不同逻辑流同时操作文档的不同区域（如 header/footer 与正文并行生成）。

### 1.3 目标用户
- **主要用户**：使用 Claude 生成复杂结构 Word 文档的开发者/AI Agent。
- **次要用户**：需要精确控制模板填充位置的自动化脚本编写者。

---

## 2. 需求与用户故事

### 2.1 需求清单

| ID | 需求点 | 优先级 | 用户故事 |
|----|--------|--------|----------|
| R-001 | Cursor 核心模型 | P0 | 作为开发者，我需要系统维护一个或多个 Cursor 状态，以便在操作时知道当前的插入位置。 |
| R-002 | 多 Cursor 管理 | P0 | 作为开发者，我要能创建命名的 Cursor（如 'main', 'header'），并在它们之间切换上下文。 |
| R-003 | Cursor 操作接口 | P0 | 作为开发者，我需要能创建、移动、销毁 Cursor，并能查询 Cursor 当前的位置。 |
| R-004 | 基于 Position 的写入 | P0 | 作为开发者，当我调用 `docx_insert_paragraph` 等写入接口时，内容应按 `position` 插入，且 Cursor 仅用于导航。 |
| R-005 | 混合定位模式 | P1 | 作为开发者，我需要 Cursor 支持"动态跟随"（随内容插入移动）和"固定锚点"（始终指向特定元素）两种模式。 |
| R-006 | 严格错误处理 | P1 | 作为开发者，当 Cursor 指向的元素被删除时，操作应明确报错，而不是静默失败或尝试猜测。 |

### 2.2 验收标准

#### R-001/R-004: 核心写入体验
- **WHEN** 创建一个新 Cursor 并设为激活
- **AND** 连续调用 `docx_insert_paragraph` 三次
- **THEN** 文档中应按顺序出现这三个段落
- **AND** Cursor 最终位置应在第三个段落之后

#### R-002: 多 Cursor 并发
- **GIVEN** 有两个 Cursor：`c1` 在文档开头，`c2` 在文档末尾
- **WHEN** 切换到 `c1` 插入 "Title"
- **AND** 切换到 `c2` 插入 "Footer"
- **THEN** "Title" 应出现在开头，"Footer" 应出现在末尾，互不干扰

#### R-005: 插入行为
- **WHEN** 在两个现有段落 P1 和 P2 之间放置 Cursor
- **AND** 插入新段落 P_new
- **THEN** P_new 应该物理位于 P1 和 P2 之间
- **AND** Cursor 应该更新指向 P_new 之后

---

## 3. 功能验收清单

| ID | 功能点 | 验收步骤 | 优先级 | 关联需求 | 通过 |
|----|--------|----------|--------|----------|------|
| F-001 | `docx_create_cursor` | 创建命名 Cursor，支持指定初始位置（默认文档末尾）和类型（动态/锚点） | P0 | R-001, R-002 | ☐ |
| F-002 | `docx_set_active_cursor` | 切换当前 Session 的激活 Cursor | P0 | R-002 | ☐ |
| F-003 | `docx_move_cursor` | 将 Cursor 移动到指定 Element 之前/之后 | P0 | R-003 | ☐ |
| F-004 | 修改 `docx_insert_paragraph` | 重构现有接口，明确使用 `position` 插入 | P0 | R-004 | ☐ |
| F-005 | 修改 `docx_insert_table` | 重构现有接口，明确使用 `position` 插入 | P0 | R-004 | ☐ |
| F-006 | 修改 `docx_insert_run` | 重构现有接口，明确使用 `position` 插入 | P0 | R-004 | ☐ |
| F-007 | `docx_get_cursor_info` | 获取 Cursor 的详细信息（位置、类型、上下文） | P1 | R-003 | ☐ |
| F-008 | Cursor 失效检测 | 当关联 Element 被删除时，访问该 Cursor 应抛出明确异常 | P1 | R-006 | ☐ |

---

## 4. 技术约束

### 4.1 架构约束
- **破坏性更新**：允许修改现有的 `add_*` 接口签名和行为，不再强制向后兼容（但应保持参数尽量简洁）。
- **Session 隔离**：Cursor 状态必须严格绑定在 Session 内，跨 Session 不可见。
- **python-docx 限制**：底层 python-docx 库对"插入"操作的支持可能有限（通常是 append），可能需要操作底层 XML (`_element.addnext` 等) 来实现真正的插入。

### 4.2 数据结构
- Session 对象需新增 `cursors: Dict[str, Cursor]` 和 `active_cursor_id: str`。
- Cursor 对象需包含 `target_element_id`, `position` ('before'|'after'|'inside'), `type` ('dynamic'|'anchor')。

---

## 5. 排除项

- **跨文档 Copy/Paste**：Cursor 仅限于当前文档内的操作，不支持跨文档。
- **复杂的选区操作**：Cursor 是一个点，不是一个 Range（选区），不支持"选中一段文本并替换"（那是 `replace_text` 的职责）。
- **撤销/重做**：暂不实现 Undo/Redo 机制。

---

## 6. 下一步

✅ 建议在 Worktree 中执行开发：
```bash
# 1. 创建 worktree
bash ~/.claude/skills/git-worktree/scripts/worktree-manager.sh create cursor-system

# 2. 切换目录
cd .worktrees/feature/cursor-system-{date}

# 3. 开始设计与开发
/clouditera:dev:spec-dev cursor-system --skip-requirements
```
