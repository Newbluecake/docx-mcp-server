---
feature: docx-server-gui-launcher
complexity: standard
generated_by: clarify
generated_at: 2026-01-20T12:00:00Z
version: 1
---

# 需求文档: Docx Server Windows GUI Launcher

> **功能标识**: docx-server-gui-launcher
> **复杂度**: standard
> **生成方式**: clarify

## 1. 概述

### 1.1 一句话描述
构建一个独立的 Windows GUI 应用程序（.exe），允许用户通过图形界面配置和启动 Docx MCP Server，并辅助将配置注入到 Claude Desktop 中。

### 1.2 核心价值
- **零依赖使用**：用户无需安装 Python 或命令行工具，双击即可运行。
- **配置可视化**：通过 GUI 选择工作目录、端口，避免手动编辑配置文件的错误。
- **服务独立化**：支持将 MCP Server 作为独立 HTTP/SSE 服务运行，而非仅作为子进程。

### 1.3 目标用户
- **Windows 用户**：不熟悉命令行，希望通过简单的界面使用 MCP Server。

---

## 2. 需求与用户故事

### 2.1 需求清单

| ID | 需求点 | 优先级 | 用户故事 |
|----|--------|--------|----------|
| R-001 | 独立可执行文件 | P0 | As a Windows User, 我希望下载一个 .exe 文件直接运行，无需配置 Python 环境。 |
| R-002 | 图形化配置界面 | P0 | As a User, 我希望通过 GUI 选择工作目录、设置端口和 Interface。 |
| R-003 | HTTP/SSE 服务启动 | P0 | As a User, 我希望点击“启动服务”按钮后，后台运行 MCP Server 并监听指定端口。 |
| R-004 | Claude 配置注入 | P1 | As a User, 我希望选择 Claude 配置文件路径后，工具能自动将当前 MCP 服务配置写入其中。 |
| R-005 | 日志查看 | P2 | As a User, 我希望在界面上看到 Server 的运行日志，以便确认服务是否正常。 |

### 2.2 验收标准

#### R-001: 独立可执行文件
- **WHEN** 在没有 Python 的 Windows 机器上双击 .exe
- **THEN** 应用程序成功启动，显示 GUI 界面

#### R-002: 图形化配置界面
- **WHEN** 界面加载
- **THEN** 显示“工作目录”选择框（默认当前目录）、“端口”输入框（默认 8000）、“Interface”输入框（默认 127.0.0.1）

#### R-003: HTTP/SSE 服务启动
- **WHEN** 点击“Start Server”
- **THEN** 界面状态变为“Running”，且端口被占用
- **WHEN** 点击“Stop Server”
- **THEN** 界面状态变为“Stopped”，端口释放

#### R-004: Claude 配置注入
- **WHEN** 点击“Inject Config”并选择有效的 `claude_desktop_config.json`
- **THEN** 文件被更新，新增 `docx-server` 项，配置为 `sse` 类型指向当前 URL

---

## 3. 技术约束

### 3.1 技术栈
- **Language**: Python 3.10+
- **GUI Framework**: PyQt6
- **Packaging**: PyInstaller
- **OS Target**: Windows (但开发环境可能为 Linux/Mac，需考虑交叉编译或 CI 构建)

### 3.2 架构设计
- **Launcher**: PyQt6 应用程序，负责 UI 和配置管理。
- **Server Process**: 使用 `subprocess` 或 `multiprocessing` 启动现有的 `docx_mcp_server`。
- **Config Injector**: 独立的 JSON 操作逻辑。

---

## 4. 排除项

- **自动更新**：暂不支持自动下载新版本。
- **系统托盘**：暂不支持最小化到托盘。
- **跨平台构建**：主要关注 Windows exe，Linux/Mac 用户通常使用 CLI。

---

## 5. 下一步

✅ 在新会话中执行：
```bash
/clouditera:dev:spec-dev docx-server-gui-launcher --skip-requirements
```
