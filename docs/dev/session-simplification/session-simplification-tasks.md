---
feature: session-simplification
complexity: complex
version: 1
generated_at: 2026-01-27T11:00:00+08:00
---

# 任务拆分文档: Session 简化 - 移除 session_id 参数

> **功能标识**: session-simplification
> **复杂度**: complex
> **版本**: 1.0
> **生成时间**: 2026-01-27

## 任务概览

| 统计项 | 数量 |
|--------|------|
| 总任务数 | 12 |
| P0 任务 | 8 |
| P1 任务 | 3 |
| P2 任务 | 1 |
| 并行组 | 3 |
| 预计工时 | 16-20 小时 |

---

## 任务依赖关系

```
T-001 (辅助函数)
  ↓
T-002 (FileController) ─┬─→ T-003 (session_tools) ─┬─→ T-007 (paragraph_tools)
                        │                          ├─→ T-008 (run_tools)
                        │                          ├─→ T-009 (table_tools)
                        │                          ├─→ T-010 (其他工具)
                        │                          └─→ T-011 (composite_tools)
                        │
                        └─→ T-004 (单元测试辅助) ─→ T-005 (单元测试更新)
                                                  └─→ T-006 (E2E 测试)

T-012 (文档更新) - 独立任务，可并行
```

---

## 并行分组

### Group 1: 基础设施 (串行)
- T-001: 创建辅助函数模块
- T-002: 修改 FileController
- T-003: 修改 session_tools
- T-004: 创建测试辅助函数

### Group 2: 工具模块更新 (并行)
- T-007: 更新 paragraph_tools
- T-008: 更新 run_tools
- T-009: 更新 table_tools
- T-010: 更新其他工具模块
- T-011: 更新 composite_tools

### Group 3: 测试与文档 (并行)
- T-005: 更新单元测试
- T-006: 更新 E2E 测试
- T-012: 更新文档

---

## 任务详情

### T-001: 创建会话辅助函数模块

**优先级**: P0
**复杂度**: Simple
**预计工时**: 1 小时
**依赖**: 无
**并行组**: Group 1

**描述**:
创建 `src/docx_mcp_server/utils/session_helpers.py` 模块，提供 `get_active_session()` 辅助函数，用于从 global_state 获取活跃会话。

**实施步骤**:
1. 创建文件 `src/docx_mcp_server/utils/session_helpers.py`
2. 实现 `get_active_session()` 函数
3. 添加完整的 docstring 和类型注解
4. 编写单元测试 `tests/unit/utils/test_session_helpers.py`

**验收标准**:
- [ ] `get_active_session()` 函数正确返回 (session, None) 或 (None, error_response)
- [ ] 当 `global_state.active_session_id` 为 None 时，返回 NoActiveSession 错误
- [ ] 当 session 不存在时，返回 SessionNotFound 错误
- [ ] 单元测试覆盖率 100%

**代码示例**:
```python
# src/docx_mcp_server/utils/session_helpers.py

def get_active_session():
    """Get the active session from global state.

    Returns:
        tuple: (session, error_response)
            - If successful: (Session object, None)
            - If failed: (None, error response string)
    """
    from docx_mcp_server.server import session_manager
    from docx_mcp_server.core.global_state import global_state
    from docx_mcp_server.core.response import create_error_response

    session_id = global_state.active_session_id
    if not session_id:
        return None, create_error_response(
            message="No active session. Please switch to a file first.",
            error_type="NoActiveSession"
        )

    session = session_manager.get_session(session_id)
    if not session:
        return None, create_error_response(
            message=f"Active session {session_id} not found or expired",
            error_type="SessionNotFound"
        )

    return session, None
```

---

### T-002: 修改 FileController.switch_file 自动创建会话

**优先级**: P0
**复杂度**: Standard
**预计工时**: 1.5 小时
**依赖**: 无
**并行组**: Group 1

**描述**:
修改 `src/docx_mcp_server/api/file_controller.py` 的 `switch_file` 方法，在切换文件后自动创建会话并存储到 `global_state.active_session_id`。

**实施步骤**:
1. 在 `switch_file` 方法的步骤 7 之后，添加自动创建会话的逻辑
2. 调用 `session_manager.create_session(file_path)`
3. 将返回的 session_id 存储到 `global_state.active_session_id`
4. 更新返回值，包含 `sessionId` 字段
5. 更新 docstring 说明新行为
6. 编写单元测试验证自动创建会话

