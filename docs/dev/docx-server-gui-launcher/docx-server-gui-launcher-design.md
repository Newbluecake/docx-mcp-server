# 技术设计: Docx Server Windows GUI Launcher

## 1. 系统架构

### 1.1 模块划分

```mermaid
graph TD
    A[Launcher (Main Window)] --> B[Server Manager]
    A --> C[Config Injector]
    A --> D[Log Handler]
    B --> E[Subprocess (docx_mcp_server)]
    C --> F[Claude Config File]
```

- **GUI Layer (`src/docx_server_launcher/gui/`)**:
  - 基于 PyQt6 实现。
  - 主窗口包含配置区域、控制按钮（启动/停止）、日志显示区域。
- **Core Layer (`src/docx_server_launcher/core/`)**:
  - `ServerManager`: 负责启动和停止 `docx-mcp-server` 子进程，捕获 stdout/stderr。
  - `ConfigInjector`: 负责读取和修改 `claude_desktop_config.json`。
- **Entry Point (`src/docx_server_launcher/main.py`)**:
  - 程序入口，初始化 QApplication。

### 1.2 数据流

1. **启动服务**:
   - 用户输入 Port (e.g., 8000) 和 Host (e.g., 127.0.0.1)。
   - 点击 "Start"。
   - `ServerManager` 构建命令: `python -m docx_mcp_server --port 8000 --host 127.0.0.1` (或者直接调用入口点)。
   - `ServerManager` 启动 `QProcess` 或 `subprocess`。
   - 信号 `server_started` 触发 UI 更新。

2. **日志流**:
   - 子进程输出 -> `ServerManager` 捕获 -> 发送信号 `log_received` -> UI 追加文本。

3. **配置注入**:
   - 用户选择 Claude Config 路径。
   - `ConfigInjector` 读取 JSON。
   - 插入/更新 `docx-server` 节点。
   - 保存 JSON。

## 2. 关键组件设计

### 2.1 ServerManager

```python
class ServerManager(QObject):
    server_started = pyqtSignal()
    server_stopped = pyqtSignal()
    log_received = pyqtSignal(str)

    def start_server(self, host: str, port: int, cwd: str):
        # 使用 QProcess 或 subprocess
        pass

    def stop_server(self):
        # terminate process
        pass
```

### 2.2 ConfigInjector

```python
class ConfigInjector:
    def inject(self, config_path: str, server_url: str):
        # Read JSON
        # Update "mcpServers" -> "docx-server"
        # Write JSON
        pass
```

### 2.3 UI Layout

- **Top Section**: Configuration
  - Working Directory (File Picker)
  - Host (LineEdit, default 127.0.0.1)
  - Port (SpinBox, default 8000)
- **Middle Section**: Actions
  - Button: Start / Stop (Toggle)
  - Button: Inject Config to Claude
- **Bottom Section**: Logs
  - QPlainTextEdit (ReadOnly)

## 3. 技术选型与依赖

- **Python**: 3.10+
- **GUI**: PyQt6 (稳定，功能全)
- **Packaging**: PyInstaller (生成单文件 .exe)
- **Process Management**: `PyQt6.QtCore.QProcess` (更好的 Qt 集成)

## 4. 目录结构

```
src/
  docx_server_launcher/
    __init__.py
    main.py
    core/
      __init__.py
      server_manager.py
      config_injector.py
    gui/
      __init__.py
      main_window.py
      widgets.py
    resources/
      icon.ico
```
