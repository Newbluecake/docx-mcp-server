# 任务规划: Cursor Context Awareness

## 任务清单

| ID | 任务名称 | 描述 | 依赖 | 复杂度 |
|----|----------|------|------|--------|
| T-001 | 核心上下文逻辑实现 | 在 `Session` 类中实现 `get_cursor_context` 及相关辅助方法，建立 ID 反向映射缓存 | - | High |
| T-002 | 核心逻辑单元测试 | 编写针对 `get_cursor_context` 的单元测试，覆盖边界情况（文档首尾、空文档、嵌套结构） | T-001 | Medium |
| T-003 | 更新段落与文本工具 | 修改 `paragraph_tools.py` 和 `run_tools.py`，在操作成功后附加上下文 | T-001 | Low |
| T-004 | 更新表格工具 | 修改 `table_tools.py`，支持表格操作的上下文返回（特别注意嵌套环境） | T-001 | Medium |
| T-005 | 更新高级与光标工具 | 修改 `advanced_tools.py` 和 `cursor_tools.py`，集成上下文感知 | T-001 | Low |
| T-006 | E2E 验证测试 | 创建端到端测试，验证完整工作流中的上下文连续性和准确性 | T-003, T-004 | Medium |

## 详细实施计划

### T-001: 核心上下文逻辑实现
- **目标**: `Session` 类具备生成当前光标位置上下文描述的能力。
- **修改文件**: `src/docx_mcp_server/core/session.py`
- **关键点**:
    - 在 `__post_init__` 或 `__init__` 初始化 `_element_id_cache`。
    - 修改 `register_object` 填充缓存。
    - 实现 `_get_siblings(parent)` 处理不同类型的容器（Body, Cell）。
    - 实现 `_format_element_summary(element)` 处理截断和类型识别。
    - 实现 `get_cursor_context(num_before, num_after)` 主逻辑。

### T-002: 核心逻辑单元测试
- **目标**: 确保核心逻辑稳健，不破坏现有功能。
- **新增文件**: `tests/unit/core/test_context_awareness.py`
- **测试用例**:
    - `test_context_empty_doc`: 空文档上下文。
    - `test_context_start_end`: 文档开头和结尾。
    - `test_context_middle`: 文档中间，前后都有元素。
    - `test_context_nested_cell`: 表格单元格内的上下文。
    - `test_context_truncation`: 长文本截断。

### T-003: 更新段落与文本工具
- **目标**: 常用文本操作工具返回有用上下文。
- **修改文件**:
    - `src/docx_mcp_server/tools/paragraph_tools.py` (`add_paragraph`, `add_heading`, `update_paragraph_text`, `delete`, `add_page_break`)
    - `src/docx_mcp_server/tools/run_tools.py` (`add_run`, `update_run_text`)
- **实施模式**:
    ```python
    # 操作完成后
    context = session.get_cursor_context()
    return f"{original_msg}\n\n{context}"
    ```

### T-004: 更新表格工具
- **目标**: 表格操作通常较复杂，上下文能帮助定位。
- **修改文件**: `src/docx_mcp_server/tools/table_tools.py`
- **涉及工具**: `add_table`, `add_paragraph_to_cell`, `add_row`, `add_col`, `copy_table`。
- **注意**: 确保在单元格内操作时显示单元格内的上下文，而非表格外。

### T-005: 更新高级与光标工具
- **目标**: 覆盖剩余修改内容的工具。
- **修改文件**:
    - `src/docx_mcp_server/tools/advanced_tools.py` (`replace_text`, `insert_image`)
    - `src/docx_mcp_server/tools/cursor_tools.py` (`insert_paragraph_at_cursor`, `insert_table_at_cursor`)

### T-006: E2E 验证测试
- **目标**: 模拟用户真实使用路径。
- **新增文件**: `tests/e2e/test_context_workflow.py`
- **场景**: 创建文档 -> 添加标题 -> 添加段落 -> 插入表格 -> 在表格中添加内容 -> 检查每一步的返回消息中是否包含预期的上下文信息。
