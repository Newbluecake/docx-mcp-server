# 任务拆分文档: Markdown Response Format

> **功能标识**: markdown-response-format
> **复杂度**: complex
> **任务版本**: v1.0
> **拆分时间**: 2026-01-23

---

## 任务概览

| 统计项 | 数量 |
|--------|------|
| 总任务数 | 12 |
| P0 任务 | 10 |
| P1 任务 | 2 |
| 预估总工时 | 8-10 天 |

---

## 任务列表

### Phase 1: 核心架构（P0）

#### T-001: 创建 visualizer.py 模块

**优先级**: P0
**预估工时**: 4-6 小时
**依赖**: 无

**描述**:
创建新的 `src/docx_mcp_server/core/visualizer.py` 模块，实现 ASCII 可视化的核心逻辑。

**实施步骤**:
1. 创建 `visualizer.py` 文件
2. 实现 `DocumentVisualizer` 类
   - `__init__(session)`
   - `render_paragraph(paragraph, element_id, highlight=False)`
   - `render_table(table, element_id, highlight=False)`
   - `render_context(element_id, context_range=None)`
   - `render_image(image_path, element_id)`
   - `render_cursor()`
3. 实现辅助函数
   - `_extract_text_with_format(paragraph)`
   - `_truncate_text(text, max_length=80)`
   - `_draw_box(content, title, highlight=False)`
4. 实现 `DiffRenderer` 类
   - `render_diff(old_content, new_content, element_id, element_type)`
   - `_compute_line_diff(old_lines, new_lines)`

**验收标准**:
- [ ] `visualizer.py` 文件创建成功
- [ ] `DocumentVisualizer` 类实现完整
- [ ] `DiffRenderer` 类实现完整
- [ ] 所有方法有完整的 docstring
- [ ] 代码通过 pylint 检查

**测试要求**:
- 创建 `tests/unit/test_visualizer.py`
- 测试用例：
  - `test_render_paragraph_basic()`
  - `test_render_paragraph_with_format()`
  - `test_render_paragraph_truncation()`
  - `test_render_table_basic()`
  - `test_render_table_large()`
  - `test_render_context_middle()`
  - `test_render_context_start()`
  - `test_render_context_end()`
  - `test_render_diff_basic()`
  - `test_render_diff_multiline()`

**关联需求**: R-002, R-003, R-004, R-005, R-007

---

#### T-002: 重构 response.py 为 Markdown 格式

**优先级**: P0
**预估工时**: 3-4 小时
**依赖**: T-001

**描述**:
重构 `src/docx_mcp_server/core/response.py`，移除 JSON 格式化函数，实现 Markdown 响应格式化。

**实施步骤**:
1. 移除旧代码
   - 删除 `ToolResponse` dataclass
   - 删除 `CursorInfo` dataclass
   - 删除 `create_success_response()` 函数
   - 删除 `create_context_aware_response()` 函数
   - 删除 `create_change_tracked_response()` 函数
2. 实现新函数
   - `create_markdown_response(session, message, element_id, operation, status, show_context, show_diff, old_content, new_content, **extra_metadata)`
   - `create_error_response(message, error_type)`
3. 集成 `DocumentVisualizer` 和 `DiffRenderer`
4. 实现 Markdown 格式化逻辑

**验收标准**:
- [ ] 旧的 JSON 格式化代码已移除
- [ ] `create_markdown_response()` 实现完整
- [ ] `create_error_response()` 实现完整
- [ ] 返回值符合 Markdown 格式规范
- [ ] 代码通过 pylint 检查

**测试要求**:
- 创建 `tests/unit/test_response_markdown.py`
- 测试用例：
  - `test_create_markdown_response_success()`
  - `test_create_markdown_response_error()`
  - `test_create_markdown_response_with_diff()`
  - `test_create_markdown_response_no_context()`
  - `test_create_markdown_response_with_extra_metadata()`

**关联需求**: R-001, R-008

---

### Phase 2: 工具迁移（P0）

#### T-003: 迁移 Session Tools (4 个工具)