**验收标准**:
- [ ] `switch_file` 成功后，`global_state.active_session_id` 不为 None
- [ ] 返回值包含 `sessionId` 字段
- [ ] 旧会话被正确关闭
- [ ] 单元测试验证自动创建会话
- [ ] 单元测试验证返回值包含 sessionId

**代码变更**:
```python
# src/docx_mcp_server/api/file_controller.py

@staticmethod
def switch_file(file_path: str, force: bool = False) -> Dict[str, Any]:
    """Switch to a new active file and auto-create session.

    ... (现有 docstring) ...

    Returns:
        dict: Status dictionary with currentFile and sessionId keys
    """
    # ... 现有逻辑 (步骤 1-7) ...

    # 8. ⭐ 新增: 自动创建会话
    session_id = session_manager.create_session(
        file_path=file_path,
        auto_save=False
    )
    global_state.active_session_id = session_id

    logger.info(f"File switched and session created: {file_path} -> {session_id}")
    return {
        "currentFile": file_path,
        "sessionId": session_id  # ⭐ 新增字段
    }
```

---

### T-003: 修改 session_tools 模块

**优先级**: P0
**复杂度**: Standard
**预计工时**: 2 小时
**依赖**: T-001, T-002
**并行组**: Group 1

**描述**:
修改 `src/docx_mcp_server/tools/session_tools.py`，移除 `docx_create` 工具，新增 `docx_get_current_session` 和 `docx_switch_session` 工具，更新 `docx_close`、`docx_save`、`docx_get_context` 工具移除 session_id 参数。

**实施步骤**:
1. 删除 `docx_create` 函数
2. 在 `register_tools` 中移除 `docx_create` 的注册
3. 实现 `docx_get_current_session()` 函数
4. 实现 `docx_switch_session(session_id)` 函数 (P2)
5. 更新 `docx_close()` - 移除 session_id 参数，从 global_state 获取
6. 更新 `docx_save()` - 移除 session_id 参数，从 global_state 获取
7. 更新 `docx_get_context()` - 移除 session_id 参数，从 global_state 获取
8. 更新所有 docstring 和示例代码
9. 编写单元测试

**验收标准**:
- [ ] `docx_create` 工具已移除，MCP 工具列表中不存在
- [ ] `docx_get_current_session()` 正确返回当前会话信息
- [ ] `docx_switch_session()` 正确切换会话 (P2)
- [ ] `docx_close()` 无需 session_id 参数，正确关闭活跃会话
- [ ] `docx_save()` 无需 session_id 参数，正确保存活跃会话
- [ ] `docx_get_context()` 无需 session_id 参数，正确返回活跃会话上下文
- [ ] 所有工具在无活跃会话时返回 NoActiveSession 错误
- [ ] 单元测试覆盖所有新增和修改的函数

**代码变更**:
```python
# src/docx_mcp_server/tools/session_tools.py

# ❌ 删除 docx_create 函数

def docx_get_current_session() -> str:
    """Get the current active session information."""
    # ... (见设计文档) ...

def docx_switch_session(session_id: str) -> str:
    """Switch to a different active session."""
    # ... (见设计文档) ...

def docx_close() -> str:  # ⭐ 移除 session_id 参数
    """Close the active session."""
    from docx_mcp_server.utils.session_helpers import get_active_session

    session, error = get_active_session()
    if error:
        return error

    # ... 现有逻辑 ...

def docx_save(file_path: str, backup: bool = False, ...) -> str:  # ⭐ 移除 session_id 参数
    """Save the document to disk."""
    from docx_mcp_server.utils.session_helpers import get_active_session

    session, error = get_active_session()
    if error:
        return error

    # ... 现有逻辑 ...

def docx_get_context() -> str:  # ⭐ 移除 session_id 参数
    """Get the current context state of the session."""
    from docx_mcp_server.utils.session_helpers import get_active_session

    session, error = get_active_session()
    if error:
        return error

    # ... 现有逻辑 ...

def register_tools(mcp: FastMCP):
    # ❌ 移除 docx_create 注册
    mcp.tool()(docx_close)
    mcp.tool()(docx_save)
    mcp.tool()(docx_get_context)
    mcp.tool()(docx_list_sessions)
    mcp.tool()(docx_cleanup_sessions)
    mcp.tool()(docx_get_current_session)  # ⭐ 新增
    mcp.tool()(docx_switch_session)  # ⭐ 新增 (P2)
```

