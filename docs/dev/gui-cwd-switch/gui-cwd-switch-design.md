---
feature: gui-cwd-switch
stage: 2
generated_at: 2026-01-21T10:15:00Z
version: 2 (revised)
---

# 技术设计文档: GUI 工作目录切换与服务重启

> **功能标识**: gui-cwd-switch
> **复杂度**: standard
> **生成时间**: 2026-01-21T10:15:00Z
> **修订说明**: v2 版本修复了信号泄漏、缺少导入和状态判断脆弱性问题

## 1. 架构设计

### 1.1 整体架构

```
┌─────────────────────────────────────────────────┐
│           MainWindow (GUI Layer)                │
├─────────────────────────────────────────────────┤
│  UI Components:                                 │
│  - cwd_input (QLineEdit)                       │
│  - cwd_browse_btn (QPushButton)                │
│  - cwd_history_btn (QPushButton) [新增]        │
│  - status_label (QLabel)                       │
│                                                 │
│  Event Handlers:                                │
│  - browse_cwd() [修改]                         │
│  - switch_cwd(new_path) [新增]                 │
│  - show_cwd_history() [新增]                   │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│      WorkingDirectoryManager (Business Layer)   │
├─────────────────────────────────────────────────┤
│  Methods:                                       │
│  - validate_directory(path) -> (bool, str)     │
│  - add_to_history(path)                        │
│  - get_history() -> List[str]                  │
│  - save_settings()                             │
│  - load_settings()                             │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│       ServerManager (Service Layer)             │
├─────────────────────────────────────────────────┤
│  Existing Methods:                              │
│  - start_server(host, port, cwd)               │
│  - stop_server()                               │
│  - process (QProcess)                          │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│           QSettings (Storage Layer)             │
├─────────────────────────────────────────────────┤
│  Keys:                                          │
│  - cwd (current working directory)             │
│  - cwd_history (list of recent directories)    │
│  - host, port (existing)                       │
└─────────────────────────────────────────────────┘
```

### 1.2 核心设计决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 历史记录存储 | QSettings (列表形式) | 与现有配置管理一致，Qt 原生支持 |
| 历史记录容量 | 10 条 | 平衡易用性和存储空间 |
| 去重策略 | 移到列表首位 | 保持最近使用顺序 |
| 重启触发时机 | 仅当服务运行中 | 避免不必要的操作 |
| 错误回滚机制 | 保存原 cwd，失败时恢复 | 确保用户体验流畅 |
| 状态判断 | QProcess.state() | 比 UI 文本判断更可靠 |
| 信号管理 | try-finally 断开 | 防止内存泄漏和重复触发 |

## 2. 模块设计

### 2.1 WorkingDirectoryManager 类

**职责**: 管理工作目录的验证、历史记录、配置持久化

**文件位置**: `src/docx_server_launcher/core/working_directory_manager.py`

**类定义**:

```python
import os  # [Fix: Added import]
from pathlib import Path
from typing import List, Tuple
from PyQt6.QtCore import QSettings

class WorkingDirectoryManager:
    """管理工作目录切换的核心逻辑"""

    MAX_HISTORY = 10

    def __init__(self, settings: QSettings):
        """
        Args:
            settings: QSettings 实例，用于持久化配置
        """
        self.settings = settings
        self._history_cache: List[str] = []
        self.load_settings()

    def validate_directory(self, path: str) -> Tuple[bool, str]:
        """
        验证目录是否有效

        Args:
            path: 目录路径

        Returns:
            (is_valid, error_message)
            - (True, "") 如果有效
            - (False, error_message) 如果无效
        """
        if not path:
            return False, "目录路径为空"

        p = Path(path)

        if not p.exists():
            return False, f"目录不存在: {path}"

        if not p.is_dir():
            return False, f"路径不是目录: {path}"

        # 检查读写权限
        if not os.access(path, os.R_OK | os.W_OK):
            return False, f"权限不足，无法访问: {path}"

        return True, ""

    def add_to_history(self, path: str):
        """
        添加目录到历史记录

        Args:
            path: 目录路径（已验证有效）
        """
        # 规范化路径
        normalized = str(Path(path).resolve())

        # 去重：如果已存在，先移除
        if normalized in self._history_cache:
            self._history_cache.remove(normalized)

        # 插入到列表首位
        self._history_cache.insert(0, normalized)

        # 限制长度
        self._history_cache = self._history_cache[:self.MAX_HISTORY]

        # 立即保存
        self.save_settings()

    def get_history(self) -> List[str]:
        """获取历史记录列表（最新的在前）"""
        return self._history_cache.copy()

    def save_settings(self):
        """保存配置到 QSettings"""
        self.settings.setValue("cwd_history", self._history_cache)

    def load_settings(self):
        """从 QSettings 加载配置"""
        history = self.settings.value("cwd_history", [])
        # QSettings 可能返回 None 或其他类型
        if isinstance(history, list):
            self._history_cache = history
        else:
            self._history_cache = []
```

### 2.2 MainWindow 修改

**修改范围**: `src/docx_server_launcher/gui/main_window.py`

#### 2.2.1 新增 UI 组件

```python
# 在 init_ui() 方法中，cwd_layout 修改为：
cwd_layout = QHBoxLayout()
cwd_layout.addWidget(QLabel("Working Directory:"))
self.cwd_input = QLineEdit()
self.cwd_input.setPlaceholderText(os.getcwd())
cwd_layout.addWidget(self.cwd_input)

self.cwd_browse_btn = QPushButton("Browse...")
cwd_layout.addWidget(self.cwd_browse_btn)

# 新增：历史记录按钮
self.cwd_history_btn = QPushButton("Recent ▼")
self.cwd_history_btn.setMaximumWidth(100)
cwd_layout.addWidget(self.cwd_history_btn)

config_layout.addLayout(cwd_layout)
```

#### 2.2.2 新增实例变量

```python
def __init__(self):
    # ... 现有代码 ...
    self.server_manager = ServerManager()
    self.config_injector = ConfigInjector()
    self.settings = QSettings("DocxMCP", "Launcher")

    # 新增
    self.cwd_manager = WorkingDirectoryManager(self.settings)
    self._is_switching_cwd = False  # 防止并发切换
```

#### 2.2.3 修改 browse_cwd() 方法

```python
def browse_cwd(self):
    """打开文件夹选择对话框"""
    current_dir = self.cwd_input.text() or os.getcwd()
    dir_path = QFileDialog.getExistingDirectory(
        self,
        "Select Working Directory",
        current_dir
    )

    if dir_path:
        # 调用新方法处理切换
        self.switch_cwd(dir_path)
```

#### 2.2.4 新增 switch_cwd() 方法（核心）

