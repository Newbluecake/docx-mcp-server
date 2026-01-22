---
feature: table-change-tracking
complexity: complex
generated_by: clarify
generated_at: 2026-01-22T23:00:00+08:00
version: 1
---

# 需求文档: Table Change Tracking & History System

> **功能标识**: table-change-tracking
> **复杂度**: complex
> **生成方式**: clarify
> **生成时间**: 2026-01-22T23:00:00+08:00

## 1. 概述

### 1.1 一句话描述

为 docx-mcp-server 添加表格智能填充、结构可视化、变更追踪和类 Git 历史管理系统，提升模型对文档修改的可控性和可追溯性。

### 1.2 核心价值

**解决的问题**：
1. **表格填充脆弱性**：当前 `docx_fill_table` 和 `docx_smart_fill_table` 遇到不规则表格（合并单元格、行列不一致）时会崩溃或填充错误
2. **结构不可见**：模型在操作表格前无法预览表格结构（行列数、合并单元格位置），导致盲目操作
3. **修改不可追踪**：执行修改操作后，无法看到修改前后的对比，难以判断修改是否正确
4. **错误不可回撤**：一旦修改错误，无法撤销，只能重新加载文档或手动修复

**带来的价值**：
- **鲁棒性提升**：表格填充遇到不规则结构时智能停止，只填充规则部分，避免崩溃
- **可视化决策**：模型可以先查看表格结构，再决定如何操作，减少错误
- **透明化修改**：每次修改都返回变更前后对比和上下文，模型可以验证修改正确性
- **可恢复性**：支持类 Git 的历史记录和回撤机制，修改错误时可以快速恢复

### 1.3 目标用户

- **主要用户**：使用 docx-mcp-server 的 AI Agent（如 Claude），需要可靠地操作复杂 Word 文档
- **次要用户**：开发者和测试人员，需要调试和验证文档操作的正确性

---

## 2. 需求与用户故事

### 2.1 需求清单

| ID | 需求点 | 优先级 | 用户故事 |
|----|--------|--------|----------|
| R-001 | 表格智能填充 | P0 | As an AI agent, I want to fill tables safely, so that irregular tables don't cause crashes |
| R-002 | 表格结构可视化 | P0 | As an AI agent, I want to see table structure before operating, so that I can make informed decisions |
| R-003 | 变更追踪与对比 | P0 | As an AI agent, I want to see before/after changes, so that I can verify modifications are correct |
| R-004 | 历史记录系统 | P0 | As an AI agent, I want to track all operations, so that I can review what has been done |
| R-005 | 回撤与恢复 | P0 | As an AI agent, I want to undo mistakes, so that I can recover from errors quickly |

### 2.2 验收标准

#### R-001: 表格智能填充

**WHEN** 调用 `docx_fill_table` 或 `docx_smart_fill_table` 填充包含合并单元格的表格，**THEN** 系统 **SHALL**：
- 检测表格是否包含不规则结构（合并单元格、行列不一致、嵌套表格）
- 填充所有规则的单元格（未合并、可访问的单元格）
- 遇到不规则区域时停止填充该区域
- 返回成功填充的范围（起始行列、结束行列）和跳过的区域列表
- 在 JSON 响应的 `data` 字段中包含 `filled_range` 和 `skipped_regions`

**WHEN** 调用填充工具时表格完全规则，**THEN** 系统 **SHALL**：
- 正常填充所有单元格
- 返回完整的填充范围
- `skipped_regions` 为空数组

#### R-002: 表格结构可视化

**WHEN** 调用 `docx_get_table_structure(session_id, table_id)`，**THEN** 系统 **SHALL** 返回：
- ASCII 格式的表格可视化（使用 `+---+---+` 和 `| cell |` 风格）
- 每个单元格的文本内容（长文本截断为 20 字符）
- 合并单元格的标注（如 `[2x3]` 表示跨 2 行 3 列）
- 空单元格的标注（显示为 `[empty]`）
- 表格的基本元数据（总行数、总列数、是否包含合并单元格）

**示例输出**：
```
Table: 3 rows x 4 cols (has merged cells: yes)

+-------------------+----------+----------+----------+
| Header 1          | Header 2 | Header 3 | Header 4 |
+-------------------+----------+----------+----------+
| Cell (0,0) [2x1]  | Data 1   | Data 2   | Data 3   |
|                   |          |          |          |
+-------------------+----------+----------+----------+
| Cell (2,0)        | [empty]  | Data 4   | Data 5   |
+-------------------+----------+----------+----------+
```

#### R-003: 变更追踪与对比

**WHEN** 执行任何修改操作（如 `docx_update_paragraph_text`, `docx_fill_table`, `docx_set_font` 等），**THEN** 系统 **SHALL** 在 JSON 响应的 `data.changes` 字段中返回：
- `before`: 修改前的内容（文本、单元格值、格式属性等）
- `after`: 修改后的内容
- `affected_elements`: 受影响元素的 ID 列表和位置信息
- `context`: 变更区域的上下文（如表格的前后几行、段落的前后段落）