---

### T-004: 创建测试辅助函数

**优先级**: P0
**复杂度**: Simple
**预计工时**: 1 小时
**依赖**: T-001
**并行组**: Group 1

**描述**:
创建 `tests/helpers/session_helpers.py` 模块，提供 `setup_active_session()` 和 `teardown_active_session()` 辅助函数，用于测试中设置和清理全局活跃会话。

**实施步骤**:
1. 创建文件 `tests/helpers/session_helpers.py`
2. 实现 `setup_active_session(file_path=None)` 函数
3. 实现 `teardown_active_session()` 函数
4. 添加完整的 docstring

**验收标准**:
- [ ] `setup_active_session()` 正确创建会话并设置到 global_state
- [ ] `teardown_active_session()` 正确关闭会话并清理 global_state
- [ ] 函数可以在测试中重复调用

**代码示例**:
```python
# tests/helpers/session_helpers.py

def setup_active_session(file_path: Optional[str] = None):
    """Setup a global active session for testing.

    Args:
        file_path: Optional file path to load

    Returns:
        str: Created session_id
    """
    from docx_mcp_server.server import session_manager
    from docx_mcp_server.core.global_state import global_state

    session_id = session_manager.create_session(file_path)
    global_state.active_session_id = session_id
    return session_id

def teardown_active_session():
    """Teardown the global active session."""
    from docx_mcp_server.server import session_manager
    from docx_mcp_server.core.global_state import global_state

    if global_state.active_session_id:
        session_manager.close_session(global_state.active_session_id)
    global_state.clear()
```

---

### T-005: 更新单元测试

**优先级**: P0
**复杂度**: Complex
**预计工时**: 4 小时
**依赖**: T-003, T-004
**并行组**: Group 3

**描述**:
更新所有单元测试，移除 `session_id` 参数传递，使用 `setup_active_session()` 和 `teardown_active_session()` 辅助函数。

**实施步骤**:
1. 识别所有需要更新的测试文件 (~60 个)
2. 编写脚本批量更新测试代码
3. 在每个测试的 setup 中调用 `setup_active_session()`
4. 在每个测试的 teardown 中调用 `teardown_active_session()`
5. 移除所有工具调用中的 `session_id` 参数
6. 运行测试验证

**验收标准**:
- [ ] 所有单元测试通过
- [ ] 测试代码中不再传递 `session_id` 参数
- [ ] 每个测试正确设置和清理全局会话
- [ ] 新增测试覆盖 NoActiveSession 错误场景

**测试更新模式**:
```python
# 变更前
def test_insert_paragraph():
    session_id = docx_create()
    result = docx_insert_paragraph(session_id, "Text", position="end:document_body")
    assert "para_" in result
    docx_close(session_id)

# 变更后
def test_insert_paragraph():
    setup_active_session()
    result = docx_insert_paragraph("Text", position="end:document_body")
    assert "para_" in result
    teardown_active_session()
```

---

### T-006: 更新 E2E 测试

**优先级**: P1
**复杂度**: Standard
**预计工时**: 2 小时
**依赖**: T-003, T-004
**并行组**: Group 3

**描述**:
更新 E2E 测试，验证完整的工作流（Launcher 切换文件 → 调用工具 → 保存 → 关闭）。

**实施步骤**:
1. 更新现有 E2E 测试，移除 `session_id` 参数
2. 新增测试场景: 未切换文件直接调用工具 → 验证 NoActiveSession 错误
3. 新增测试场景: 完整工作流（switch_file → 工具调用 → save → close）
4. 新增测试场景: 会话切换 (P2)

**验收标准**:
- [ ] 所有 E2E 测试通过
- [ ] 新增测试覆盖 NoActiveSession 错误场景
- [ ] 新增测试覆盖完整工作流
- [ ] 新增测试覆盖会话切换 (P2)

---

### T-007: 更新 paragraph_tools 模块

**优先级**: P0
**复杂度**: Standard
**预计工时**: 1.5 小时
**依赖**: T-001, T-003
**并行组**: Group 2

**描述**:
更新 `src/docx_mcp_server/tools/paragraph_tools.py` 中的所有工具，移除 `session_id` 参数，使用 `get_active_session()` 辅助函数。