**优先级**: P0
**预估工时**: 2-3 小时
**依赖**: T-002

**描述**:
迁移 `src/docx_mcp_server/tools/session_tools.py` 中的 4 个工具，使用新的 Markdown 响应格式。

**工具列表**:
1. `docx_create()`
2. `docx_save()`
3. `docx_close()`
4. `docx_get_context()`

**实施步骤**:
1. 更新每个工具的返回语句
   - 从 `return create_success_response(...)` 改为 `return create_markdown_response(...)`
2. 添加 `operation` 参数（如 "Create Session", "Save Document"）
3. 根据工具类型决定是否显示上下文（`show_context`）
4. 更新 docstring 中的返回值说明

**验收标准**:
- [ ] 所有 4 个工具已迁移
- [ ] 返回值符合 Markdown 格式
- [ ] Docstring 已更新
- [ ] 代码通过 pylint 检查

**测试要求**:
- 更新 `tests/unit/test_session_tools.py`（如存在）
- 验证 Markdown 输出格式
- 使用正则表达式提取 element_id

**关联需求**: R-001, R-008

---

#### T-004: 迁移 Paragraph Tools (6 个工具)

**优先级**: P0
**预估工时**: 3-4 小时
**依赖**: T-002

**描述**:
迁移 `src/docx_mcp_server/tools/paragraph_tools.py` 中的 6 个工具。

**工具列表**:
1. `docx_insert_paragraph()`
2. `docx_insert_heading()`
3. `docx_update_paragraph_text()` ⭐ 需要 diff
4. `docx_copy_paragraph()`
5. `docx_delete()`
6. `docx_insert_page_break()`

**实施步骤**:
1. 更新每个工具的返回语句
2. 对于 `docx_update_paragraph_text()`，添加 diff 支持：
   - 在更新前捕获 `old_content`
   - 在更新后捕获 `new_content`
   - 调用 `create_markdown_response(..., show_diff=True, old_content=..., new_content=...)`
3. 更新 docstring

**验收标准**:
- [ ] 所有 6 个工具已迁移
- [ ] `docx_update_paragraph_text()` 显示 diff
- [ ] 返回值符合 Markdown 格式
- [ ] Docstring 已更新

**测试要求**:
- 更新相关单元测试
- 验证 diff 输出格式（包含 `-` 和 `+` 前缀）

**关联需求**: R-001, R-003, R-008

---

#### T-005: 迁移 Run Tools (3 个工具)

**优先级**: P0
**预估工时**: 2 小时
**依赖**: T-002

**描述**:
迁移 `src/docx_mcp_server/tools/run_tools.py` 中的 3 个工具。

**工具列表**:
1. `docx_insert_run()`
2. `docx_update_run_text()` ⭐ 需要 diff
3. `docx_set_font()`

**实施步骤**:
1. 更新每个工具的返回语句
2. 对于 `docx_update_run_text()`，添加 diff 支持
3. 更新 docstring

**验收标准**:
- [ ] 所有 3 个工具已迁移
- [ ] `docx_update_run_text()` 显示 diff
- [ ] 返回值符合 Markdown 格式

**测试要求**:
- 更新相关单元测试

**关联需求**: R-001, R-003, R-008

---

#### T-006: 迁移 Table Tools (13 个工具)

**优先级**: P0
**预估工时**: 4-5 小时
**依赖**: T-002

**描述**:
迁移 `src/docx_mcp_server/tools/table_tools.py` 和 `table_rowcol_tools.py` 中的 13 个工具。

**工具列表**:
1. `docx_insert_table()`
2. `docx_get_table()`
3. `docx_find_table()`
4. `docx_get_cell()`
5. `docx_insert_paragraph_to_cell()`
6. `docx_insert_table_row()`
7. `docx_insert_table_col()`
8. `docx_insert_row_at()`
9. `docx_insert_col_at()`
10. `docx_delete_row()`
11. `docx_delete_col()`
12. `docx_fill_table()`
13. `docx_copy_table()`

