# docx-mcp-server

一个基于 Model Context Protocol (MCP) 的服务器，为 Claude 提供细粒度的 Microsoft Word (.docx) 文档操作能力。

## 特性

- **会话管理**：维护有状态的文档编辑会话，支持并发操作
- **原子化操作**：精确控制段落、文本块、标题和表格的每个元素
- **混合上下文**：支持基于 ID 的精确操作和基于上下文的便捷操作
- **高级内容操作**：
  - **表格处理**：深拷贝表格、批量填充数据
  - **文本替换**：支持跨 Run 的智能文本替换（Text Stitching）
  - **模板填充**：完善的模板占位符处理能力
- **精确布局控制**：支持通过 `position` 参数（如 `after:para_123`）将元素插入到文档的任意位置
- **可视化上下文**：工具返回直观的 ASCII 树状图，展示操作前后的文档结构
- **格式化**：设置字体（粗体、斜体、大小、颜色）和对齐方式
- **布局控制**：调整页边距和插入分页符
- **Windows GUI**：提供独立的 Windows 启动器，无需配置环境即可使用

## 快速开始

### 安装

使用安装脚本（推荐）：

```bash
./scripts/install.sh
```

或手动安装：

```bash
pip install .
```

### Windows 用户（GUI 启动器）

直接下载最新发布的 `DocxServerLauncher.exe`，双击运行即可。无需安装 Python 或任何依赖。

### 运行服务器

服务器支持三种传输模式：

#### 1. STDIO 模式（默认，用于 Claude Desktop）

```bash
mcp-server-docx
# 或显式指定
mcp-server-docx --transport stdio
```

#### 2. SSE 模式（HTTP Server-Sent Events）

适用于需要通过 HTTP 访问的场景：

```bash
# 使用默认配置（127.0.0.1:8000）
mcp-server-docx --transport sse

# 指定自定义 host 和 port
mcp-server-docx --transport sse --host 0.0.0.0 --port 3000

# 使用环境变量
DOCX_MCP_TRANSPORT=sse DOCX_MCP_HOST=127.0.0.1 DOCX_MCP_PORT=3000 mcp-server-docx
```

启动后可通过 `http://127.0.0.1:8000` 访问（或你指定的 host:port）。

#### 3. Streamable HTTP 模式

```bash
# 使用默认配置
mcp-server-docx --transport streamable-http

# 指定 host、port 和挂载路径
mcp-server-docx --transport streamable-http --host 0.0.0.0 --port 8080 --mount-path /mcp
```

启动后可通过 `http://0.0.0.0:8080/mcp` 访问（如果指定了 mount-path）。

#### 查看所有选项

```bash
mcp-server-docx --help
mcp-server-docx --version
```

#### Windows GUI 启动器

Windows GUI 启动器会自动使用 SSE 模式启动服务器，你可以在界面中配置：
- **Host**: 通过"Allow LAN Access"复选框选择 127.0.0.1（本地）或 0.0.0.0（局域网）
- **Port**: 在端口输入框中指定端口号
- **Working Directory**: 服务器的工作目录

### 构建可执行文件

如果您想自己从源码构建 Windows 可执行文件：

```powershell
# 1. 确保已安装 Python 3.10+
# 2. 运行构建脚本
.\scripts\build_exe.ps1
```

构建产物将位于 `dist\DocxServerLauncher.exe`。

### 配置 Claude Desktop

在 Claude Desktop 的 MCP 配置中添加：

```json
{
  "mcpServers": {
    "docx": {
      "command": "mcp-server-docx"
    }
  }
}
```

## MCP 工具列表

### 生命周期管理

- `docx_create(file_path=None, auto_save=False)` - 创建新文档会话
- `docx_save(session_id, file_path)` - 保存文档到文件
- `docx_close(session_id)` - 关闭会话并释放资源
- `docx_get_context(session_id)` - 获取当前会话上下文信息