**涉及的工具** (6 个):
- `docx_insert_paragraph`
- `docx_insert_heading`
- `docx_update_paragraph_text`
- `docx_copy_paragraph`
- `docx_delete`
- `docx_insert_page_break`

**实施步骤**:
1. 对每个工具函数:
   - 移除第一个参数 `session_id: str`
   - 在函数开头调用 `get_active_session()`
   - 更新 docstring 中的参数说明
   - 更新 docstring 中的示例代码
2. 运行单元测试验证

**验收标准**:
- [ ] 所有工具函数签名已更新（移除 session_id 参数）
- [ ] 所有工具函数使用 `get_active_session()` 获取会话
- [ ] 所有 docstring 已更新
- [ ] 单元测试通过

**代码变更模式**:
```python
# 变更前
def docx_insert_paragraph(session_id: str, text: str, position: str, style: str = None) -> str:
    from docx_mcp_server.server import session_manager

    session = session_manager.get_session(session_id)
    if not session:
        return create_error_response(...)

    # ... 操作逻辑 ...

# 变更后
def docx_insert_paragraph(text: str, position: str, style: str = None) -> str:
    from docx_mcp_server.utils.session_helpers import get_active_session

    session, error = get_active_session()
    if error:
        return error

    # ... 操作逻辑 (无变更) ...
```

---

### T-008: 更新 run_tools 模块

**优先级**: P0
**复杂度**: Simple
**预计工时**: 1 小时
**依赖**: T-001, T-003
**并行组**: Group 2

**描述**:
更新 `src/docx_mcp_server/tools/run_tools.py` 中的所有工具，移除 `session_id` 参数。

**涉及的工具** (3 个):
- `docx_insert_run`
- `docx_update_run_text`
- `docx_set_font`

**实施步骤**:
同 T-007

**验收标准**:
同 T-007

---

### T-009: 更新 table_tools 模块

**优先级**: P0
**复杂度**: Standard
**预计工时**: 2 小时
**依赖**: T-001, T-003
**并行组**: Group 2

**描述**:
更新 `src/docx_mcp_server/tools/table_tools.py` 和 `table_rowcol_tools.py` 中的所有工具，移除 `session_id` 参数。

**涉及的工具** (13 个):
- `docx_insert_table`
- `docx_get_table`
- `docx_find_table`
- `docx_get_cell`
- `docx_insert_paragraph_to_cell`
- `docx_insert_table_row`
- `docx_insert_table_col`
- `docx_insert_row_at`
- `docx_insert_col_at`
- `docx_delete_row`
- `docx_delete_col`
- `docx_fill_table`
- `docx_copy_table`

**实施步骤**:
同 T-007

**验收标准**:
同 T-007

---

### T-010: 更新其他工具模块

**优先级**: P0
**复杂度**: Standard
**预计工时**: 2 小时
**依赖**: T-001, T-003
**并行组**: Group 2

**描述**:
更新以下工具模块，移除 `session_id` 参数:
- `format_tools.py` (6 个工具)
- `advanced_tools.py` (3 个工具)
- `cursor_tools.py` (2 个工具)
- `copy_tools.py` (2 个工具)
- `content_tools.py` (3 个工具)

**涉及的工具** (16 个):
- Format: `docx_set_alignment`, `docx_set_properties`, `docx_format_copy`, `docx_set_margins`, `docx_extract_format_template`, `docx_apply_format_template`
- Advanced: `docx_replace_text`, `docx_batch_replace_text`, `docx_insert_image`
- Cursor: `docx_cursor_get`, `docx_cursor_move`
- Copy: `docx_get_element_source`, `docx_copy_elements_range`
- Content: `docx_read_content`, `docx_find_paragraphs`, `docx_extract_template_structure`

**实施步骤**:
同 T-007

**验收标准**:
同 T-007

---

### T-011: 更新 composite_tools 模块

**优先级**: P1
**复杂度**: Standard
**预计工时**: 1.5 小时
**依赖**: T-001, T-003
**并行组**: Group 2

**描述**:
更新 `src/docx_mcp_server/tools/composite_tools.py` 中的所有复合工具，移除 `session_id` 参数。

**涉及的工具** (5 个):
- `docx_insert_formatted_paragraph`
- `docx_quick_edit`
- `docx_get_structure_summary`
- `docx_smart_fill_table`
- `docx_format_range`

**实施步骤**:
同 T-007

**验收标准**:
同 T-007

---

### T-012: 更新文档

