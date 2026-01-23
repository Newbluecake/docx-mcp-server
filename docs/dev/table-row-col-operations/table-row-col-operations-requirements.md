---
feature: table-row-col-operations
complexity: standard
generated_by: clarify
generated_at: 2026-01-23T13:30:00+08:00
version: 1
---

# 需求文档: 表格行列操作增强

> **功能标识**: table-row-col-operations
> **复杂度**: standard
> **生成方式**: clarify
> **生成时间**: 2026-01-23 13:30:00

## 1. 概述

### 1.1 一句话描述
为 docx-mcp-server 添加表格的精确行列插入和删除功能，支持在任意位置插入行/列，以及按索引或 element_id 删除行/列。

### 1.2 核心价值
- **精确控制**: 支持在表格的任意位置插入行/列，而非仅限于末尾追加
- **灵活删除**: 支持通过索引或 element_id 两种方式删除行/列
- **格式保留**: 插入时可选择复制相邻行/列的格式，保持文档一致性
- **安全边界**: 防止删除最后一行/列，避免表格结构破坏
- **API 一致性**: 遵循项目现有的原子化 API 设计和 position 字符串规范

### 1.3 目标用户
- **主要用户**: 使用 docx-mcp-server 进行文档自动化生成的开发者和 AI Agent
- **次要用户**: 需要精确控制表格结构的文档处理系统

---

## 2. 需求与用户故事

### 2.1 需求清单

| ID | 需求点 | 优先级 | 用户故事 |
|----|--------|--------|----------|
| R-001 | 在指定位置插入行 | P0 | As a developer, I want to insert a row at a specific position in a table, so that I can build complex table structures programmatically |
| R-002 | 在指定位置插入列 | P0 | As a developer, I want to insert a column at a specific position in a table, so that I can dynamically adjust table layout |
| R-003 | 按索引删除行 | P0 | As a developer, I want to delete a row by its index, so that I can remove unwanted data from tables |
| R-004 | 按索引删除列 | P0 | As a developer, I want to delete a column by its index, so that I can adjust table structure |
| R-005 | 格式复制选项 | P1 | As a developer, I want to optionally copy formatting from adjacent rows/columns when inserting, so that the table maintains visual consistency |
| R-006 | 边界条件保护 | P0 | As a developer, I want the system to prevent deletion of the last row/column, so that table structure is never broken |
| R-007 | 索引越界检查 | P0 | As a developer, I want clear error messages when indices are out of range, so that I can debug issues quickly |
| R-008 | element_id 映射更新 | P1 | As a developer, I want element_id mappings to be automatically updated after deletion, so that subsequent operations remain valid |

### 2.2 验收标准

#### R-001: 在指定位置插入行
- **WHEN** 调用 `docx_insert_row_at(session_id, table_id, position="after:row_2", copy_format=True)`, **THEN** 系统 **SHALL**:
  - 在指定位置插入新行
  - 如果 `copy_format=True`，复制相邻行的单元格格式（字体、边框、背景色）
  - 返回 JSON 响应，包含 `table_id`、`new_row_count`、`inserted_at` 等信息
  - 更新 Session 的 cursor 位置到新插入的行

#### R-002: 在指定位置插入列
- **WHEN** 调用 `docx_insert_col_at(session_id, table_id, position="before:col_1", copy_format=False)`, **THEN** 系统 **SHALL**:
  - 在指定位置插入新列
  - 如果 `copy_format=False`，使用默认格式（空白单元格）
  - 返回 JSON 响应，包含 `table_id`、`new_col_count`、`inserted_at` 等信息
  - 更新 Session 的 cursor 位置

#### R-003: 按索引删除行
- **WHEN** 调用 `docx_delete_row(session_id, table_id, row_index=2)`, **THEN** 系统 **SHALL**:
  - 删除指定索引的行（0-based）
  - 如果是最后一行，返回错误 `{"status": "error", "error_type": "ValidationError", "message": "Cannot delete the last row"}`
  - 如果索引越界，返回错误 `{"status": "error", "error_type": "IndexError", "message": "Row index 10 out of range (table has 5 rows)"}`
  - 成功删除后，返回 JSON 响应，包含 `table_id`、`new_row_count`、`deleted_index` 等信息
  - 自动更新受影响的 element_id 映射（如果有单元格被注册）