**示例**：
```json
{
  "status": "success",
  "message": "Table filled successfully",
  "data": {
    "element_id": "table_abc123",
    "changes": {
      "before": {
        "cells": [
          {"row": 0, "col": 0, "text": ""},
          {"row": 0, "col": 1, "text": ""}
        ]
      },
      "after": {
        "cells": [
          {"row": 0, "col": 0, "text": "Alice"},
          {"row": 0, "col": 1, "text": "30"}
        ]
      },
      "affected_elements": [
        {"element_id": "cell_001", "position": "(0,0)"},
        {"element_id": "cell_002", "position": "(0,1)"}
      ],
      "context": {
        "table_id": "table_abc123",
        "total_rows": 5,
        "modified_rows": [0]
      }
    }
  }
}
```

#### R-004: 历史记录系统

**WHEN** 执行任何修改操作，**THEN** 系统 **SHALL**：
- 自动创建一个 commit 记录，包含：
  - `commit_id`: 唯一标识符（UUID）
  - `timestamp`: 操作时间戳（ISO 8601 格式）
  - `operation`: 操作类型（如 "update_paragraph_text", "fill_table"）
  - `changes`: 增量变更数据（只保存修改的部分，不保存完整文档快照）
  - `affected_elements`: 受影响元素的 ID 列表
- 将 commit 记录添加到 session 的历史栈中
- 保存所有历史记录直到 session 关闭（无数量限制）

**WHEN** 调用 `docx_log(session_id, limit=10)`，**THEN** 系统 **SHALL** 返回：
- 最近 N 条 commit 记录（默认 10 条）
- 每条记录包含：commit_id、timestamp、operation、affected_elements 摘要
- 按时间倒序排列（最新的在前）

#### R-005: 回撤与恢复

**WHEN** 调用 `docx_rollback(session_id, commit_id=None)`，**THEN** 系统 **SHALL**：
- 如果 `commit_id` 为 None，回撤到上一个 commit（类似 `git reset HEAD~1`）
- 如果指定 `commit_id`，回撤到该 commit 状态（类似 `git reset <commit>`）
- 应用反向变更（根据历史记录中的增量数据恢复）
- 返回回撤的详细信息（回撤了哪些操作、恢复了哪些内容）

**WHEN** 调用 `docx_checkout(session_id, commit_id)`，**THEN** 系统 **SHALL**：
- 将文档状态恢复到指定 commit 时的状态
- 保留当前 commit 之后的历史记录（不删除，类似 git checkout）
- 返回 checkout 的详细信息

---

## 3. 功能验收清单

| ID | 功能点 | 验收步骤 | 优先级 | 关联需求 | 通过 |
|----|--------|----------|--------|----------|------|
| F-001 | 表格不规则检测 | 1. 创建包含合并单元格的表格 2. 调用检测函数 3. 验证返回正确的不规则区域 | P0 | R-001 | ☐ |
| F-002 | 智能填充规则部分 | 1. 填充不规则表格 2. 验证规则单元格被填充 3. 验证不规则区域被跳过 | P0 | R-001 | ☐ |
| F-003 | ASCII 表格可视化 | 1. 调用 docx_get_table_structure 2. 验证输出格式正确 3. 验证合并单元格标注正确 | P0 | R-002 | ☐ |
| F-004 | 变更追踪返回 | 1. 执行修改操作 2. 验证返回包含 before/after 3. 验证上下文信息完整 | P0 | R-003 | ☐ |
| F-005 | 自动 commit 创建 | 1. 执行修改操作 2. 调用 docx_log 3. 验证 commit 记录已创建 | P0 | R-004 | ☐ |
| F-006 | 历史记录查询 | 1. 执行多次操作 2. 调用 docx_log 3. 验证返回正确的历史记录 | P0 | R-004 | ☐ |
| F-007 | 单步回撤 | 1. 执行修改 2. 调用 docx_rollback() 3. 验证修改被撤销 | P0 | R-005 | ☐ |
| F-008 | 指定版本回撤 | 1. 执行多次修改 2. 调用 docx_rollback(commit_id) 3. 验证回到指定版本 | P0 | R-005 | ☐ |
| F-009 | Checkout 到历史版本 | 1. 执行多次修改 2. 调用 docx_checkout(commit_id) 3. 验证文档状态正确 | P0 | R-005 | ☐ |

---

## 4. 技术约束

### 4.1 技术栈

- **核心库**：python-docx（现有依赖）
- **数据结构**：使用 Python 内置数据结构（dict, list）存储历史记录
- **序列化**：JSON 格式存储增量变更数据
- **ID 生成**：使用 UUID 生成 commit_id

### 4.2 架构约束

