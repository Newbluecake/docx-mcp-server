# 任务拆分文档: 表格行列操作增强

> **功能标识**: table-row-col-operations
> **复杂度**: standard
> **任务版本**: v1
> **拆分日期**: 2026-01-23

## 任务概览

| 统计项 | 数量 |
|--------|------|
| 总任务数 | 8 |
| P0 任务 | 6 |
| P1 任务 | 2 |
| 并行组数 | 3 |
| 预计工时 | 12-16 小时 |

## 任务依赖关系

```
T-001 (Core Services)
  ↓
├─ T-002 (Insert Row Tool) ──┐
├─ T-003 (Insert Col Tool) ──┤ (并行组 1)
├─ T-004 (Delete Row Tool) ──┤
└─ T-005 (Delete Col Tool) ──┘
  ↓
├─ T-006 (Unit Tests) ────────┐ (并行组 2)
└─ T-007 (Integration Tests) ─┘
  ↓
T-008 (Documentation)
```

---

## 任务清单

### T-001: 核心服务实现

**优先级**: P0
**预计工时**: 4-5 小时
**依赖**: 无
**并行组**: 独立

#### 描述
实现底层核心服务，包括 ElementManipulator、FormatPainter 和 RegistryCleaner。

#### 验收标准
- [ ] `ElementManipulator` 类实现以下方法:
  - `insert_row_at(table, index, copy_format_from=None)` - 在指定索引插入行
  - `insert_col_at(table, index, copy_format_from=None)` - 在指定索引插入列
  - `delete_row(table, index)` - 删除指定行
  - `delete_col(table, index)` - 删除指定列
- [ ] `FormatPainter` 类实现以下方法:
  - `copy_row_format(source_row, target_row)` - 复制行格式
  - `copy_col_format(table, source_col_index, target_col_index)` - 复制列格式
  - `copy_cell_format(source_cell, target_cell)` - 复制单元格格式
- [ ] `RegistryCleaner` 类实现以下方法:
  - `find_invalidated_ids(session, table, row_index=None, col_index=None)` - 查找失效 ID
  - `invalidate_ids(session, ids)` - 清理失效 ID
- [ ] 所有方法包含完整的 docstring
- [ ] 边界条件检查（最后一行/列保护、索引越界）
- [ ] 错误处理（返回明确的错误信息）

#### 实现要点
1. **ElementManipulator.insert_row_at**:
   - 使用 `table._tbl.insert(index, new_tr)` 插入行
   - 如果 `copy_format_from` 不为 None，调用 FormatPainter 复制格式
   - 返回新插入的 _Row 对象

2. **ElementManipulator.insert_col_at**:
   - 遍历所有行，在每行的指定位置插入新单元格
   - 使用 lxml 操作 XML: `row._tr.insert(index, new_tc)`
   - 如果 `copy_format_from` 不为 None，调用 FormatPainter 复制格式

3. **ElementManipulator.delete_row**:
   - 检查是否为最后一行（len(table.rows) == 1），如果是则抛出 ValidationError
   - 使用 `table._tbl.remove(row._tr)` 删除行

4. **ElementManipulator.delete_col**:
   - 检查是否为最后一列（len(table.columns) == 1），如果是则抛出 ValidationError
   - 遍历所有行，删除指定索引的单元格: `row._tr.remove(row._tr[col_index])`

5. **FormatPainter.copy_cell_format**:
   - 复制段落格式: alignment, line_spacing
   - 复制 Run 格式: font.name, font.size, font.bold, font.italic, font.color
   - 复制单元格背景色: `_tc.get_or_add_tcPr().shd_val`
   - 复制单元格边框: `_tc.get_or_add_tcPr().tcBorders`

6. **RegistryCleaner.find_invalidated_ids**:
   - 遍历 `session.object_registry`
   - 对于每个 `cell_*` ID，检查其是否属于被删除的行/列
   - 返回失效 ID 列表

#### 测试要求
- 为每个方法编写单元测试
- 测试边界条件（最后一行/列、索引越界）
- 测试格式复制（字体、颜色、背景）

#### 文件位置
- `src/docx_mcp_server/core/element_manipulator.py` (增强)
- `src/docx_mcp_server/core/format_painter.py` (新建)
- `src/docx_mcp_server/core/registry_cleaner.py` (新建)

---

### T-002: 实现 docx_insert_row_at 工具

**优先级**: P0
**预计工时**: 1.5-2 小时
**依赖**: T-001
**并行组**: 1

