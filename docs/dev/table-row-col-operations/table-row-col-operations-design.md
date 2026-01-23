# 技术设计文档: 表格行列操作增强

> **功能标识**: table-row-col-operations
> **复杂度**: standard
> **设计版本**: v1
> **设计日期**: 2026-01-23

## 1. 系统架构设计

### 1.1 架构概览

本功能在现有的 docx-mcp-server 架构基础上，扩展表格操作能力。核心设计遵循项目的原子化 API 原则和 ID 映射系统。

```
┌─────────────────────────────────────────────────────────────┐
│                     MCP Client (Claude)                      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server (FastMCP)                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         Table Row/Col Tools (New)                     │  │
│  │  - docx_insert_row_at()                               │  │
│  │  - docx_insert_col_at()                               │  │
│  │  - docx_delete_row()                                  │  │
│  │  - docx_delete_col()                                  │  │
│  └───────────────────────────────────────────────────────┘  │
│                              ↓                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         Core Services (Existing)                      │  │
│  │  - SessionManager                                     │  │
│  │  - PositionResolver                                   │  │
│  │  - FormatPainter (New)                                │  │
│  │  - ElementManipulator (Enhanced)                      │  │
│  │  - ContextBuilder                                     │  │
│  └───────────────────────────────────────────────────────┘  │
│                              ↓                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         Session & Object Registry                     │  │
│  │  - Document                                           │  │
│  │  - object_registry (element_id mapping)               │  │
│  │  - Cursor                                             │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    python-docx Library                       │
│  - Table, Row, Cell objects                                 │
│  - XML manipulation (lxml)                                  │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 核心组件

#### 1.2.1 Table Row/Col Tools (新增)

位置: `src/docx_mcp_server/tools/table_rowcol_tools.py`

职责:
- 提供 4 个 MCP 工具函数
- 参数验证和错误处理
- 调用核心服务完成操作
- 返回标准化 JSON 响应

#### 1.2.2 ElementManipulator (增强)

位置: `src/docx_mcp_server/core/element_manipulator.py`

新增方法:
- `insert_row_at(table, index, copy_format_from=None)`: 在指定索引插入行
- `insert_col_at(table, index, copy_format_from=None)`: 在指定索引插入列
- `delete_row(table, index)`: 删除指定索引的行
- `delete_col(table, index)`: 删除指定索引的列

职责:
- 底层 XML 操作（使用 python-docx 和 lxml）
- 处理行/列的插入和删除
- 确保表格结构完整性

#### 1.2.3 FormatPainter (新增)

位置: `src/docx_mcp_server/core/format_painter.py`

方法:
- `copy_row_format(source_row, target_row)`: 复制行格式
- `copy_col_format(source_col_index, target_col_index, table)`: 复制列格式
- `copy_cell_format(source_cell, target_cell)`: 复制单元格格式

职责:
- 复制单元格的字体、边框、背景色、对齐方式
- 处理段落和 Run 级别的格式
- 支持跨行/列的格式复制

#### 1.2.4 PositionResolver (增强)

位置: `src/docx_mcp_server/core/position_resolver.py`

新增方法:
- `resolve_table_position(position, table, dimension)`: 解析表格内的位置字符串
  - 支持 "after:1", "before:2", "start:table_id", "end:table_id"
  - dimension 参数指定是行还是列 ("row" 或 "col")

#### 1.2.5 RegistryCleaner (新增)

位置: `src/docx_mcp_server/core/registry_cleaner.py`

方法:
- `invalidate_row_cells(session, table_id, row_index)`: 清理删除行的单元格 ID
- `invalidate_col_cells(session, table_id, col_index)`: 清理删除列的单元格 ID
- `find_invalidated_ids(session, table, row_index=None, col_index=None)`: 查找失效的 element_id

职责:
- 在删除行/列后，清理 object_registry 中失效的 element_id
- 返回失效 ID 列表，供响应使用

## 2. 接口设计

### 2.1 MCP 工具接口

#### 2.1.1 docx_insert_row_at

```python
@mcp.tool()
def docx_insert_row_at(
    session_id: str,
    table_id: str,
    position: str,
    row_index: int = None,
    copy_format: bool = False
) -> str:
    """
    在表格的指定位置插入新行。

    Args:
        session_id: 会话 ID
        table_id: 表格的 element_id
        position: 插入位置字符串
            - "after:N" - 在第 N 行之后插入（N 为 0-based 索引）
            - "before:N" - 在第 N 行之前插入
            - "start:table_id" - 在表格开头插入
            - "end:table_id" - 在表格末尾插入
        row_index: 可选，直接指定行索引（与 position 二选一）
        copy_format: 是否复制相邻行的格式（默认 False）

    Returns:
        JSON 响应字符串:
        {
            "status": "success",
            "message": "Row inserted at position 2",
            "data": {
                "element_id": "table_abc123",
                "table_id": "table_abc123",
                "new_row_count": 4,
                "inserted_at": 2,
                "copy_format": true,
                "cursor": {...}
            }
        }

    Raises:
        SessionNotFound: 会话不存在
        ElementNotFound: table_id 不存在
        ValidationError: position 格式错误或索引越界
    """
