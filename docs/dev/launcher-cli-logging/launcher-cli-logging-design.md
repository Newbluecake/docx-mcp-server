---
feature: launcher-cli-logging
complexity: standard
version: 1
generated_at: 2026-01-25T11:00:00Z
---

# 技术设计文档: Launcher CLI Logging Enhancement

> **功能标识**: launcher-cli-logging
> **复杂度**: standard
> **版本**: 1

## 1. 系统架构设计

### 1.1 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                     GUI Launcher (PyQt6)                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │ MainWindow   │───▶│ CLILauncher  │───▶│ ServerManager│ │
│  │              │    │              │    │              │ │
│  │ - CLI Params │    │ - Log Cmd    │    │ - Log Cmd    │ │
│  │ - Copy Btn   │    │ - Build Cmd  │    │ - Start MCP  │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│         │                    │                    │         │
│         └────────────────────┴────────────────────┘         │
│                              │                              │
│                    ┌─────────▼─────────┐                    │
│                    │  Logging System   │                    │
│                    │  - GUI Logger     │                    │
│                    │  - MCP Logger     │                    │
│                    └───────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 核心组件

| 组件 | 职责 | 修改类型 |
|------|------|----------|
| `ServerManager` | 启动 MCP 服务器，记录启动命令 | 增强 |
| `CLILauncher` | 启动 Claude CLI，记录启动命令 | 增强 |
| `MainWindow` | 添加 CLI 参数复选框，错误复制按钮 | 增强 |
| `QSettings` | 持久化用户的 CLI 参数选择 | 新增使用 |

---

## 2. 组件设计

### 2.1 ServerManager 增强

**文件**: `src/docx_server_launcher/core/server_manager.py`

**新增功能**:
1. 在启动 MCP 服务器前记录完整命令
2. 使用 JSON 结构化格式
3. 同时记录到 GUI 日志和 MCP 服务器日志

**关键方法**:
```python
def start_server(self, transport: str, host: str, port: int, mount_path: str = None) -> bool:
    # 构建命令
    command = ["uv", "run", "mcp-server-docx"]
    args = ["--transport", transport]
    # ... 添加其他参数

    # 记录到 GUI 日志
    log_data = {"command": command[0], "args": command[1:]}
    self.logger.info(f"Starting MCP server with command: {json.dumps(log_data)}")

    # 记录到 MCP 服务器日志（通过环境变量或配置）
    # ...

    # 启动进程
    self.process = subprocess.Popen(command, ...)
```

### 2.2 CLILauncher 增强

**文件**: `src/docx_server_launcher/core/cli_launcher.py`

**新增功能**:
1. 记录完整的 Claude CLI 命令
2. 记录 MCP 配置 JSON
3. 记录用户输入的额外参数

**关键方法**:
```python
def launch_claude_cli(self, mcp_config: dict, extra_params: list = None) -> bool:
    # 构建命令
    mcp_config_json = json.dumps(mcp_config)
    command = f"claude --mcp-config '{mcp_config_json}'"

    if extra_params:
        command += " " + " ".join(extra_params)

    # 记录日志
    self.logger.info("Launching Claude CLI")
    self.logger.info(f"Command: {command}")
    self.logger.info(f"MCP Config: {mcp_config_json}")
    if extra_params:
        self.logger.info(f"Extra Params: {' '.join(extra_params)}")

    # 启动进程
    subprocess.Popen(command, shell=True, ...)
```

### 2.3 MainWindow 增强

**文件**: `src/docx_server_launcher/gui/main_window.py`

**新增 UI 组件**:

1. **CLI 参数复选框区域**:
```python
# 在 Claude CLI 启动按钮附近添加
self.cli_params_group = QGroupBox("Claude CLI Parameters")
self.cli_params_layout = QVBoxLayout()

# Model 选择
self.model_checkbox = QCheckBox("--model")
self.model_combo = QComboBox()
self.model_combo.addItems(["sonnet", "opus", "haiku"])

# Agent 选择
self.agent_checkbox = QCheckBox("--agent")
self.agent_input = QLineEdit()

# Verbose 和 Debug
self.verbose_checkbox = QCheckBox("--verbose")
self.debug_checkbox = QCheckBox("--debug")
```

2. **错误弹窗复制按钮**:
```python
def show_error_dialog(self, title: str, message: str):
    dialog = QMessageBox(self)
    dialog.setIcon(QMessageBox.Icon.Critical)
    dialog.setWindowTitle(title)
    dialog.setText(message)

    # 添加复制按钮
    copy_button = dialog.addButton("Copy", QMessageBox.ButtonRole.ActionRole)
    copy_button.clicked.connect(lambda: self.copy_to_clipboard(message))

    dialog.exec()

def copy_to_clipboard(self, text: str):
    clipboard = QApplication.clipboard()
    clipboard.setText(text)
    # 显示提示
    QMessageBox.information(self, "Copied", "Error message copied to clipboard")
```

**配置持久化**:
```python
def save_cli_params(self):
    settings = QSettings("docx-mcp-server", "launcher")
    settings.setValue("cli/model_enabled", self.model_checkbox.isChecked())
    settings.setValue("cli/model_value", self.model_combo.currentText())
    settings.setValue("cli/agent_enabled", self.agent_checkbox.isChecked())
    settings.setValue("cli/agent_value", self.agent_input.text())
    settings.setValue("cli/verbose", self.verbose_checkbox.isChecked())
    settings.setValue("cli/debug", self.debug_checkbox.isChecked())

def load_cli_params(self):
    settings = QSettings("docx-mcp-server", "launcher")
    self.model_checkbox.setChecked(settings.value("cli/model_enabled", False, bool))
    self.model_combo.setCurrentText(settings.value("cli/model_value", "sonnet"))
    # ... 加载其他参数
```