#### 描述
实现 MCP 工具 `docx_insert_row_at`，支持在表格的指定位置插入新行。

#### 验收标准
- [ ] 工具函数签名正确:
  ```python
  def docx_insert_row_at(
      session_id: str,
      table_id: str,
      position: str,
      row_index: int = None,
      copy_format: bool = False
  ) -> str
  ```
- [ ] 支持 position 字符串格式:
  - `after:N` - 在第 N 行之后插入
  - `before:N` - 在第 N 行之前插入
  - `start:table_id` - 在表格开头插入
  - `end:table_id` - 在表格末尾插入
- [ ] 支持 `row_index` 参数（与 position 二选一）
- [ ] 支持 `copy_format` 参数（复制相邻行格式）
- [ ] 返回标准化 JSON 响应，包含:
  - `table_id`
  - `new_row_count`
  - `inserted_at`
  - `copy_format`
  - `cursor` 信息
- [ ] 错误处理:
  - SessionNotFound
  - ElementNotFound
  - ValidationError (position 格式错误)
  - IndexError (索引越界)

#### 实现要点
1. 验证 session_id 和 table_id
2. 解析 position 字符串或使用 row_index
3. 调用 `ElementManipulator.insert_row_at()`
4. 更新 Session 的 cursor 位置
5. 使用 `create_context_aware_response()` 返回响应

#### 测试要求
- 测试所有 position 格式
- 测试 copy_format=True/False
- 测试错误场景（无效 session、无效 table_id、索引越界）

#### 文件位置
- `src/docx_mcp_server/tools/table_rowcol_tools.py` (新建)

---

### T-003: 实现 docx_insert_col_at 工具

**优先级**: P0
**预计工时**: 1.5-2 小时
**依赖**: T-001
**并行组**: 1

#### 描述
实现 MCP 工具 `docx_insert_col_at`，支持在表格的指定位置插入新列。

#### 验收标准
- [ ] 工具函数签名正确（类似 docx_insert_row_at）
- [ ] 支持 position 字符串格式（同上）
- [ ] 支持 `col_index` 参数
- [ ] 支持 `copy_format` 参数
- [ ] 返回标准化 JSON 响应
- [ ] 错误处理（同上）

#### 实现要点
1. 验证 session_id 和 table_id
2. 解析 position 字符串或使用 col_index
3. 调用 `ElementManipulator.insert_col_at()`
4. 更新 Session 的 cursor 位置
5. 使用 `create_context_aware_response()` 返回响应

#### 测试要求
- 测试所有 position 格式
- 测试 copy_format=True/False
- 测试错误场景

#### 文件位置
- `src/docx_mcp_server/tools/table_rowcol_tools.py`

---

### T-004: 实现 docx_delete_row 工具

**优先级**: P0
**预计工时**: 1.5-2 小时
**依赖**: T-001
**并行组**: 1

#### 描述
实现 MCP 工具 `docx_delete_row`，支持按索引或 element_id 删除表格行。

#### 验收标准
- [ ] 工具函数签名正确:
  ```python
  def docx_delete_row(
      session_id: str,
      table_id: str,
      row_index: int = None,
      row_id: str = None
  ) -> str
  ```
- [ ] 支持 `row_index` 参数（按索引删除）
- [ ] 支持 `row_id` 参数（按 element_id 删除）
- [ ] 返回标准化 JSON 响应，包含:
  - `table_id`
  - `new_row_count`
  - `deleted_index`
  - `invalidated_ids` (失效的 element_id 列表)
  - `cursor` 信息
- [ ] 错误处理:
  - SessionNotFound
  - ElementNotFound
  - ValidationError (尝试删除最后一行)
  - IndexError (索引越界)

#### 实现要点
1. 验证 session_id 和 table_id
2. 如果提供 row_id，查找对应的行索引
3. 调用 `RegistryCleaner.find_invalidated_ids()` 查找失效 ID
4. 调用 `ElementManipulator.delete_row()`
5. 调用 `RegistryCleaner.invalidate_ids()` 清理失效 ID
6. 更新 Session 的 cursor 位置
7. 使用 `create_context_aware_response()` 返回响应，包含 `invalidated_ids`

#### 测试要求
- 测试按索引删除
- 测试按 element_id 删除
- 测试删除最后一行（应失败）
- 测试索引越界
- 测试 element_id 映射清理

