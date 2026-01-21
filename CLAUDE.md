# docx-mcp-server - Claude 开发指南

## 项目概述

docx-mcp-server 是一个基于 Model Context Protocol (MCP) 的服务器，为 Claude 提供细粒度的 Microsoft Word 文档操作能力。通过原子化的 API 设计，Claude 可以精确控制文档的每个元素。

### 核心目标

- **状态管理**：维护多个文档编辑会话，支持并发操作
- **原子化操作**：每个操作针对单一元素（段落、文本块、表格）
- **ID 映射系统**：将 python-docx 的内存对象映射为稳定的字符串 ID
- **MCP 协议兼容**：完全符合 MCP 规范，易于集成
- **模块化架构**：工具按领域拆分，便于维护和扩展

## 核心架构

### 1. Session 管理机制

```
Client (Claude)
    ↓ docx_create()
SessionManager
    ↓ 创建 UUID
Session {
    session_id: "abc-123"
    document: Document()
    object_registry: {}
    cursor: Cursor()      # 新增：光标位置管理
    last_accessed: timestamp
}
```

**关键特性**：
- 每个会话独立，互不干扰
- 自动过期机制（默认 1 小时）
- 支持显式关闭 `docx_close()`

**代码位置**：`src/docx_mcp_server/core/session.py`

### 2. 对象 ID 映射系统

这是本项目最关键的设计。python-docx 的对象（Paragraph、Run、Table）是临时的 Python 对象，没有稳定 ID。我们通过 `object_registry` 建立映射：

```python
# 创建段落时
paragraph = document.add_paragraph("Hello")
element_id = session.register_object(paragraph, "para")  # 返回 "para_a1b2c3d4"

# 后续操作时
paragraph = session.get_object("para_a1b2c3d4")
```

**ID 前缀约定**：
- `para_*` - 段落（Paragraph）
- `run_*` - 文本块（Run）
- `table_*` - 表格（Table）
- `cell_*` - 单元格（Cell）

### 3. 原子化操作设计

每个工具只做一件事，避免复杂的组合参数：

```python
# 不好的设计（过于复杂）
docx_add_formatted_paragraph(session_id, text, bold=True, size=14, alignment="center")

# 好的设计（原子化）
para_id = docx_add_paragraph(session_id, "Hello")
run_id = docx_add_run(session_id, text="World", paragraph_id=para_id)
docx_set_font(session_id, run_id, bold=True, size=14)
docx_set_alignment(session_id, para_id, "center")
```

## 开发指南

### 环境配置与运行