### 内容检索与浏览

- `docx_read_content(session_id)` - 读取文档全文
- `docx_list_files(directory=".")` - 列出目录下的 .docx 文件
- `docx_find_paragraphs(session_id, query)` - 查找包含特定文本的段落
- `docx_find_table(session_id, text)` - 查找包含特定文本的表格
- `docx_get_table(session_id, index)` - 按索引获取表格

### 内容编辑

- `docx_insert_paragraph(session_id, text, position, style=None)` - 添加段落（position 必选）
- `docx_insert_heading(session_id, text, position, level=1)` - 添加标题（position 必选）
- `docx_insert_run(session_id, text, position)` - 向段落添加文本块（position 必选）
- `docx_insert_page_break(session_id, position)` - 插入分页符（position 必选）
- `docx_insert_image(session_id, image_path, width=None, height=None, position)` - 插入图片（position 必选）

### 高级编辑

- `docx_copy_paragraph(session_id, paragraph_id, position)` - 复制段落（保留格式）
- `docx_copy_table(session_id, table_id, position)` - 深拷贝表格（保留结构与格式）
- `docx_copy_elements_range(session_id, start_id, end_id, position)` - 复制元素区间（如整个章节）
- `docx_replace_text(session_id, old_text, new_text, scope_id=None)` - 智能文本替换（支持模板填充）
- `docx_batch_replace_text(session_id, replacements_json, scope_id=None)` - 批量文本替换（格式保留）
- `docx_update_paragraph_text(session_id, paragraph_id, new_text)` - 更新段落文本
- `docx_update_run_text(session_id, run_id, new_text)` - 更新 Run 文本
- `docx_extract_template_structure(session_id)` - 提取文档模板结构（智能识别标题、表格、段落）
- `docx_extract_format_template(session_id, element_id)` - 提取格式模板
- `docx_apply_format_template(session_id, element_id, template_json)` - 应用格式模板
- `docx_get_element_source(session_id, element_id)` - 获取元素来源元数据

### 表格操作

- `docx_insert_table(session_id, rows, cols, position)` - 创建表格（position 必选）
- `docx_insert_table_row(session_id, position)` - 添加行到表格末尾（position 必选）
- `docx_insert_table_col(session_id, position)` - 添加列到表格末尾（position 必选）
- `docx_insert_row_at(session_id, table_id, position, row_index=None, copy_format=False)` - 在指定位置插入行（支持 after:N, before:N, start, end）
- `docx_insert_col_at(session_id, table_id, position, col_index=None, copy_format=False)` - 在指定位置插入列（支持 after:N, before:N, start, end）
- `docx_delete_row(session_id, table_id, row_index)` - 删除指定行（自动清理 element_id）
- `docx_delete_col(session_id, table_id, col_index)` - 删除指定列（自动清理 element_id）
- `docx_fill_table(session_id, data, table_id=None, start_row=0)` - 批量填充表格数据
- `docx_get_cell(session_id, table_id, row, col)` - 获取单元格
- `docx_insert_paragraph_to_cell(session_id, text, position)` - 向单元格添加段落（position 必选）

### 格式化

- `docx_set_properties(session_id, properties, element_id=None)` - 通用属性设置（JSON 格式）
- `docx_set_font(...)` - 设置字体属性（快捷方式）
- `docx_set_alignment(...)` - 设置对齐方式（快捷方式）
- `docx_set_margins(...)` - 设置页边距

### Cursor 定位系统

- `docx_cursor_get(session_id)` - 获取当前光标位置
- `docx_cursor_move(session_id, element_id, position)` - 移动光标到指定位置

## 使用示例

### 示例 1：提取模板结构

```python
session_id = docx_create(file_path="/path/to/template.docx")

# 提取文档结构（智能识别标题、表格、段落）
structure_json = docx_extract_template_structure(session_id)
structure = json.loads(structure_json)

# 查看提取的元素
for element in structure["document_structure"]:
    if element["type"] == "table":
        print(f"表格: {element['headers']}")  # 自动检测的表头
    elif element["type"] == "heading":
        print(f"标题 {element['level']}: {element['text']}")
```