**实施步骤**:
1. 更新每个工具的返回语句
2. 对于表格创建/修改工具，确保 ASCII 表格正确渲染
3. 更新 docstring

**验收标准**:
- [ ] 所有 13 个工具已迁移
- [ ] 表格工具显示 ASCII 表格
- [ ] 返回值符合 Markdown 格式

**测试要求**:
- 更新相关单元测试
- 验证 ASCII 表格格式

**关联需求**: R-001, R-005, R-008

---

#### T-007: 迁移 Format Tools (6 个工具)

**优先级**: P0
**预估工时**: 2-3 小时
**依赖**: T-002

**描述**:
迁移 `src/docx_mcp_server/tools/format_tools.py` 中的 6 个工具。

**工具列表**:
1. `docx_set_alignment()`
2. `docx_set_properties()`
3. `docx_format_copy()`
4. `docx_set_margins()`
5. `docx_extract_format_template()`
6. `docx_apply_format_template()`

**实施步骤**:
1. 更新每个工具的返回语句
2. 更新 docstring

**验收标准**:
- [ ] 所有 6 个工具已迁移
- [ ] 返回值符合 Markdown 格式

**测试要求**:
- 更新相关单元测试

**关联需求**: R-001, R-008

---

#### T-008: 迁移 Advanced Tools (3 个工具)

**优先级**: P0
**预估工时**: 2-3 小时
**依赖**: T-002

**描述**:
迁移 `src/docx_mcp_server/tools/advanced_tools.py` 中的 3 个工具。

**工具列表**:
1. `docx_replace_text()` ⭐ 需要 diff
2. `docx_batch_replace_text()` ⭐ 需要 diff
3. `docx_insert_image()`

**实施步骤**:
1. 更新每个工具的返回语句
2. 对于替换工具，添加 diff 支持（显示所有替换位置）
3. 对于 `docx_insert_image()`，使用 `[IMG: filename.png]` 标记
4. 更新 docstring

**验收标准**:
- [ ] 所有 3 个工具已迁移
- [ ] 替换工具显示 diff
- [ ] 图片工具显示图片标记
- [ ] 返回值符合 Markdown 格式

**测试要求**:
- 更新相关单元测试
- 验证图片标记格式

**关联需求**: R-001, R-003, R-006, R-008

---

#### T-009: 迁移 Cursor/Copy/Content/Composite/System Tools (16 个工具)

**优先级**: P0
**预估工时**: 4-5 小时
**依赖**: T-002

**描述**:
迁移剩余的 16 个工具：
- Cursor Tools (4 个)
- Copy Tools (2 个)
- Content Tools (4 个)
- Composite Tools (5 个)
- System Tools (1 个)

**工具列表**:
1. `docx_cursor_get()`
2. `docx_cursor_move()`
3. `docx_get_element_source()`
4. `docx_copy_elements_range()`
5. `docx_read_content()`
6. `docx_find_paragraphs()`
7. `docx_list_files()`
8. `docx_extract_template_structure()`
9. `docx_insert_formatted_paragraph()`
10. `docx_quick_edit()` ⭐ 需要 diff
11. `docx_get_structure_summary()`
12. `docx_smart_fill_table()`
13. `docx_format_range()`
14. `docx_server_status()`
15. 其他 History Tools (如有)

**实施步骤**:
1. 更新每个工具的返回语句
2. 对于编辑工具，添加 diff 支持
3. 对于光标工具，使用 `>>> [CURSOR] <<<` 标记
4. 更新 docstring

**验收标准**:
- [ ] 所有 16 个工具已迁移
- [ ] 返回值符合 Markdown 格式

**测试要求**:
- 更新相关单元测试

**关联需求**: R-001, R-003, R-006, R-008

---

### Phase 3: 测试更新（P0）

#### T-010: 更新所有单元测试

**优先级**: P0
**预估工时**: 1 天
**依赖**: T-003, T-004, T-005, T-006, T-007, T-008, T-009

**描述**:
更新所有单元测试，使其适配 Markdown 响应格式。