#### R-004: 按索引删除列
- **WHEN** 调用 `docx_delete_col(session_id, table_id, col_index=1)`, **THEN** 系统 **SHALL**:
  - 删除指定索引的列（0-based）
  - 如果是最后一列，返回错误 `{"status": "error", "error_type": "ValidationError", "message": "Cannot delete the last column"}`
  - 如果索引越界，返回错误 `{"status": "error", "error_type": "IndexError", "message": "Column index 5 out of range (table has 3 columns)"}`
  - 成功删除后，返回 JSON 响应，包含 `table_id`、`new_col_count`、`deleted_index` 等信息
  - 自动更新受影响的 element_id 映射

#### R-005: 格式复制选项
- **WHEN** 插入行/列时指定 `copy_format=True`, **THEN** 系统 **SHALL**:
  - 复制相邻行/列的单元格格式（字体、边框、背景色、对齐方式）
  - 对于插入行：复制前一行的格式（如果在第一行之前插入，则复制后一行）
  - 对于插入列：复制前一列的格式（如果在第一列之前插入，则复制后一列）
- **WHEN** 插入行/列时指定 `copy_format=False` 或省略该参数, **THEN** 系统 **SHALL**:
  - 使用默认格式（空白单元格，无特殊格式）

#### R-006: 边界条件保护
- **WHEN** 尝试删除表格的最后一行, **THEN** 系统 **SHALL**:
  - 返回错误响应 `{"status": "error", "error_type": "ValidationError", "message": "Cannot delete the last row"}`
  - 不修改表格结构
- **WHEN** 尝试删除表格的最后一列, **THEN** 系统 **SHALL**:
  - 返回错误响应 `{"status": "error", "error_type": "ValidationError", "message": "Cannot delete the last column"}`
  - 不修改表格结构

#### R-007: 索引越界检查
- **WHEN** 提供的 `row_index` 或 `col_index` 超出表格范围, **THEN** 系统 **SHALL**:
  - 返回错误响应，包含清晰的错误信息（如 `"Row index 10 out of range (table has 5 rows)"`）
  - 不修改表格结构

#### R-008: element_id 映射更新
- **WHEN** 删除行/列后，某些单元格的 element_id 映射失效, **THEN** 系统 **SHALL**:
  - 自动从 `session.object_registry` 中移除失效的 element_id
  - 在响应中包含 `invalidated_ids` 列表，告知调用者哪些 ID 已失效
  - 后续对失效 ID 的操作应返回 `ElementNotFound` 错误

---

## 3. 功能验收清单