输出格式：
```json
{
  "metadata": {
    "extracted_at": "2026-01-21T...",
    "docx_version": "0.1.3"
  },
  "document_structure": [
    {
      "type": "heading",
      "level": 1,
      "text": "章节标题",
      "style": {"font": "Arial", "size": 16, "bold": true}
    },
    {
      "type": "table",
      "rows": 5,
      "cols": 3,
      "header_row": 0,
      "headers": ["姓名", "年龄", "部门"],
      "style": {...}
    },
    {
      "type": "paragraph",
      "text": "段落内容",
      "style": {"font": "宋体", "size": 12, "alignment": "left"}
    }
  ]
}
```

### 示例 2：高级编辑功能

#### 2.1 模板填充（智能替换）

```python
session_id = docx_create(file_path="/path/to/template.docx")

# 智能替换 {{name}} 占位符，即使它跨越了多个 Run
docx_replace_text(session_id, "{{name}}", "张三")
docx_replace_text(session_id, "{{date}}", "2026-01-20")

docx_save(session_id, "/path/to/result.docx")
```

#### 2.2 表格克隆与填充

```python
session_id = docx_create()

# 获取模板中的第一个表格
table_id = docx_get_table(session_id, 0)

# 克隆表格用于填充新数据
new_table_id = docx_copy_table(session_id, table_id)

# 批量填充数据
data = json.dumps([
    ["李四", "28", "工程师"],
    ["王五", "32", "设计师"]
])
docx_fill_table(session_id, data, table_id=new_table_id, start_row=1)

docx_save(session_id, "/path/to/report.docx")
```

## 开发指南

### 安装开发环境

```bash
./scripts/install.sh
source venv/bin/activate
```

### 运行测试

```bash
./scripts/test.sh
```

或手动运行：

```bash
# 单元测试
python -m pytest tests/unit/ -v

# E2E 测试
python -m pytest tests/e2e/ -v
```

### 项目结构

```
docx-mcp-server/
├── src/docx_mcp_server/
│   ├── server.py          # MCP 主入口
│   ├── tools/             # 工具模块（按领域拆分）
│   │   ├── __init__.py
│   │   ├── session_tools.py      # 会话生命周期
│   │   ├── content_tools.py      # 内容检索与浏览
│   │   ├── paragraph_tools.py    # 段落操作
│   │   ├── run_tools.py          # 文本块操作
│   │   ├── table_tools.py        # 表格操作
│   │   ├── format_tools.py       # 格式化与样式
│   │   ├── advanced_tools.py     # 高级编辑（替换、图片）
│   │   ├── cursor_tools.py       # 光标定位系统
│   │   ├── copy_tools.py         # 复制与元数据
│   │   └── system_tools.py       # 系统状态
│   ├── core/              # 核心逻辑
│   │   ├── session.py     # 会话管理
│   │   ├── cursor.py      # 光标系统
│   │   ├── copier.py      # 对象克隆引擎
│   │   ├── replacer.py    # 文本替换引擎
│   │   └── properties.py  # 属性设置引擎
│   ├── preview/           # 实时预览
│   └── utils/             # 工具函数
├── src/docx_server_launcher/ # Windows GUI 启动器
├── tests/
│   ├── unit/              # 单元测试
│   ├── e2e/               # 端到端测试
│   └── integration/       # 集成测试
├── docs/                  # 文档
├── config/                # 配置文件
├── scripts/               # 脚本工具
└── CLAUDE.md              # Claude 开发指南
```

## 许可证

MIT License

## 相关资源

- [MCP 协议规范](https://modelcontextprotocol.io)
- [python-docx 文档](https://python-docx.readthedocs.io)