**Session 类改造**：
- 新增 `history_stack: List[Commit]` 属性，存储所有 commit 记录
- 新增 `current_commit_index: int` 属性，指向当前 commit 位置
- 新增 `create_commit(operation, changes, affected_elements)` 方法
- 新增 `rollback(commit_id)` 和 `checkout(commit_id)` 方法

**Commit 数据结构**：
```python
@dataclass
class Commit:
    commit_id: str  # UUID
    timestamp: str  # ISO 8601
    operation: str  # 操作类型
    changes: Dict[str, Any]  # 增量变更数据
    affected_elements: List[str]  # 受影响元素 ID
```

**变更追踪集成**：
- 所有修改类工具（update_*, set_*, fill_*, replace_*, etc.）都需要：
  1. 在修改前捕获当前状态（before）
  2. 执行修改
  3. 捕获修改后状态（after）
  4. 调用 `session.create_commit()` 创建历史记录
  5. 在 JSON 响应中包含 `changes` 字段

### 4.3 性能约束

- **增量存储**：只保存变更的增量数据，不保存完整文档快照
- **内存管理**：历史记录保存在内存中，session 关闭时释放
- **无数量限制**：保存所有历史记录直到 session 关闭（用户选择）

### 4.4 集成点

**需要修改的模块**：
1. `src/docx_mcp_server/core/session.py` - 添加历史记录系统
2. `src/docx_mcp_server/core/response.py` - 扩展响应格式支持 changes 字段
3. `src/docx_mcp_server/tools/table_tools.py` - 添加智能填充和结构可视化
4. `src/docx_mcp_server/tools/paragraph_tools.py` - 集成变更追踪
5. `src/docx_mcp_server/tools/run_tools.py` - 集成变更追踪
6. `src/docx_mcp_server/tools/format_tools.py` - 集成变更追踪
7. `src/docx_mcp_server/tools/advanced_tools.py` - 集成变更追踪
8. 新增 `src/docx_mcp_server/tools/history_tools.py` - 历史记录和回撤工具

---

## 5. 排除项

- **不支持 redo 功能**：只支持 rollback 和 checkout，不支持 redo（可在后续版本添加）
- **不支持分支管理**：不支持类似 git branch 的分支功能，只有线性历史
- **不支持持久化**：历史记录只在 session 生命周期内有效，不保存到磁盘
- **不支持合并冲突解决**：不处理多个 session 同时修改同一文档的冲突
- **不支持嵌套表格的智能填充**：嵌套表格视为不规则结构，跳过填充
- **不支持图片单元格的可视化**：图片单元格在 ASCII 输出中显示为 `[image]`

---

## 6. 下一步

✅ 需求已澄清，建议在新会话中执行：

```bash
/clouditera:dev:spec-dev table-change-tracking --skip-requirements
```

**建议使用 Worktree 隔离开发**：
- 创建独立工作区避免影响主分支
- 在当前会话继续执行 spec-dev

---

## 附录 A: 不规则表格定义

**不规则表格**包括以下情况：

1. **合并单元格**：
   - 横向合并（colspan）：一个单元格占据多列
   - 纵向合并（rowspan）：一个单元格占据多行

2. **行列不一致**：
   - 某些行的列数与其他行不同
   - 表格结构不是标准的矩形

3. **嵌套表格**：
   - 单元格内包含另一个表格

4. **特殊格式单元格**：
   - 空单元格（无内容）
   - 图片单元格（包含图片而非文本）

**检测策略**：
- 遍历表格的所有行和单元格
- 检查每个单元格的 `grid_span`（列跨度）和 `row_span`（行跨度）属性
- 检查每行的单元格数量是否一致
- 检查单元格内是否包含嵌套表格

---

## 附录 B: ASCII 表格输出示例

### 示例 1: 规则表格

```
Table: 3 rows x 3 cols (has merged cells: no)

+----------+----------+----------+
| Name     | Age      | City     |
+----------+----------+----------+
| Alice    | 30       | NYC      |
+----------+----------+----------+
| Bob      | 25       | LA       |
+----------+----------+----------+
```

### 示例 2: 包含合并单元格的表格

```
Table: 4 rows x 4 cols (has merged cells: yes)

+-------------------+----------+----------+----------+
| Header [1x2]      |          | Col 3    | Col 4    |
+-------------------+----------+----------+----------+
| Row 1 [2x1]       | Data 1   | Data 2   | Data 3   |
|                   |          |          |          |
+-------------------+----------+----------+----------+
| Row 3             | [empty]  | Data 4   | Data 5   |
+-------------------+----------+----------+----------+
```

### 示例 3: 长文本截断

```
Table: 2 rows x 2 cols (has merged cells: no)

+----------------------+----------------------+
| This is a very lo... | Short text           |
+----------------------+----------------------+
| Another long text... | [empty]              |
+----------------------+----------------------+
```

---

**文档结束**