```python
def switch_cwd(self, new_path: str):
    """
    切换工作目录并重启服务

    Args:
        new_path: 新的工作目录路径
    """
    from PyQt6.QtCore import QProcess

    # 防止并发切换
    if self._is_switching_cwd:
        QMessageBox.warning(self, "Warning", "工作目录切换正在进行中，请稍候...")
        return

    # 验证目录
    is_valid, error_msg = self.cwd_manager.validate_directory(new_path)
    if not is_valid:
        QMessageBox.critical(self, "Invalid Directory", error_msg)
        return

    # 规范化路径
    normalized_path = str(Path(new_path).resolve())
    current_path = self.cwd_input.text() or os.getcwd()

    # 检查是否与当前目录相同
    if normalized_path == str(Path(current_path).resolve()):
        return  # 无需操作

    # 保存原目录（用于回滚）
    original_cwd = current_path

    # [Fix: Use QProcess state instead of UI text]
    is_server_running = (self.server_manager.process.state() != QProcess.ProcessState.NotRunning)

    self._is_switching_cwd = True

    try:
        if is_server_running:
            # 步骤 1: 停止服务
            self.status_label.setText("Status: Stopping server...")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
            self._disable_controls()

            # 同步等待服务停止
            self.server_manager.stop_server()

            # 等待停止完成（最多 5 秒）
            if not self._wait_for_server_stop(timeout=5000):
                raise Exception("服务停止超时")

        # 步骤 2: 更新 UI 和配置
        self.cwd_input.setText(normalized_path)
        self.settings.setValue("cwd", normalized_path)
        self.cwd_manager.add_to_history(normalized_path)

        if is_server_running:
            # 步骤 3: 启动服务
            self.status_label.setText("Status: Starting server...")
            host = "0.0.0.0" if self.lan_checkbox.isChecked() else "127.0.0.1"
            port = self.port_input.value()

            self.server_manager.start_server(host, port, normalized_path)

            # 等待启动完成（最多 10 秒）
            if not self._wait_for_server_start(timeout=10000):
                raise Exception("服务启动失败")

        # 成功提示
        QMessageBox.information(
            self,
            "Success",
            f"工作目录已切换到:\n{normalized_path}" +
            ("\n服务已重启" if is_server_running else "")
        )

    except Exception as e:
        # 回滚
        self.cwd_input.setText(original_cwd)
        self.settings.setValue("cwd", original_cwd)

        # [Fix: Improved error message]
        error_detail = f"切换失败: {str(e)}\n已回滚到原目录"

        # 尝试恢复服务（如果之前在运行）
        if is_server_running:
            try:
                host = "0.0.0.0" if self.lan_checkbox.isChecked() else "127.0.0.1"
                port = self.port_input.value()
                self.server_manager.start_server(host, port, original_cwd)
            except Exception as recovery_error:
                error_detail += f"\n\n注意：服务恢复失败: {str(recovery_error)}"

        QMessageBox.critical(self, "Error", error_detail)

    finally:
        self._is_switching_cwd = False
        self._enable_controls()
```

#### 2.2.5 新增辅助方法（修复信号泄漏）

```python
def _disable_controls(self):
    """禁用所有控制按钮"""
    self.start_btn.setEnabled(False)
    self.cwd_browse_btn.setEnabled(False)
    self.cwd_history_btn.setEnabled(False)
    self.cwd_input.setEnabled(False)
    self.lan_checkbox.setEnabled(False)
    self.port_input.setEnabled(False)

def _enable_controls(self):
    """根据服务状态恢复按钮"""
    from PyQt6.QtCore import QProcess
    is_running = (self.server_manager.process.state() != QProcess.ProcessState.NotRunning)

    self.start_btn.setEnabled(True)
    self.cwd_browse_btn.setEnabled(not is_running)
    self.cwd_history_btn.setEnabled(not is_running)
    self.cwd_input.setEnabled(not is_running)
    self.lan_checkbox.setEnabled(not is_running)
    self.port_input.setEnabled(not is_running)

def _wait_for_server_stop(self, timeout: int) -> bool:
    """
    等待服务停止
    [Fix: Signal connection management]
    """
    from PyQt6.QtCore import QEventLoop, QTimer, QProcess

    # 如果已经停止，直接返回
    if self.server_manager.process.state() == QProcess.ProcessState.NotRunning:
        return True

    loop = QEventLoop()
    timer = QTimer()
    timer.setSingleShot(True)

    stopped = [False]

    def on_stopped():
        stopped[0] = True
        loop.quit()

    # 连接信号
    self.server_manager.server_stopped.connect(on_stopped)
    timer.timeout.connect(loop.quit)

    try:
        timer.start(timeout)
        loop.exec()
    finally:
        # [Fix: Disconnect signals]
        try:
            self.server_manager.server_stopped.disconnect(on_stopped)
            timer.timeout.disconnect(loop.quit)
        except:
            pass # 忽略已断开的异常

    return stopped[0]

def _wait_for_server_start(self, timeout: int) -> bool:
    """
    等待服务启动
    [Fix: Signal connection management]
    """
    from PyQt6.QtCore import QEventLoop, QTimer

    loop = QEventLoop()
    timer = QTimer()
    timer.setSingleShot(True)

    result = [False]
    error_msg = [""]

    def on_started():
        result[0] = True
        loop.quit()

    def on_error(msg):
        result[0] = False
        error_msg[0] = msg
        loop.quit()

    # 连接信号
    self.server_manager.server_started.connect(on_started)
    self.server_manager.server_error.connect(on_error)
    timer.timeout.connect(loop.quit)

    try:
        timer.start(timeout)
        loop.exec()
    finally:
        # [Fix: Disconnect signals]
        try:
            self.server_manager.server_started.disconnect(on_started)
            self.server_manager.server_error.disconnect(on_error)
            timer.timeout.disconnect(loop.quit)
        except:
            pass

    if not result[0] and error_msg[0]:
        raise Exception(error_msg[0])

    return result[0]
```