---

## 3. 接口设计

### 3.1 日志接口

**日志格式规范**:

```python
# MCP 服务器启动日志
{
    "timestamp": "2026-01-25T10:30:45Z",
    "level": "INFO",
    "message": "Starting MCP server with command",
    "data": {
        "command": "uv",
        "args": ["run", "mcp-server-docx", "--transport", "sse", "--port", "3000"]
    }
}

# Claude CLI 启动日志
{
    "timestamp": "2026-01-25T10:30:50Z",
    "level": "INFO",
    "message": "Launching Claude CLI",
    "data": {
        "command": "claude --mcp-config {...} --model opus",
        "mcp_config": {...},
        "extra_params": ["--model", "opus"]
    }
}
```

### 3.2 配置接口

**QSettings 键值规范**:

| 键 | 类型 | 默认值 | 说明 |
|----|------|--------|------|
| `cli/model_enabled` | bool | false | 是否启用 --model 参数 |
| `cli/model_value` | str | "sonnet" | model 参数值 |
| `cli/agent_enabled` | bool | false | 是否启用 --agent 参数 |
| `cli/agent_value` | str | "" | agent 参数值 |
| `cli/verbose` | bool | false | 是否启用 --verbose |
| `cli/debug` | bool | false | 是否启用 --debug |

---

## 4. 数据设计

### 4.1 日志文件结构

```
logs/
├── gui_launcher.log          # GUI 启动器日志（包含所有启动命令）
├── gui_launcher.log.1         # 轮转日志
├── mcp_server.log            # MCP 服务器日志（包含服务器启动命令）
└── mcp_server.log.1          # 轮转日志
```

### 4.2 配置文件

使用 QSettings 自动管理，位置取决于操作系统:
- Linux: `~/.config/docx-mcp-server/launcher.conf`
- macOS: `~/Library/Preferences/com.docx-mcp-server.launcher.plist`
- Windows: `HKEY_CURRENT_USER\Software\docx-mcp-server\launcher`

---

## 5. 安全考量

### 5.1 日志安全

1. **敏感信息过滤**:
   - 不记录可能包含敏感信息的环境变量
   - 不记录用户的完整文件路径（仅记录相对路径）

2. **日志文件权限**:
   - 确保日志文件仅当前用户可读写（chmod 600）

### 5.2 剪贴板安全

1. **复制内容限制**:
   - 仅复制错误消息本身，不包含系统路径
   - 限制复制内容长度（最多 10KB）

---

## 6. 性能考量

### 6.1 日志性能

1. **异步日志**:
   - 使用 Python logging 的异步处理器
   - 避免阻塞主线程

2. **日志轮转**:
   - 使用 RotatingFileHandler
   - 最大文件大小: 10MB
   - 保留文件数: 5

### 6.2 UI 响应性

1. **复选框状态保存**:
   - 使用 QTimer 延迟保存（避免频繁写入）
   - 仅在值变化时保存

---

## 7. 测试策略

### 7.1 单元测试

| 测试模块 | 测试内容 |
|---------|---------|
| `test_server_manager.py` | 验证 MCP 服务器启动命令日志格式 |
| `test_cli_launcher.py` | 验证 Claude CLI 启动命令日志格式 |
| `test_main_window.py` | 验证 CLI 参数复选框功能和配置持久化 |

### 7.2 集成测试

| 测试场景 | 验证点 |
|---------|--------|
| 启动 MCP 服务器 | 日志文件包含正确的启动命令 |
| 启动 Claude CLI | 日志文件包含完整的命令和配置 |
| 勾选 CLI 参数 | 启动命令包含选中的参数 |
| 重启 GUI | CLI 参数选择被正确恢复 |
| 触发错误弹窗 | 复制按钮正常工作 |

### 7.3 E2E 测试

使用 pytest-qt 进行 GUI 自动化测试:
```python
def test_cli_params_persistence(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    # 勾选参数
    window.model_checkbox.setChecked(True)
    window.model_combo.setCurrentText("opus")

    # 保存并重启
    window.save_cli_params()
    window.close()

    # 创建新窗口
    new_window = MainWindow()
    qtbot.addWidget(new_window)
    new_window.load_cli_params()

    # 验证
    assert new_window.model_checkbox.isChecked()
    assert new_window.model_combo.currentText() == "opus"
```

---

## 8. 部署考量

### 8.1 向后兼容性

1. **配置迁移**:
   - 首次启动时检查旧配置
   - 自动迁移到新的 QSettings 格式

2. **日志格式**:
   - 新日志格式不影响现有日志解析工具

### 8.2 文档更新

需要更新的文档:
- `README.md` - 添加 CLI 参数复选框说明
- `docs/user-guide.md` - 添加日志查看指南
- `CHANGELOG.md` - 记录新功能

---

## 9. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 日志文件过大 | 磁盘空间占用 | 使用日志轮转，限制文件大小和数量 |
| 敏感信息泄露 | 安全风险 | 实施日志过滤，不记录敏感信息 |
| UI 复杂度增加 | 用户体验下降 | 使用可折叠的参数区域，默认隐藏 |
| 配置文件损坏 | 启动失败 | 添加配置验证和默认值回退 |

---

## 10. 后续优化方向

1. **日志搜索功能**: 在 GUI 中添加日志查看和搜索面板
2. **命令历史**: 记录最近使用的 CLI 参数组合
3. **预设配置**: 支持保存和加载多个 CLI 参数预设
4. **日志导出**: 支持导出日志为 JSON 或 CSV 格式

---

**维护者**: AI Team
**最后更新**: 2026-01-25