```

#### 2.1.2 docx_insert_col_at

```python
@mcp.tool()
def docx_insert_col_at(
    session_id: str,
    table_id: str,
    position: str,
    col_index: int = None,
    copy_format: bool = False
) -> str:
    """
    在表格的指定位置插入新列。

    Args:
        session_id: 会话 ID
        table_id: 表格的 element_id
        position: 插入位置字符串
            - "after:N" - 在第 N 列之后插入（N 为 0-based 索引）
            - "before:N" - 在第 N 列之前插入
            - "start:table_id" - 在表格开头插入
            - "end:table_id" - 在表格末尾插入
        col_index: 可选，直接指定列索引（与 position 二选一）
        copy_format: 是否复制相邻列的格式（默认 False）

    Returns:
        JSON 响应字符串（格式同 docx_insert_row_at）

    Raises:
        SessionNotFound: 会话不存在
        ElementNotFound: table_id 不存在
        ValidationError: position 格式错误或索引越界
    """
```

#### 2.1.3 docx_delete_row

```python
@mcp.tool()
def docx_delete_row(
    session_id: str,
    table_id: str,
    row_index: int = None,
    row_id: str = None
) -> str:
    """
    删除表格中的指定行。

    Args:
        session_id: 会话 ID
        table_id: 表格的 element_id
        row_index: 可选，行索引（0-based）
        row_id: 可选，行的 element_id（与 row_index 二选一）

    Returns:
        JSON 响应字符串:
        {
            "status": "success",
            "message": "Row deleted at index 1",
            "data": {
                "element_id": "table_abc123",
                "table_id": "table_abc123",
                "new_row_count": 2,
                "deleted_index": 1,
                "invalidated_ids": ["cell_xyz789", "cell_xyz790"],
                "cursor": {...}
            }
        }

    Raises:
        SessionNotFound: 会话不存在
        ElementNotFound: table_id 或 row_id 不存在
        ValidationError: 尝试删除最后一行
        IndexError: row_index 越界
    """
```

#### 2.1.4 docx_delete_col

```python
@mcp.tool()
def docx_delete_col(
    session_id: str,
    table_id: str,
    col_index: int = None,
    col_id: str = None
) -> str:
    """
    删除表格中的指定列。

    Args:
        session_id: 会话 ID
        table_id: 表格的 element_id
        col_index: 可选，列索引（0-based）
        col_id: 可选，列的 element_id（与 col_index 二选一）

    Returns:
        JSON 响应字符串（格式同 docx_delete_row）

    Raises:
        SessionNotFound: 会话不存在
        ElementNotFound: table_id 或 col_id 不存在
        ValidationError: 尝试删除最后一列
        IndexError: col_index 越界
    """
```

### 2.2 内部服务接口

#### 2.2.1 ElementManipulator

```python
class ElementManipulator:
    @staticmethod
    def insert_row_at(
        table: Table,
        index: int,
        copy_format_from: int = None
    ) -> _Row:
        """
        在表格的指定索引插入新行。

        Args:
            table: python-docx Table 对象
            index: 插入位置（0-based）
            copy_format_from: 可选，复制格式的源行索引

        Returns:
            新插入的 _Row 对象

        Raises:
            IndexError: index 超出范围 [0, len(table.rows)]
        """

    @staticmethod
    def insert_col_at(
        table: Table,
        index: int,
        copy_format_from: int = None
    ) -> None:
        """
        在表格的指定索引插入新列。

        Args:
            table: python-docx Table 对象
            index: 插入位置（0-based）
            copy_format_from: 可选，复制格式的源列索引

        Raises:
            IndexError: index 超出范围 [0, len(table.columns)]
        """

    @staticmethod
    def delete_row(table: Table, index: int) -> None:
        """
        删除表格的指定行。

        Args:
            table: python-docx Table 对象
            index: 行索引（0-based）

        Raises:
            IndexError: index 超出范围
            ValidationError: 尝试删除最后一行
        """

    @staticmethod
    def delete_col(table: Table, index: int) -> None:
        """
        删除表格的指定列。

        Args:
            table: python-docx Table 对象
            index: 列索引（0-based）

        Raises:
            IndexError: index 超出范围
            ValidationError: 尝试删除最后一列
        """