| ID | 功能点 | 验收步骤 | 优先级 | 关联需求 | 通过 |
|----|--------|----------|--------|----------|------|
| F-001 | 在行之后插入新行 | 1. 创建 3x3 表格 2. 调用 `docx_insert_row_at(table_id, position="after:1")` 3. 验证表格变为 4x3，新行在索引 2 | P0 | R-001 | ☐ |
| F-002 | 在行之前插入新行 | 1. 创建 3x3 表格 2. 调用 `docx_insert_row_at(table_id, position="before:1")` 3. 验证表格变为 4x3，新行在索引 1 | P0 | R-001 | ☐ |
| F-003 | 在表格开头插入行 | 1. 创建 3x3 表格 2. 调用 `docx_insert_row_at(table_id, position="start:table_id")` 3. 验证表格变为 4x3，新行在索引 0 | P0 | R-001 | ☐ |
| F-004 | 在表格末尾插入行 | 1. 创建 3x3 表格 2. 调用 `docx_insert_row_at(table_id, position="end:table_id")` 3. 验证表格变为 4x3，新行在索引 3 | P0 | R-001 | ☐ |
| F-005 | 在列之后插入新列 | 1. 创建 3x3 表格 2. 调用 `docx_insert_col_at(table_id, position="after:1")` 3. 验证表格变为 3x4，新列在索引 2 | P0 | R-002 | ☐ |
| F-006 | 在列之前插入新列 | 1. 创建 3x3 表格 2. 调用 `docx_insert_col_at(table_id, position="before:1")` 3. 验证表格变为 3x4，新列在索引 1 | P0 | R-002 | ☐ |
| F-007 | 按索引删除中间行 | 1. 创建 3x3 表格 2. 调用 `docx_delete_row(table_id, row_index=1)` 3. 验证表格变为 2x3 | P0 | R-003 | ☐ |
| F-008 | 按索引删除中间列 | 1. 创建 3x3 表格 2. 调用 `docx_delete_col(table_id, col_index=1)` 3. 验证表格变为 3x2 | P0 | R-004 | ☐ |
| F-009 | 禁止删除最后一行 | 1. 创建 1x3 表格 2. 调用 `docx_delete_row(table_id, row_index=0)` 3. 验证返回错误 `ValidationError` | P0 | R-006 | ☐ |
| F-010 | 禁止删除最后一列 | 1. 创建 3x1 表格 2. 调用 `docx_delete_col(table_id, col_index=0)` 3. 验证返回错误 `ValidationError` | P0 | R-006 | ☐ |
| F-011 | 索引越界检查（行） | 1. 创建 3x3 表格 2. 调用 `docx_delete_row(table_id, row_index=10)` 3. 验证返回错误 `IndexError` | P0 | R-007 | ☐ |
| F-012 | 索引越界检查（列） | 1. 创建 3x3 表格 2. 调用 `docx_delete_col(table_id, col_index=10)` 3. 验证返回错误 `IndexError` | P0 | R-007 | ☐ |
| F-013 | 插入行时复制格式 | 1. 创建表格，设置第一行为粗体红色 2. 调用 `docx_insert_row_at(table_id, position="after:0", copy_format=True)` 3. 验证新行的单元格格式与第一行一致 | P1 | R-005 | ☐ |
| F-014 | 插入列时复制格式 | 1. 创建表格，设置第一列为蓝色背景 2. 调用 `docx_insert_col_at(table_id, position="after:0", copy_format=True)` 3. 验证新列的单元格格式与第一列一致 | P1 | R-005 | ☐ |
| F-015 | element_id 映射更新 | 1. 创建 3x3 表格，注册所有单元格的 element_id 2. 删除第二行 3. 验证第二行的单元格 ID 在 `object_registry` 中被移除 4. 验证响应中包含 `invalidated_ids` 列表 | P1 | R-008 | ☐ |
| F-016 | 支持 position 字符串（索引方式） | 1. 创建 3x3 表格 2. 调用 `docx_insert_row_at(table_id, row_index=1, position="after")` 3. 验证新行在索引 2 | P0 | R-001 | ☐ |
| F-017 | 支持 element_id 删除 | 1. 创建 3x3 表格，注册第二行的 element_id 2. 调用 `docx_delete_row(table_id, row_id="row_abc123")` 3. 验证第二行被删除 | P1 | R-003 | ☐ |

---

## 4. 技术约束

### 4.1 技术栈
- **语言**: Python 3.8+
- **核心库**: python-docx
- **MCP 框架**: FastMCP
- **测试框架**: pytest, pytest-cov

### 4.2 API 设计

#### 新增工具函数

**1. docx_insert_row_at**
```python
def docx_insert_row_at(
    session_id: str,
    table_id: str,
    position: str,  # 支持 "after:1", "before:2", "start:table_id", "end:table_id"
    row_index: int = None,  # 可选：直接指定索引（与 position 二选一）
    copy_format: bool = False
) -> str:
    """
    在表格的指定位置插入新行。

    Args:
        session_id: 会话 ID
        table_id: 表格 ID
        position: 插入位置字符串（如 "after:1", "before:2"）
        row_index: 可选，直接指定行索引（0-based）
        copy_format: 是否复制相邻行的格式

    Returns:
        JSON 响应字符串
    """
```

**2. docx_insert_col_at**
```python
def docx_insert_col_at(
    session_id: str,
    table_id: str,
    position: str,  # 支持 "after:1", "before:2", "start:table_id", "end:table_id"
    col_index: int = None,  # 可选：直接指定索引（与 position 二选一）
    copy_format: bool = False
) -> str:
    """
    在表格的指定位置插入新列。

    Args:
        session_id: 会话 ID
        table_id: 表格 ID
        position: 插入位置字符串（如 "after:1", "before:2"）
        col_index: 可选，直接指定列索引（0-based）
        copy_format: 是否复制相邻列的格式

    Returns:
        JSON 响应字符串
    """
```