#### 文件位置
- `src/docx_mcp_server/tools/table_rowcol_tools.py`

---

### T-005: 实现 docx_delete_col 工具

**优先级**: P0
**预计工时**: 1.5-2 小时
**依赖**: T-001
**并行组**: 1

#### 描述
实现 MCP 工具 `docx_delete_col`，支持按索引或 element_id 删除表格列。

#### 验收标准
- [ ] 工具函数签名正确（类似 docx_delete_row）
- [ ] 支持 `col_index` 参数
- [ ] 支持 `col_id` 参数
- [ ] 返回标准化 JSON 响应（同上）
- [ ] 错误处理（同上）

#### 实现要点
1. 验证 session_id 和 table_id
2. 如果提供 col_id，查找对应的列索引
3. 调用 `RegistryCleaner.find_invalidated_ids()` 查找失效 ID
4. 调用 `ElementManipulator.delete_col()`
5. 调用 `RegistryCleaner.invalidate_ids()` 清理失效 ID
6. 更新 Session 的 cursor 位置
7. 使用 `create_context_aware_response()` 返回响应

#### 测试要求
- 测试按索引删除
- 测试按 element_id 删除
- 测试删除最后一列（应失败）
- 测试索引越界
- 测试 element_id 映射清理

#### 文件位置
- `src/docx_mcp_server/tools/table_rowcol_tools.py`

---

### T-006: 单元测试

**优先级**: P0
**预计工时**: 2-3 小时
**依赖**: T-002, T-003, T-004, T-005
**并行组**: 2

#### 描述
为所有新增的工具和核心服务编写单元测试。

#### 验收标准
- [ ] 测试覆盖率 > 90%
- [ ] 所有测试通过
- [ ] 测试用例包括:
  - 正常场景（插入、删除）
  - 边界条件（最后一行/列、索引越界）
  - 错误场景（无效 session、无效 table_id）
  - 格式复制（copy_format=True）
  - element_id 映射清理

#### 测试用例清单
1. **test_insert_row_at**:
   - 在中间插入行
   - 在开头插入行
   - 在末尾插入行
   - 插入行并复制格式
   - 索引越界

2. **test_insert_col_at**:
   - 在中间插入列
   - 在开头插入列
   - 在末尾插入列
   - 插入列并复制格式
   - 索引越界

3. **test_delete_row**:
   - 删除中间行
   - 删除第一行
   - 删除最后一行（应失败）
   - 索引越界
   - element_id 映射清理

4. **test_delete_col**:
   - 删除中间列
   - 删除第一列
   - 删除最后一列（应失败）
   - 索引越界
   - element_id 映射清理

5. **test_format_painter**:
   - 复制行格式
   - 复制列格式
   - 复制单元格格式（字体、颜色、背景）

6. **test_registry_cleaner**:
   - 查找失效 ID（删除行）
   - 查找失效 ID（删除列）
   - 清理失效 ID

#### 文件位置
- `tests/unit/test_table_rowcol_tools.py` (新建)
- `tests/unit/test_element_manipulator.py` (增强)
- `tests/unit/test_format_painter.py` (新建)
- `tests/unit/test_registry_cleaner.py` (新建)

---

### T-007: 集成测试

**优先级**: P1
**预计工时**: 1.5-2 小时
**依赖**: T-002, T-003, T-004, T-005
**并行组**: 2

#### 描述
编写集成测试，验证工具在真实场景中的表现。

#### 验收标准
- [ ] 所有集成测试通过
- [ ] 测试场景包括:
  - 创建表格 → 插入行 → 填充数据 → 保存
  - 加载文档 → 删除行 → 验证内容 → 保存
  - 创建表格 → 插入列 → 设置格式 → 复制格式 → 保存
  - 复杂场景: 多次插入/删除操作的组合

#### 测试场景清单
1. **test_insert_and_fill_rows**:
   - 创建 3x3 表格
   - 在第 2 行之后插入新行
   - 填充新行的数据
   - 保存文档
   - 验证文档结构

2. **test_delete_and_verify**:
   - 加载包含表格的文档
   - 删除第 2 行
   - 验证剩余行的内容
   - 保存文档

3. **test_insert_col_with_format**:
   - 创建表格，设置第 1 列为粗体红色
   - 在第 1 列之后插入新列，copy_format=True
   - 验证新列的格式与第 1 列一致
   - 保存文档