```

#### 2.2.2 FormatPainter

```python
class FormatPainter:
    @staticmethod
    def copy_row_format(source_row: _Row, target_row: _Row) -> None:
        """
        复制行的格式（逐单元格复制）。

        Args:
            source_row: 源行
            target_row: 目标行
        """

    @staticmethod
    def copy_col_format(
        table: Table,
        source_col_index: int,
        target_col_index: int
    ) -> None:
        """
        复制列的格式（逐单元格复制）。

        Args:
            table: 表格对象
            source_col_index: 源列索引
            target_col_index: 目标列索引
        """

    @staticmethod
    def copy_cell_format(source_cell: _Cell, target_cell: _Cell) -> None:
        """
        复制单元格的格式。

        包括:
        - 段落格式（对齐方式、行距）
        - Run 格式（字体、大小、颜色、粗体、斜体）
        - 单元格背景色
        - 单元格边框

        Args:
            source_cell: 源单元格
            target_cell: 目标单元格
        """
```

#### 2.2.3 RegistryCleaner

```python
class RegistryCleaner:
    @staticmethod
    def find_invalidated_ids(
        session: Session,
        table: Table,
        row_index: int = None,
        col_index: int = None
    ) -> list[str]:
        """
        查找删除行/列后失效的 element_id。

        Args:
            session: 会话对象
            table: 表格对象
            row_index: 可选，删除的行索引
            col_index: 可选，删除的列索引

        Returns:
            失效的 element_id 列表
        """

    @staticmethod
    def invalidate_ids(session: Session, ids: list[str]) -> None:
        """
        从 object_registry 中移除失效的 element_id。

        Args:
            session: 会话对象
            ids: 要移除的 element_id 列表
        """