#### 2.2.6 新增 show_cwd_history() 方法

```python
def show_cwd_history(self):
    """显示历史目录选择菜单"""
    from PyQt6.QtWidgets import QMenu
    from PyQt6.QtGui import QAction
    from pathlib import Path

    history = self.cwd_manager.get_history()

    if not history:
        QMessageBox.information(self, "No History", "暂无历史记录")
        return

    menu = QMenu(self)

    for path in history:
        # [Enhancement: Check if path exists]
        exists = Path(path).exists()
        label = path if exists else f"{path} (不存在)"

        action = QAction(label, self)
        action.setEnabled(exists)
        action.setToolTip(path)

        # 注意：lambda 需要捕获 path
        action.triggered.connect(lambda checked, p=path: self.switch_cwd(p))
        menu.addAction(action)

    # 显示在按钮下方
    menu.exec(self.cwd_history_btn.mapToGlobal(
        self.cwd_history_btn.rect().bottomLeft()
    ))
```

#### 2.2.7 修改 connect_signals()

```python
def connect_signals(self):
    # 现有信号
    self.cwd_browse_btn.clicked.connect(self.browse_cwd)
    self.start_btn.clicked.connect(self.toggle_server)
    self.inject_btn.clicked.connect(self.inject_config)

    # 新增信号
    self.cwd_history_btn.clicked.connect(self.show_cwd_history)

    # ServerManager signals
    self.server_manager.server_started.connect(self.on_server_started)
    self.server_manager.server_stopped.connect(self.on_server_stopped)
    self.server_manager.log_received.connect(self.append_log)
    self.server_manager.server_error.connect(self.on_server_error)
```

## 3. 数据模型

### 3.1 QSettings 键值结构

```python
# 现有键
"cwd": str  # 当前工作目录
"host": str  # 127.0.0.1 或 0.0.0.0
"port": int  # 端口号

# 新增键
"cwd_history": List[str]  # 历史目录列表（最新的在前，最多 10 条）
```

### 3.2 历史记录管理逻辑

```python
# 示例：切换到 3 个不同目录后的状态
cwd_history = [
    "/home/user/project3",  # 最新
    "/home/user/project2",
    "/home/user/project1"
]

# 再次切换到 project1，会移到最前
cwd_history = [
    "/home/user/project1",  # 移到最前
    "/home/user/project3",
    "/home/user/project2"
]
```

## 4. 交互流程

### 4.1 正常切换流程（服务运行中）

