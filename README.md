# docx-mcp-server

一个基于 Model Context Protocol (MCP) 的服务器，为 Claude 提供细粒度的 Microsoft Word (.docx) 文档操作能力。

## 特性

- **会话管理**：维护有状态的文档编辑会话，支持并发操作
- **原子化操作**：精确控制段落、文本块、标题和表格的每个元素
- **格式化**：设置字体（粗体、斜体、大小、颜色）和对齐方式
- **布局控制**：调整页边距和插入分页符
- **表格支持**：创建表格并填充单元格内容

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

### 运行服务器

```bash
mcp-server-docx
```

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

- `docx_create()` - 创建新文档会话
  - 返回：`session_id`

- `docx_save(session_id, file_path)` - 保存文档到文件
  - 参数：会话 ID、文件路径（绝对路径）
  - 返回：成功消息

- `docx_close(session_id)` - 关闭会话并释放资源
  - 参数：会话 ID
  - 返回：成功消息

### 内容操作

- `docx_add_paragraph(session_id, text, style=None)` - 添加段落
  - 返回：`paragraph_id`

- `docx_add_heading(session_id, text, level=1)` - 添加标题
  - 参数：标题文本、级别（0-9）
  - 返回：`paragraph_id`

- `docx_add_run(session_id, paragraph_id, text)` - 向段落添加文本块
  - 返回：`run_id`

- `docx_add_page_break(session_id)` - 插入分页符
  - 返回：成功消息

### 格式化

- `docx_set_font(session_id, run_id, size=None, bold=None, italic=None, color_hex=None)` - 设置字体属性
  - 参数：
    - `size`: 字号（磅）
    - `bold`: 是否粗体
    - `italic`: 是否斜体
    - `color_hex`: 颜色（如 "FF0000" 表示红色）

- `docx_set_alignment(session_id, paragraph_id, alignment)` - 设置段落对齐
  - 参数：`alignment` 可选值：`"left"`, `"center"`, `"right"`, `"justify"`

- `docx_set_margins(session_id, top=None, bottom=None, left=None, right=None)` - 设置页边距
  - 参数：边距值（英寸）

### 表格操作

- `docx_add_table(session_id, rows, cols)` - 创建表格
  - 返回：`table_id`

- `docx_get_cell(session_id, table_id, row, col)` - 获取单元格
  - 参数：行列索引（从 0 开始）
  - 返回：`cell_id`

- `docx_add_paragraph_to_cell(session_id, cell_id, text)` - 向单元格添加内容
  - 返回：`paragraph_id`

## 使用示例

### 示例 1：创建简单文档

```python
# 通过 Claude 使用 MCP 工具
session_id = docx_create()
docx_add_heading(session_id, "我的文档", level=1)
para_id = docx_add_paragraph(session_id, "这是第一段内容。")
docx_save(session_id, "/path/to/output.docx")
docx_close(session_id)
```

### 示例 2：格式化文本

```python
session_id = docx_create()

# 创建段落和文本块
para_id = docx_add_paragraph(session_id, "")
run_id = docx_add_run(session_id, para_id, "重要提示")

# 设置格式
docx_set_font(session_id, run_id, size=16, bold=True, color_hex="FF0000")
docx_set_alignment(session_id, para_id, "center")

docx_save(session_id, "/path/to/formatted.docx")
docx_close(session_id)
```

### 示例 3：创建表格

```python
session_id = docx_create()

# 创建 3x2 表格
table_id = docx_add_table(session_id, rows=3, cols=2)

# 填充表头
cell_id = docx_get_cell(session_id, table_id, row=0, col=0)
docx_add_paragraph_to_cell(session_id, cell_id, "姓名")

cell_id = docx_get_cell(session_id, table_id, row=0, col=1)
docx_add_paragraph_to_cell(session_id, cell_id, "年龄")

# 填充数据
cell_id = docx_get_cell(session_id, table_id, row=1, col=0)
docx_add_paragraph_to_cell(session_id, cell_id, "张三")

docx_save(session_id, "/path/to/table.docx")
docx_close(session_id)
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
│   ├── server.py          # MCP 工具定义
│   ├── core/
│   │   └── session.py     # 会话管理
│   └── utils/
│       └── logger.py      # 日志工具
├── tests/
│   ├── unit/              # 单元测试
│   └── e2e/               # 端到端测试
├── config/
│   ├── dev.yaml           # 开发环境配置
│   └── prod.yaml          # 生产环境配置
├── scripts/
│   ├── install.sh         # 安装脚本
│   └── test.sh            # 测试脚本
├── .claude/
│   └── prompts/           # Claude 提示词模板
├── CLAUDE.md              # Claude 开发指南
└── README.md
```

### 添加新工具

参考 [CLAUDE.md](CLAUDE.md) 中的开发指南，或使用 `.claude/prompts/add-new-tool.md` 模板。

### 配置说明

- `config/dev.yaml` - 开发环境配置（详细日志、短超时）
- `config/prod.yaml` - 生产环境配置（警告日志、长超时）

## 核心概念

### 会话管理

每个文档编辑操作都在一个会话中进行：

1. 创建会话：`docx_create()` 返回 `session_id`
2. 执行操作：使用 `session_id` 调用其他工具
3. 保存文档：`docx_save(session_id, path)`
4. 关闭会话：`docx_close(session_id)` 释放资源

会话默认 1 小时后自动过期。

### 对象 ID 映射

python-docx 的对象（段落、文本块）没有稳定 ID，本服务器通过 ID 映射系统解决：

- 创建对象时返回唯一 ID（如 `para_a1b2c3d4`）
- 后续操作使用该 ID 引用对象
- ID 在会话内有效

### 原子化操作

每个工具只做一件事，通过组合实现复杂功能：

```python
# 创建格式化段落需要多步操作
para_id = docx_add_paragraph(session_id, "")
run_id = docx_add_run(session_id, para_id, "文本")
docx_set_font(session_id, run_id, bold=True)
```

这种设计让 Claude 可以灵活控制每个细节。

## 常见问题

**Q: 会话过期后数据会丢失吗？**

A: 是的。必须在过期前调用 `docx_save()` 保存文件。

**Q: 可以同时编辑多个文档吗？**

A: 可以。每个 `docx_create()` 创建独立的会话。

**Q: 如何处理大文档？**

A: 分批操作，及时保存，避免长时间持有会话。参考 `.claude/prompts/optimize-performance.md`。

## 贡献

欢迎提交 Issue 和 Pull Request！

提交前请：
1. 运行 `./scripts/test.sh` 确保测试通过
2. 遵循现有代码风格
3. 更新相关文档

详细指南请参考 [CLAUDE.md](CLAUDE.md)。

## 许可证

MIT License

## 相关资源

- [MCP 协议规范](https://modelcontextprotocol.io)
- [python-docx 文档](https://python-docx.readthedocs.io)
- [Claude Desktop](https://claude.ai/download)