**3. docx_delete_row**
```python
def docx_delete_row(
    session_id: str,
    table_id: str,
    row_index: int = None,  # 可选：按索引删除
    row_id: str = None  # 可选：按 element_id 删除（与 row_index 二选一）
) -> str:
    """
    删除表格中的指定行。

    Args:
        session_id: 会话 ID
        table_id: 表格 ID
        row_index: 可选，行索引（0-based）
        row_id: 可选，行的 element_id

    Returns:
        JSON 响应字符串

    Raises:
        ValidationError: 尝试删除最后一行
        IndexError: 索引越界
        ElementNotFound: row_id 不存在
    """
```

**4. docx_delete_col**
```python
def docx_delete_col(
    session_id: str,
    table_id: str,
    col_index: int = None,  # 可选：按索引删除
    col_id: str = None  # 可选：按 element_id 删除（与 col_index 二选一）
) -> str:
    """
    删除表格中的指定列。

    Args:
        session_id: 会话 ID
        table_id: 表格 ID
        col_index: 可选，列索引（0-based）
        col_id: 可选，列的 element_id

    Returns:
        JSON 响应字符串

    Raises:
        ValidationError: 尝试删除最后一列
        IndexError: 索引越界
        ElementNotFound: col_id 不存在
    """
```

### 4.3 集成点
- **PositionResolver**: 解析 position 字符串（如 "after:1", "before:2"）
- **Session.object_registry**: 管理 element_id 映射，删除时需要清理失效的 ID
- **FormatPainter**: 复制单元格格式（字体、边框、背景色）
- **ElementManipulator**: 底层 XML 操作（插入、删除行/列）
- **ContextBuilder**: 构建响应数据，包含光标上下文

### 4.4 响应格式

**成功响应示例（插入行）**:
```json
{
  "status": "success",
  "message": "Row inserted at position 2",
  "data": {
    "element_id": "table_abc123",
    "table_id": "table_abc123",
    "new_row_count": 4,
    "inserted_at": 2,
    "copy_format": true,
    "cursor": {
      "element_id": "table_abc123",
      "position": "inside_end",
      "context": "Cursor: inside table (4 rows, 3 cols)"
    }
  }
}
```

**错误响应示例（删除最后一行）**:
```json
{
  "status": "error",
  "message": "Cannot delete the last row",
  "data": {
    "error_type": "ValidationError",
    "table_id": "table_abc123",
    "current_row_count": 1
  }
}
```

**错误响应示例（索引越界）**:
```json
{
  "status": "error",
  "message": "Row index 10 out of range (table has 5 rows)",
  "data": {
    "error_type": "IndexError",
    "table_id": "table_abc123",
    "requested_index": 10,
    "max_index": 4
  }
}
```

**成功响应示例（删除行，含失效 ID）**:
```json
{
  "status": "success",
  "message": "Row deleted at index 1",
  "data": {
    "element_id": "table_abc123",
    "table_id": "table_abc123",
    "new_row_count": 2,
    "deleted_index": 1,
    "invalidated_ids": ["cell_xyz789", "cell_xyz790", "cell_xyz791"],
    "cursor": {
      "element_id": "table_abc123",
      "position": "inside_end",
      "context": "Cursor: inside table (2 rows, 3 cols)"
    }
  }
}
```

---

## 5. 排除项

- **不支持合并单元格的行/列操作**: 如果表格包含合并单元格（gridSpan > 1），插入/删除操作可能导致结构错误。本期不处理合并单元格场景，遇到时返回警告或错误。
- **不支持批量删除**: 本期只支持单次删除一行/列，不支持批量删除多行/列。
- **不支持撤销/重做**: 删除操作不可逆，不提供撤销功能。
- **不支持行/列的移动**: 本期只支持插入和删除，不支持移动行/列到其他位置。
- **不支持嵌套表格**: 如果单元格内包含嵌套表格，本期不处理嵌套表格的行/列操作。

---

## 6. 下一步

✅ 需求已澄清，在当前会话继续执行：

```bash
/clouditera:dev:spec-dev table-row-col-operations --skip-requirements --no-worktree
```

或手动执行：
1. 阅读本需求文档，确认需求方向
2. 在当前会话执行 `/clouditera:dev:spec-dev table-row-col-operations --skip-requirements --no-worktree`
3. 系统将生成技术设计文档（design.md）和任务清单（tasks.md）
4. 按照 TDD 流程实施开发

---

**文档版本**: v1
**最后更新**: 2026-01-23 13:30:00
**生成方式**: /clouditera:dev:clarify