```

## 3. 数据设计

### 3.1 element_id 映射

本功能不引入新的 element_id 类型。使用现有的:
- `table_*` - 表格
- `cell_*` - 单元格

注意: 行和列本身不分配 element_id（python-docx 的 _Row 和 _Column 对象不稳定），通过索引引用。

### 3.2 Position 字符串格式

扩展现有的 position 字符串规范，支持表格内的行/列定位:

| 格式 | 说明 | 示例 |
|------|------|------|
| `after:N` | 在第 N 行/列之后 | `after:1` |
| `before:N` | 在第 N 行/列之前 | `before:2` |
| `start:table_id` | 在表格开头 | `start:table_abc123` |
| `end:table_id` | 在表格末尾 | `end:table_abc123` |

### 3.3 响应数据结构

#### 插入操作响应

```json
{
  "status": "success",
  "message": "Row inserted at position 2",
  "data": {
    "element_id": "table_abc123",
    "table_id": "table_abc123",
    "new_row_count": 4,
    "new_col_count": 3,
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

#### 删除操作响应

```json
{
  "status": "success",
  "message": "Row deleted at index 1",
  "data": {
    "element_id": "table_abc123",
    "table_id": "table_abc123",
    "new_row_count": 2,
    "new_col_count": 3,
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

## 4. 安全考量

### 4.1 输入验证

1. **Session 验证**: 所有操作前检查 session_id 是否有效
2. **Element 验证**: 检查 table_id 是否存在且类型正确
3. **索引验证**: 检查 row_index/col_index 是否在有效范围内
4. **Position 验证**: 检查 position 字符串格式是否正确

### 4.2 边界条件保护

1. **最后一行/列保护**: 禁止删除表格的最后一行或最后一列
2. **索引越界保护**: 插入和删除操作前检查索引范围
3. **空表格保护**: 确保表格至少有 1 行 1 列

### 4.3 错误处理

所有错误通过标准化 JSON 响应返回，不抛出异常:

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

错误类型:
- `SessionNotFound`: 会话不存在
- `ElementNotFound`: 元素不存在
- `ValidationError`: 参数验证失败
- `IndexError`: 索引越界

### 4.4 并发安全

本项目采用单线程模型（MCP STDIO），无需考虑并发问题。每个会话独立，互不干扰。

## 5. 性能考量

### 5.1 时间复杂度

| 操作 | 时间复杂度 | 说明 |
|------|-----------|------|
| 插入行 | O(n) | n 为表格行数，需要移动后续行的 XML 节点 |
| 插入列 | O(n*m) | n 为行数，m 为列数，需要为每行插入单元格 |
| 删除行 | O(n) | n 为表格行数 |
| 删除列 | O(n*m) | n 为行数，m 为列数 |
| 格式复制 | O(m) | m 为单元格数（行操作）或 O(n)（列操作）|
| Registry 清理 | O(k) | k 为 object_registry 中的元素数 |

### 5.2 空间复杂度

- 插入操作: O(m)（新行的单元格数）或 O(n)（新列的单元格数）
- 删除操作: O(1)（仅删除引用）
- 格式复制: O(1)（复制格式属性，不复制内容）

### 5.3 优化策略

1. **延迟格式复制**: 仅在 `copy_format=True` 时执行格式复制
2. **批量 Registry 清理**: 一次性查找并清理所有失效 ID
3. **XML 直接操作**: 使用 lxml 直接操作 XML，避免 python-docx 的高层抽象开销

## 6. 测试策略

### 6.1 单元测试

位置: `tests/unit/test_table_rowcol_tools.py`

测试用例:
1. **插入行测试**:
   - 在表格中间插入行
   - 在表格开头插入行
   - 在表格末尾插入行
   - 插入行并复制格式
   - 索引越界测试

2. **插入列测试**:
   - 在表格中间插入列
   - 在表格开头插入列
   - 在表格末尾插入列
   - 插入列并复制格式
   - 索引越界测试

3. **删除行测试**:
   - 删除中间行
   - 删除第一行
   - 删除最后一行（应失败）
   - 索引越界测试
   - element_id 映射清理测试

4. **删除列测试**:
   - 删除中间列
   - 删除第一列
   - 删除最后一列（应失败）
   - 索引越界测试
   - element_id 映射清理测试

5. **格式复制测试**:
   - 复制行格式（字体、颜色、背景）
   - 复制列格式
   - 边界情况（第一行/列之前插入）

### 6.2 集成测试

位置: `tests/integration/test_table_rowcol_integration.py`

测试场景:
1. 创建表格 → 插入行 → 填充数据 → 保存文档
2. 加载文档 → 删除行 → 验证内容 → 保存
3. 创建表格 → 插入列 → 设置格式 → 复制格式 → 保存
4. 复杂场景: 多次插入/删除操作的组合

### 6.3 E2E 测试

位置: `tests/e2e/test_table_rowcol_e2e.py`

测试流程:
1. 通过 MCP 工具创建会话
2. 创建表格并填充数据
3. 执行插入/删除操作
4. 保存文档
5. 使用 python-docx 验证生成的 .docx 文件结构

## 7. 部署与发布

### 7.1 版本规划

- **v2.2.0**: 新增表格行列操作功能
  - 新增 4 个 MCP 工具
  - 新增 FormatPainter 和 RegistryCleaner 核心服务
  - 增强 ElementManipulator 和 PositionResolver

### 7.2 向后兼容性

- 本功能为新增功能，不影响现有 API
- 所有现有工具和测试保持不变
- 新增的 position 字符串格式向后兼容

### 7.3 文档更新

需要更新的文档:
1. `README.md`: 添加 4 个新工具到工具列表
2. `CLAUDE.md`: 更新工具参考和快速参考章节
3. `CHANGELOG.md`: 记录 v2.2.0 的变更

### 7.4 发布检查清单

- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] E2E 测试通过
- [ ] 代码覆盖率 > 90%
- [ ] 文档更新完成
- [ ] CHANGELOG 更新
- [ ] 版本号更新（pyproject.toml）

## 8. 风险与缓解

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| python-docx 不支持列删除 | 高 | 中 | 使用 lxml 直接操作 XML |
| 格式复制不完整 | 中 | 中 | 详细测试各种格式属性，逐步完善 |
| element_id 映射清理遗漏 | 中 | 低 | 编写专门的测试用例验证清理逻辑 |
| 合并单元格场景 | 高 | 低 | 本期不支持，文档明确说明 |
| 性能问题（大表格） | 低 | 低 | 优化 XML 操作，避免不必要的遍历 |

## 9. 未来扩展

### 9.1 短期扩展（v2.3）

- 支持批量删除多行/列
- 支持行/列的移动操作
- 支持按 element_id 引用行/列（需要为行/列分配 ID）

### 9.2 长期扩展（v3.0）

- 支持合并单元格的行/列操作
- 支持嵌套表格的行/列操作
- 支持撤销/重做功能
- 支持表格的复杂变换（转置、排序等）

---

**设计版本**: v1
**最后更新**: 2026-01-23
**设计者**: Claude Sonnet 4.5