4. **test_complex_operations**:
   - 创建 5x5 表格
   - 插入 2 行
   - 删除 1 列
   - 插入 1 列
   - 删除 1 行
   - 验证最终表格为 6x5
   - 保存文档

#### 文件位置
- `tests/integration/test_table_rowcol_integration.py` (新建)

---

### T-008: 文档更新

**优先级**: P1
**预计工时**: 1-1.5 小时
**依赖**: T-006, T-007
**并行组**: 独立

#### 描述
更新项目文档，添加新工具的说明和示例。

#### 验收标准
- [ ] `README.md` 更新:
  - 在 "Table Tools" 章节添加 4 个新工具
  - 包含参数说明和示例
- [ ] `CLAUDE.md` 更新:
  - 在 "完整工具参考" 章节添加新工具
  - 更新 "快速参考" 章节的表格操作示例
- [ ] `CHANGELOG.md` 更新:
  - 记录 v2.2.0 的变更
  - 列出新增的 4 个工具
  - 列出新增的核心服务

#### 文档内容要点
1. **README.md**:
   - 工具名称、参数、返回值
   - 使用示例（插入行、删除列等）
   - 注意事项（最后一行/列保护）

2. **CLAUDE.md**:
   - 工具列表更新（从 47 个增加到 51 个）
   - 快速参考章节添加行列操作示例
   - 更新工具设计原则（如适用）

3. **CHANGELOG.md**:
   ```markdown
   ## [2.2.0] - 2026-01-23
   ### Added
   - 新增 `docx_insert_row_at` 工具，支持在表格指定位置插入行
   - 新增 `docx_insert_col_at` 工具，支持在表格指定位置插入列
   - 新增 `docx_delete_row` 工具，支持按索引或 element_id 删除行
   - 新增 `docx_delete_col` 工具，支持按索引或 element_id 删除列
   - 新增 `FormatPainter` 核心服务，支持行/列格式复制
   - 新增 `RegistryCleaner` 核心服务，自动清理失效的 element_id

   ### Enhanced
   - 增强 `ElementManipulator`，支持行/列的插入和删除
   - 增强 `PositionResolver`，支持表格内的位置解析
   ```

#### 文件位置
- `README.md`
- `CLAUDE.md`
- `CHANGELOG.md`

---

## 并行执行计划

### 并行组 1: 工具实现（T-002 ~ T-005）

这 4 个任务可以并行执行，因为它们都依赖于 T-001，但彼此独立。

**执行策略**:
- 优先实现 T-002 和 T-004（插入行、删除行），因为它们相对简单
- 然后实现 T-003 和 T-005（插入列、删除列），可以复用行操作的逻辑

**预计总耗时**: 2-3 小时（如果串行执行需要 6-8 小时）

### 并行组 2: 测试（T-006 ~ T-007）

这 2 个任务可以并行执行，因为它们都依赖于工具实现，但彼此独立。

**执行策略**:
- 单元测试和集成测试可以同时进行
- 单元测试优先级更高（P0），应优先完成

**预计总耗时**: 2-3 小时（如果串行执行需要 3.5-5 小时）

---

## 风险与缓解

| 任务 | 风险 | 影响 | 缓解措施 |
|------|------|------|----------|
| T-001 | python-docx 不支持列删除 | 高 | 使用 lxml 直接操作 XML |
| T-001 | 格式复制不完整 | 中 | 逐步完善，优先支持常见格式 |
| T-004, T-005 | element_id 映射清理遗漏 | 中 | 编写专门的测试用例验证 |
| T-006 | 测试覆盖率不足 | 中 | 使用 pytest-cov 监控覆盖率 |
| T-007 | 集成测试环境问题 | 低 | 使用临时文件，测试后清理 |

---

## 完成标准

所有任务完成后，需满足以下条件:

1. **功能完整性**:
   - [ ] 4 个 MCP 工具全部实现
   - [ ] 支持所有需求文档中的功能点

2. **质量标准**:
   - [ ] 所有单元测试通过
   - [ ] 所有集成测试通过
   - [ ] 代码覆盖率 > 90%
   - [ ] 无 linting 错误

3. **文档完整性**:
   - [ ] README.md 更新
   - [ ] CLAUDE.md 更新
   - [ ] CHANGELOG.md 更新

4. **验收测试**:
   - [ ] 功能验收清单（requirements.md）中的所有项通过

---

**任务版本**: v1
**最后更新**: 2026-01-23
**拆分者**: Claude Sonnet 4.5