本项目**必须**使用 [uv](https://github.com/astral-sh/uv) 进行依赖管理和任务执行。

```bash
# 1. 安装 uv
pip install uv

# 2. 安装项目依赖 (创建虚拟环境)
uv venv
uv pip install -e .[gui]
uv pip install pytest pytest-cov

# 3. 运行服务器
uv run mcp-server-docx

# 4. 运行 GUI 启动器
uv run docx-server-launcher
```

### 添加新工具

1. **在 `src/docx_mcp_server/tools/` 下的相应模块中定义工具**

   （如 `paragraph_tools.py`，或新建模块）

```python
def docx_new_feature(session_id: str, param: str) -> str:
    """
    工具描述（Claude 会读取这个）

    Args:
        session_id: 会话 ID
        param: 参数说明

    Returns:
        str: 返回值说明
    """
    from docx_mcp_server.server import session_manager
    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    # 实现逻辑
    # ...
```

2. **注册工具**

   - 如果是现有模块，无需额外操作（已自动扫描）
   - 如果是新模块，需要在 `src/docx_mcp_server/tools/__init__.py` 中注册：

```python
from . import new_module
new_module.register_tools(mcp)
```

3. **编写单元测试**

在 `tests/unit/` 创建测试文件：

```python
def test_new_feature():
    session_id = docx_create()
    result = docx_new_feature(session_id, "test")
    assert "expected" in result
```

4. **更新文档**

- 在 `README.md` 的工具列表中添加
- 如果是重要功能，在本文件添加说明

### 测试策略

**单元测试**（`tests/unit/`）：
- 测试每个工具的基本功能
- 测试错误处理（无效 session_id、element_id）
- 测试边界条件

**E2E 测试**（`tests/e2e/`）：
- 模拟真实使用场景
- 测试工具组合使用
- 验证生成的 .docx 文件

**运行测试**：
```bash
# 1. 安装测试依赖 (含 GUI 和测试工具)
uv pip install -e ".[gui,dev]"

# 2. 运行测试
# 注意：在无头 Linux 环境需指定 QT_QPA_PLATFORM=offscreen
QT_QPA_PLATFORM=offscreen uv run pytest

# 或运行脚本
./scripts/test.sh
```

### 调试技巧

1. **查看会话状态**

```python
# 临时添加调试工具
@mcp.tool()
def docx_debug_session(session_id: str) -> str:
    session = session_manager.get_session(session_id)
    return f"Objects: {list(session.object_registry.keys())}"
```

2. **日志配置**

修改 `config/dev.yaml` 中的日志级别为 `DEBUG`。错误日志会自动包含堆栈跟踪（Stack Trace）。

## MCP 协议注意事项

### 1. 工具命名规范

- 使用 `docx_` 前缀，避免与其他 MCP 服务器冲突
- 使用动词开头：`add`、`set`、`get`
- 保持简洁：`docx_add_paragraph` 而非 `docx_add_paragraph_to_document`

### 2. 错误处理

始终使用明确的错误消息，利用 `logger.exception` 记录完整堆栈：

```python
try:
    # ...
except Exception as e:
    logger.exception(f"Operation failed: {e}")
    raise ValueError(f"User friendly error message: {e}")
```

### 3. 会话生命周期

```
创建 → 操作 → 保存 → 关闭
  ↓      ↓      ↓      ↓
create  add_*  save   close
        set_*
```

**重要**：提醒 Claude 在完成后调用 `docx_close()` 释放资源。

## 快速参考

### 常用工具组合

**提取模板结构**：
```python
session_id = docx_create(file_path="/path/to/template.docx")
structure_json = docx_extract_template_structure(session_id)
structure = json.loads(structure_json)
docx_close(session_id)
```

**创建格式化文档**：
```python
session_id = docx_create()
para_id = docx_add_paragraph(session_id, "")
run_id = docx_add_run(session_id, para_id, "重要文本")
docx_set_font(session_id, run_id, bold=True, size=16, color_hex="FF0000")
docx_save(session_id, "/path/to/output.docx")
docx_close(session_id)
```

**Cursor 定位系统（高级插入）**：
```python
# 1. 移动光标到指定元素之后
docx_cursor_move(session_id, element_id="para_123", position="after")

# 2. 在光标处插入内容（而非追加到末尾）
docx_insert_paragraph_at_cursor(session_id, "这是插入在中间的段落")
docx_insert_table_at_cursor(session_id, rows=3, cols=2)
```

**格式刷（Format Painter）**：
```python
# 将源对象（如 Run, Paragraph, Table）的格式复制到目标对象
docx_format_copy(session_id, source_id="run_src", target_id="run_target")
```

**创建表格**：
```python
table_id = docx_add_table(session_id, rows=3, cols=2)
cell_id = docx_get_cell(session_id, table_id, row=0, col=0)
docx_add_paragraph_to_cell(session_id, cell_id, "单元格内容")
```

## 完整工具参考

本服务器提供 42 个 MCP 工具，按功能领域分为 10 个模块：

### 1. Session Tools（会话管理，4 个）

| 工具 | 说明 |
|------|------|
| `docx_create(file_path=None, auto_save=False)` | 创建新会话或加载文档 |
| `docx_save(session_id, file_path)` | 保存文档到指定路径 |
| `docx_close(session_id)` | 关闭会话并释放资源 |
| `docx_get_context(session_id)` | 获取会话上下文信息 |

### 2. Content Tools（内容检索，4 个）

| 工具 | 说明 |
|------|------|
| `docx_read_content(session_id)` | 读取文档全文 |
| `docx_find_paragraphs(session_id, query)` | 查找包含指定文本的段落 |
| `docx_list_files(directory=".")` | 列出目录下的 .docx 文件 |
| `docx_extract_template_structure(session_id)` | 提取文档结构（标题、表格、段落） |

### 3. Paragraph Tools（段落操作，6 个）

| 工具 | 说明 |
|------|------|
| `docx_add_paragraph(session_id, text, style=None, parent_id=None)` | 添加段落 |
| `docx_add_heading(session_id, text, level=1)` | 添加标题 |
| `docx_update_paragraph_text(session_id, paragraph_id, new_text)` | 更新段落文本 |
| `docx_copy_paragraph(session_id, paragraph_id)` | 深拷贝段落（保留格式） |
| `docx_delete(session_id, element_id=None)` | 删除元素 |
| `docx_add_page_break(session_id)` | 插入分页符 |

### 4. Run Tools（文本块操作，3 个）

| 工具 | 说明 |
|------|------|
| `docx_add_run(session_id, text, paragraph_id=None)` | 向段落添加文本块 |
| `docx_update_run_text(session_id, run_id, new_text)` | 更新 Run 文本 |
| `docx_set_font(session_id, run_id, size=None, bold=None, italic=None, color_hex=None)` | 设置字体属性 |

### 5. Table Tools（表格操作，9 个）

| 工具 | 说明 |
|------|------|
| `docx_add_table(session_id, rows, cols)` | 创建表格 |
| `docx_get_table(session_id, index)` | 按索引获取表格 |
| `docx_find_table(session_id, text)` | 查找包含指定文本的表格 |
| `docx_get_cell(session_id, table_id, row, col)` | 获取单元格 |
| `docx_add_paragraph_to_cell(session_id, cell_id, text)` | 向单元格添加段落 |
| `docx_add_table_row(session_id, table_id=None)` | 添加行 |
| `docx_add_table_col(session_id, table_id=None)` | 添加列 |
| `docx_fill_table(session_id, data, table_id=None, start_row=0)` | 批量填充表格数据 |
| `docx_copy_table(session_id, table_id)` | 深拷贝表格 |

### 6. Format Tools（格式化，6 个）

| 工具 | 说明 |
|------|------|
| `docx_set_alignment(session_id, paragraph_id, alignment)` | 设置段落对齐方式 |
| `docx_set_properties(session_id, properties, element_id=None)` | 通用属性设置（JSON） |
| `docx_format_copy(session_id, source_id, target_id)` | 复制格式（格式刷） |
| `docx_set_margins(session_id, top=None, bottom=None, left=None, right=None)` | 设置页边距 |
| `docx_extract_format_template(session_id, element_id)` | 提取格式模板 |
| `docx_apply_format_template(session_id, element_id, template_json)` | 应用格式模板 |

### 7. Advanced Tools（高级编辑，3 个）

| 工具 | 说明 |
|------|------|
| `docx_replace_text(session_id, old_text, new_text, scope_id=None)` | 智能文本替换（跨 Run） |
| `docx_batch_replace_text(session_id, replacements_json, scope_id=None)` | 批量文本替换 |
| `docx_insert_image(session_id, image_path, width=None, height=None, parent_id=None)` | 插入图片 |

### 8. Cursor Tools（光标定位，4 个）

| 工具 | 说明 |
|------|------|
| `docx_cursor_get(session_id)` | 获取当前光标位置 |
| `docx_cursor_move(session_id, element_id, position)` | 移动光标到指定位置 |
| `docx_insert_paragraph_at_cursor(session_id, text, style=None)` | 在光标处插入段落 |
| `docx_insert_table_at_cursor(session_id, rows, cols)` | 在光标处插入表格 |

### 9. Copy Tools（复制与元数据，2 个）

| 工具 | 说明 |
|------|------|
| `docx_get_element_source(session_id, element_id)` | 获取元素来源元数据 |
| `docx_copy_elements_range(session_id, start_id, end_id)` | 复制元素区间 |

### 10. System Tools（系统状态，1 个）

| 工具 | 说明 |
|------|------|
| `docx_server_status()` | 获取服务器状态和环境信息 |

### 工具设计原则

1. **原子化操作**：每个工具只做一件事
2. **ID 映射系统**：所有对象通过稳定 ID 引用
3. **混合上下文**：支持显式 ID 和隐式上下文
4. **格式保留**：高级操作保留原始格式

详细参数和示例请参考 [README.md](../README.md) 的工具列表部分。

---

**最后更新**：2026-01-21