**优先级**: P1
**复杂度**: Standard
**预计工时**: 2 小时
**依赖**: 无 (可并行)
**并行组**: Group 3

**描述**:
更新所有文档，移除 `docx_create` 工具说明，新增 `docx_get_current_session` 工具说明，更新所有示例代码移除 `session_id` 参数。

**涉及的文档**:
- `README.md`
- `CLAUDE.md`
- `CHANGELOG.md`
- API 文档 (如有)

**实施步骤**:
1. 更新 `README.md`:
   - 移除 `docx_create` 工具说明
   - 新增 `docx_get_current_session` 工具说明
   - 更新所有示例代码
   - 更新工具列表统计
2. 更新 `CLAUDE.md`:
   - 更新"快速参考"章节
   - 更新所有示例代码
   - 新增迁移指南
3. 更新 `CHANGELOG.md`:
   - 添加 v4.0.0 变更日志
   - 说明 Breaking Change
   - 提供迁移指南链接

**验收标准**:
- [ ] `README.md` 中不再提及 `docx_create` 工具
- [ ] `README.md` 中新增 `docx_get_current_session` 工具说明
- [ ] 所有示例代码已更新（移除 session_id 参数）
- [ ] `CLAUDE.md` 中的快速参考已更新
- [ ] `CHANGELOG.md` 中添加了 v4.0.0 变更日志
- [ ] 文档中提供了清晰的迁移指南

**文档更新示例**:
```markdown
# README.md

## Quick Start (v4.0)

```python
# 1. Use Launcher to select file (or --file parameter)
# 2. Call tools directly (no session_id needed)
para_id = docx_insert_paragraph("Hello World", position="end:document_body")
docx_save("./output.docx")
```

## Migration from v3.x

**Old (v3.x)**:
```python
session_id = docx_create(file_path="./template.docx")
para_id = docx_insert_paragraph(session_id, "Text", position="end:document_body")
docx_save(session_id, "./output.docx")
docx_close(session_id)
```

**New (v4.0)**:
```python
# 1. Use Launcher to switch file
# 2. Call tools without session_id
para_id = docx_insert_paragraph("Text", position="end:document_body")
docx_save("./output.docx")
```
```

---

## 任务执行顺序建议

### Phase 1: 基础设施 (串行，2-3 天)
1. T-001: 创建辅助函数模块 (1h)
2. T-002: 修改 FileController (1.5h)
3. T-003: 修改 session_tools (2h)
4. T-004: 创建测试辅助函数 (1h)

### Phase 2: 工具模块更新 (并行，2-3 天)
并行执行:
- T-007: 更新 paragraph_tools (1.5h)
- T-008: 更新 run_tools (1h)
- T-009: 更新 table_tools (2h)
- T-010: 更新其他工具模块 (2h)
- T-011: 更新 composite_tools (1.5h)

### Phase 3: 测试与文档 (并行，1-2 天)
并行执行:
- T-005: 更新单元测试 (4h)
- T-006: 更新 E2E 测试 (2h)
- T-012: 更新文档 (2h)

**总预计工时**: 16-20 小时 (2-3 个工作日)

---

## 风险与注意事项

| 任务 | 风险 | 缓解措施 |
|------|------|----------|
| T-005 | 大量测试需要更新，容易遗漏 | 编写脚本批量更新，运行完整测试套件 |
| T-007-T-011 | 工具模块更新容易出错 | 使用统一的代码变更模式，逐个验证 |
| T-012 | 文档更新容易遗漏示例代码 | 使用 grep 搜索所有 `session_id` 引用 |

---

## 验收清单

### 功能验收
- [ ] F-001: switch_file 自动创建会话
- [ ] F-002: 所有工具无需 session_id 参数
- [ ] F-003: docx_create 已移除
- [ ] F-004: docx_get_current_session 正常工作
- [ ] F-005: 无会话时返回 NoActiveSession 错误

### 测试验收
- [ ] 所有单元测试通过 (100%)
- [ ] 所有 E2E 测试通过 (100%)
- [ ] 新增测试覆盖 NoActiveSession 场景
- [ ] 新增测试覆盖完整工作流

### 文档验收
- [ ] README.md 已更新
- [ ] CLAUDE.md 已更新
- [ ] CHANGELOG.md 已更新
- [ ] 所有示例代码已更新

---

**任务拆分完成时间**: 2026-01-27
**拆分者**: AI Architect
**审核状态**: 待审核
