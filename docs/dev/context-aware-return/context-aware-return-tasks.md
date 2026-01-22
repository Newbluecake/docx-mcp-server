# 任务拆分: Context Aware Return

## 核心任务

### T-001: 实现 ResponseFormatter 基础类
- **文件**: `src/docx_mcp_server/core/response.py`
- **内容**: 定义 `ToolResponse` 数据类和 `create_response` 辅助函数。
- **验收**: 单元测试验证 JSON 序列化正确性。

### T-002: 重构 Paragraph Tools
- **文件**: `src/docx_mcp_server/tools/paragraph_tools.py`
- **范围**: `add_paragraph`, `add_heading`, `update_paragraph_text`, `copy_paragraph`, `delete`.
- **改动**: 使用 `ResponseFormatter` 构造返回值，包含 ID 和 Context。

### T-003: 重构 Table Tools
- **文件**: `src/docx_mcp_server/tools/table_tools.py`
- **范围**: `add_table`, `add_row`, `add_col`, `fill_table`, `copy_table`.
- **改动**: 确保返回新创建的对象 ID（如新行/列时可能需要返回相关信息）及 Context。

### T-004: 重构 Run & Format Tools
- **文件**: `src/docx_mcp_server/tools/run_tools.py`, `src/docx_mcp_server/tools/format_tools.py`
- **范围**: `add_run`, `update_run_text`, `set_font`, `set_alignment`, etc.
- **改动**: 统一返回 JSON 格式。

### T-005: 重构 Cursor & Advanced Tools
- **文件**: `src/docx_mcp_server/tools/cursor_tools.py`, `src/docx_mcp_server/tools/advanced_tools.py`
- **范围**: `cursor_move`, `insert_*`, `replace_text`.
- **改动**: 标准化返回结构。

### T-006: 更新项目文档
- **文件**: `CLAUDE.md`
- **内容**: 更新“快速参考”和工具说明，指出返回值已变更为 JSON 格式，并提供解析示例。

## 并行分组
- Group 1: T-001 (基础)
- Group 2: T-002, T-003, T-004, T-005 (工具重构，可并行)
- Group 3: T-006 (文档)