```
用户点击"Browse..." → 选择目录 → 确认
    ↓
validate_directory() → 验证通过
    ↓
禁用所有控制按钮
    ↓
显示 "Status: Stopping server..."
    ↓
ServerManager.stop_server()
    ↓
等待 server_stopped 信号（最多 5 秒）
    ↓
更新 cwd_input.setText()
    ↓
settings.setValue("cwd", new_path)
    ↓
cwd_manager.add_to_history()
    ↓
显示 "Status: Starting server..."
    ↓
ServerManager.start_server(host, port, new_cwd)
    ↓
等待 server_started 信号（最多 10 秒）
    ↓
显示成功提示
    ↓
恢复按钮状态
```

### 4.2 错误处理流程

```
启动失败（server_error 信号）
    ↓
捕获异常
    ↓
回滚 cwd_input 和 settings
    ↓
显示错误提示
    ↓
尝试恢复到原目录（best effort）
    ↓
恢复按钮状态
```

## 5. 错误处理策略

| 错误场景 | 检测时机 | 处理方式 | 用户反馈 |
|---------|---------|---------|---------|
| 目录不存在 | validate_directory() | 拒绝切换 | 错误对话框 |
| 权限不足 | validate_directory() | 拒绝切换 | 错误对话框 |
| 停止超时 | _wait_for_server_stop() | 抛出异常，触发回滚 | 错误对话框 + 回滚 |
| 启动失败 | _wait_for_server_start() | 抛出异常，触发回滚 | 错误对话框 + 回滚 |
| 并发切换 | switch_cwd() 开头 | 拒绝操作 | 警告对话框 |

## 6. 性能考虑

| 项目 | 目标 | 实现方式 |
|------|------|---------|
| 目录验证 | < 100ms | 使用 Path.exists() + os.access() |
| 停止超时 | 5 秒 | QEventLoop + QTimer |
| 启动超时 | 10 秒 | QEventLoop + QTimer |
| 历史记录保存 | 即时 | 每次切换后立即 setValue() |
| UI 响应 | 无阻塞 | 使用信号-槽机制异步等待 |

## 7. 测试策略

### 7.1 单元测试

**测试文件**: `tests/unit/test_working_directory_manager.py`

```python
# 测试用例
- test_validate_directory_valid
- test_validate_directory_not_exists
- test_validate_directory_no_permission
- test_add_to_history_new
- test_add_to_history_duplicate
- test_add_to_history_max_limit
- test_save_load_settings
```

### 7.2 集成测试

**测试文件**: `tests/integration/test_cwd_switch.py`

```python
# 测试场景
- test_switch_cwd_server_stopped
- test_switch_cwd_server_running
- test_switch_cwd_invalid_directory
- test_switch_cwd_start_failure_rollback
- test_history_button_empty
- test_history_button_with_records
```

### 7.3 手动测试清单

参考 requirements.md 的功能验收清单（F-001 ~ F-012）

## 8. 兼容性和依赖

### 8.1 Python 版本
- 要求: Python 3.8+
- 理由: Path.resolve() 和类型提示

### 8.2 PyQt6 版本
- 要求: PyQt6 6.0+
- 理由: QSettings, QEventLoop, QMenu

### 8.3 操作系统
- Windows: 完全支持
- macOS: 完全支持
- Linux: 完全支持

## 9. 安全考虑

1. **路径注入防护**: 使用 Path.resolve() 规范化路径
2. **权限检查**: 使用 os.access() 检查 R_OK | W_OK
3. **并发保护**: _is_switching_cwd 标志防止重入
4. **错误回滚**: 确保失败后不留下不一致状态
5. **资源释放**: 确保 QEventLoop 和信号连接正确清理

## 10. 后续优化方向

1. **历史记录持久化增强**: 考虑添加"固定"功能，防止常用目录被挤出历史
2. **快速切换快捷键**: 添加键盘快捷键（如 Ctrl+H 打开历史）
3. **目录有效性缓存**: 避免重复验证相同目录
4. **异步验证**: 对于网络路径，使用后台线程验证

---

**最后更新**: 2026-01-21T10:15:00Z
**下一步**: 进入 Execution 阶段，按任务组顺序实施
