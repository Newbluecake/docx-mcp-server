# Claude Desktop 配置指南

## 安装 MCP 服务器

从 GitHub 安装（推荐）：

```bash
pip install git+https://github.com/Newbluecake/docx-mcp-server.git
```

## 配置 Claude Desktop

编辑 Claude Desktop 配置文件：

**macOS/Linux**:
```bash
~/.config/Claude/claude_desktop_config.json
```

**Windows**:
```
%APPDATA%\Claude\claude_desktop_config.json
```

添加以下配置：

```json
{
  "mcpServers": {
    "docx": {
      "command": "python",
      "args": ["-m", "docx_mcp_server"]
    }
  }
}
```

## 验证安装

1. 重启 Claude Desktop
2. 在对话中输入：

```
请使用 docx 工具创建一个新文档，添加标题"测试报告"，然后保存为 test.docx
```

3. 如果看到 Claude 调用了 `docx_create`, `docx_insert_heading`, `docx_save` 等工具，说明配置成功！

## 使用示例

### 创建简单文档
```
创建一个新的 Word 文档，包含：
- 标题：项目报告
- 段落：这是一个测试文档
- 保存为：report.docx
```

### 创建格式化文档
```
创建一个文档，包含：
1. 居中的标题"年度总结"（加粗，16号字）
2. 正文段落，首行缩进
3. 一个 3x3 的表格，第一行作为表头
保存为 summary.docx
```

### 批量生成文档
```
根据以下数据生成 3 份合同：
- 客户A，金额 10000
- 客户B，金额 20000
- 客户C，金额 15000

每份合同包含标题、客户信息表格、金额说明
```

## 故障排查

### 工具未显示
1. 检查 Python 路径：`which python`
2. 检查安装：`python -m docx_mcp_server --help`
3. 查看 Claude Desktop 日志（Help → View Logs）

### 文档保存失败
- 确保文件路径有写入权限
- 使用绝对路径（如 `/Users/username/Documents/test.docx`）

## 更新服务器

```bash
pip install --upgrade git+https://github.com/Newbluecake/docx-mcp-server.git
```

## 卸载

```bash
pip uninstall docx-mcp-server
```

然后从 `claude_desktop_config.json` 中移除 `docx` 配置。