**实施步骤**:
1. 扫描所有单元测试文件（`tests/unit/`）
2. 识别使用 `json.loads()` 的测试
3. 更新断言逻辑：
   - 从 `data["status"] == "success"` 改为 `"✅ Success" in response`
   - 从 `data["data"]["element_id"]` 改为正则提取 `**Element ID**: (para_\w+)`
4. 编写辅助函数 `extract_element_id(response)` 用于提取 element_id
5. 运行测试，修复失败的用例

**验收标准**:
- [ ] 所有单元测试通过（`pytest tests/unit/`）
- [ ] 无 JSON 解析代码残留
- [ ] 测试覆盖率保持不变

**测试要求**:
- 运行 `pytest tests/unit/ -v`
- 确保所有测试通过

**关联需求**: R-008

---

#### T-011: 更新所有 E2E 和集成测试

**优先级**: P0
**预估工时**: 1 天
**依赖**: T-003, T-004, T-005, T-006, T-007, T-008, T-009

**描述**:
更新所有 E2E 测试和集成测试，使其适配 Markdown 响应格式。

**实施步骤**:
1. 扫描所有 E2E 测试文件（`tests/e2e/`）
2. 扫描所有集成测试文件（`tests/integration/`）
3. 更新断言逻辑（同 T-010）
4. 运行测试，修复失败的用例

**验收标准**:
- [ ] 所有 E2E 测试通过（`pytest tests/e2e/`）
- [ ] 所有集成测试通过（`pytest tests/integration/`）
- [ ] 无 JSON 解析代码残留

**测试要求**:
- 运行 `pytest tests/e2e/ tests/integration/ -v`
- 确保所有测试通过

**关联需求**: R-008

---

### Phase 4: 文档更新（P0）

#### T-012: 更新项目文档

**优先级**: P0
**预估工时**: 4-6 小时
**依赖**: T-010, T-011

**描述**:
更新项目文档，反映 Markdown 响应格式的变更。

**实施步骤**:
1. 更新 `README.md`
   - 修改工具返回值说明（从 JSON 改为 Markdown）
   - 添加 Markdown 格式示例
   - 更新使用示例
2. 更新 `CLAUDE.md`
   - 修改响应格式化层说明
   - 移除 JSON 相关内容
   - 添加 Markdown 格式规范
   - 更新 v2.1 更新日志为 v3.0
3. 创建迁移指南（可选）
   - 说明破坏性变更
   - 提供迁移示例

**验收标准**:
- [ ] `README.md` 已更新
- [ ] `CLAUDE.md` 已更新
- [ ] 文档中无 JSON 格式残留
- [ ] 示例代码正确

**测试要求**:
- 手动验证文档内容
- 确保示例代码可运行

**关联需求**: R-008

---

### Phase 5: 增强功能（P1，可选）

#### T-013: 实现图片位置标记和文档结构树

**优先级**: P1
**预估工时**: 4-6 小时
**依赖**: T-012

**描述**:
实现增强功能，提升可视化体验。

**实施步骤**:
1. 在 `DocumentVisualizer` 中实现 `render_image()`
   - 返回 `[IMG: filename.png, width=100, height=50]`
2. 实现文档结构树渲染（可选）
   - 使用树形结构展示文档层次
   - 示例：
     ```
     Document
     ├── Heading 1 (para_001)
     │   ├── Paragraph (para_002)
     │   └── Table (table_003)
     └── Heading 2 (para_004)
         └── Paragraph (para_005)
     ```
3. 更新相关工具（如 `docx_insert_image()`）

**验收标准**:
- [ ] 图片标记功能实现
- [ ] 文档结构树功能实现（可选）
- [ ] 相关测试通过

**测试要求**:
- 添加测试用例验证图片标记
- 添加测试用例验证结构树（如实现）

**关联需求**: R-006

---

#### T-014: 性能优化和调优

**优先级**: P1
**预估工时**: 4-6 小时
**依赖**: T-012

**描述**:
优化渲染性能，确保满足性能指标。

**实施步骤**:
1. 添加性能测试
   - 测量渲染时间（段落、表格、上下文、diff）
   - 使用 `time.time()` 或 `pytest-benchmark`
2. 识别性能瓶颈
3. 优化关键路径
   - 缓存机制（如需要）
   - 减少不必要的计算
4. 验证性能指标
   - 单个段落渲染 < 5ms
   - 单个表格渲染 < 20ms
   - 上下文渲染 < 50ms
   - 完整响应生成 < 100ms

**验收标准**:
- [ ] 性能测试通过
- [ ] 所有性能指标满足要求
- [ ] 无明显性能退化

**测试要求**:
- 创建 `tests/performance/test_visualizer_performance.py`
- 运行性能测试

**关联需求**: 技术约束 4.3

---

## 任务依赖关系

```
T-001 (visualizer.py)
  ↓
T-002 (response.py)
  ↓
┌─────┬─────┬─────┬─────┬─────┬─────┐
│     │     │     │     │     │     │
T-003 T-004 T-005 T-006 T-007 T-008 T-009
(Session) (Paragraph) (Run) (Table) (Format) (Advanced) (Others)
│     │     │     │     │     │     │
└─────┴─────┴─────┴─────┴─────┴─────┘
  ↓
┌─────────┬─────────┐
│         │         │
T-010     T-011     │
(Unit)    (E2E)     │
│         │         │
└─────────┴─────────┘
  ↓
T-012 (Docs)
  ↓
┌─────────┬─────────┐
│         │         │
T-013     T-014     │
(Enhancement) (Performance)
```

---

## 并行执行建议

### 并行组 1（Phase 1）
- T-001 (独立)

### 并行组 2（Phase 2）
- T-003, T-004, T-005, T-006, T-007, T-008, T-009 可并行执行（如有多人）

### 并行组 3（Phase 3）
- T-010, T-011 可并行执行

### 并行组 4（Phase 5）
- T-013, T-014 可并行执行

---

## 风险与挑战

| 任务 | 风险 | 缓解措施 |
|------|------|----------|
| T-001 | ASCII 绘制逻辑复杂 | 参考 `tabulate` 库，编写详细测试 |
| T-006 | 表格工具数量多 | 优先迁移核心工具，批量处理 |
| T-010 | 测试用例更新工作量大 | 编写脚本批量更新断言 |
| T-011 | E2E 测试可能失败 | 逐个修复，确保覆盖率 |
| T-014 | 性能可能不达标 | 提前测量，识别瓶颈 |

---

## 验收清单

### Phase 1
- [ ] T-001: visualizer.py 模块创建完成
- [ ] T-002: response.py 重构完成

### Phase 2
- [ ] T-003: Session Tools 迁移完成
- [ ] T-004: Paragraph Tools 迁移完成
- [ ] T-005: Run Tools 迁移完成
- [ ] T-006: Table Tools 迁移完成
- [ ] T-007: Format Tools 迁移完成
- [ ] T-008: Advanced Tools 迁移完成
- [ ] T-009: 其他工具迁移完成

### Phase 3
- [ ] T-010: 单元测试更新完成
- [ ] T-011: E2E 和集成测试更新完成

### Phase 4
- [ ] T-012: 项目文档更新完成

### Phase 5（可选）
- [ ] T-013: 增强功能实现完成
- [ ] T-014: 性能优化完成

---

## 总结

**总任务数**: 12 个（10 个 P0，2 个 P1）
**预估总工时**: 8-10 天
**关键路径**: T-001 → T-002 → T-003~T-009 → T-010~T-011 → T-012
**并行机会**: Phase 2 的 7 个任务可并行执行

**建议执行顺序**:
1. 先完成 Phase 1（核心架构）
2. 并行执行 Phase 2（工具迁移）
3. 并行执行 Phase 3（测试更新）
4. 完成 Phase 4（文档更新）
5. 可选执行 Phase 5（增强功能）

---

**文档版本**: v1.0
**最后更新**: 2026-01-23
