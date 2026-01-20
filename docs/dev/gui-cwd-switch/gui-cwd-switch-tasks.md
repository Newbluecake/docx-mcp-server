---
feature: gui-cwd-switch
stage: 3
generated_at: 2026-01-21T09:55:00Z
version: 1
total_tasks: 6
estimated_hours: 8
---

# 任务拆分文档: GUI 工作目录切换与服务重启

> **功能标识**: gui-cwd-switch
> **复杂度**: standard
> **生成时间**: 2026-01-21T09:55:00Z

## 任务概览

| 任务 ID | 任务名称 | 优先级 | 预估时间 | 依赖 | 可并行组 |
|---------|---------|--------|---------|------|---------|
| T-001 | 实现 WorkingDirectoryManager 核心类 | P0 | 2h | 无 | Group-1 |
| T-002 | 添加 UI 组件（历史按钮） | P0 | 1h | 无 | Group-1 |
| T-003 | 实现工作目录切换逻辑（switch_cwd） | P0 | 2.5h | T-001 | Group-2 |
| T-004 | 实现历史记录展示（show_cwd_history） | P1 | 1h | T-001 | Group-2 |
| T-005 | 添加单元测试 | P0 | 1h | T-001 | Group-3 |
| T-006 | 添加集成测试 | P1 | 0.5h | T-003 | Group-3 |

**并行分组说明**:
- **Group-1**: T-001 和 T-002 可并行（分别处理后端和前端）
- **Group-2**: T-003 和 T-004 依赖 T-001，但彼此独立
- **Group-3**: 测试任务，可在实现完成后并行

---

## 任务详细说明

### T-001: 实现 WorkingDirectoryManager 核心类

**优先级**: P0
**预估时间**: 2 小时
**依赖**: 无
**可并行组**: Group-1

#### 任务描述

创建 `WorkingDirectoryManager` 类，负责工作目录的验证、历史记录管理和配置持久化。

#### 验收标准

1. 创建文件 `src/docx_server_launcher/core/working_directory_manager.py`
2. 实现以下方法:
   - `__init__(settings: QSettings)`
   - `validate_directory(path: str) -> Tuple[bool, str]`
   - `add_to_history(path: str)`
   - `get_history() -> List[str]`
   - `save_settings()`
   - `load_settings()`
3. 验证逻辑包含:
   - 路径存在性检查
   - 目录类型检查
   - 读写权限检查
4. 历史记录逻辑:
   - 去重（移到首位）
   - 限制 10 条
   - 路径规范化（使用 Path.resolve()）

#### 技术要点

```python
from pathlib import Path
from typing import List, Tuple
import os
from PyQt6.QtCore import QSettings

class WorkingDirectoryManager:
    MAX_HISTORY = 10

    def validate_directory(self, path: str) -> Tuple[bool, str]:
        # 关键检查
        if not path:
            return False, "目录路径为空"

        p = Path(path)
        if not p.exists():
            return False, f"目录不存在: {path}"

        if not p.is_dir():
            return False, f"路径不是目录: {path}"

        if not os.access(path, os.R_OK | os.W_OK):
            return False, f"权限不足，无法访问: {path}"

        return True, ""
```

#### TDD 步骤

1. 编写测试 `test_validate_directory_valid` (RED)
2. 实现 `validate_directory()` 基本逻辑 (GREEN)
3. 重构优化错误消息 (REFACTOR)
4. 编写测试 `test_add_to_history_new` (RED)
5. 实现 `add_to_history()` (GREEN)
6. 编写测试 `test_add_to_history_duplicate` (RED)
7. 实现去重逻辑 (GREEN)
8. 编写测试 `test_add_to_history_max_limit` (RED)
9. 实现限制逻辑 (GREEN)

#### 关联需求

- R-001: 工作目录选择
- R-005: 错误处理
- R-006: 配置持久化
- R-007: 历史目录记录

---

### T-002: 添加 UI 组件（历史按钮）

**优先级**: P0
**预估时间**: 1 小时
**依赖**: 无
**可并行组**: Group-1

#### 任务描述

在 MainWindow 的工作目录配置区域添加"Recent"历史记录按钮。

#### 验收标准

1. 在 `init_ui()` 方法中添加 `self.cwd_history_btn`
2. 按钮文字为 "Recent ▼"
3. 按钮最大宽度 100 像素
4. 布局位置：Browse 按钮右侧
5. 在 `connect_signals()` 中连接点击事件（先设置占位处理器）

#### 技术要点

```python
# 在 init_ui() 的 cwd_layout 部分
self.cwd_history_btn = QPushButton("Recent ▼")
self.cwd_history_btn.setMaximumWidth(100)
cwd_layout.addWidget(self.cwd_history_btn)

# 在 connect_signals()
self.cwd_history_btn.clicked.connect(self.show_cwd_history)

# 临时占位方法
def show_cwd_history(self):
    QMessageBox.information(self, "TODO", "历史记录功能待实现")
```

#### TDD 步骤

1. 运行 GUI，确认按钮显示正确
2. 点击按钮，确认占位提示出现
3. 检查按钮在服务运行时是否正确禁用（依赖后续任务）

#### 关联需求

- R-007: 历史目录记录

---

### T-003: 实现工作目录切换逻辑（switch_cwd）

**优先级**: P0
**预估时间**: 2.5 小时
**依赖**: T-001
**可并行组**: Group-2

#### 任务描述

实现核心方法 `switch_cwd()`，处理工作目录切换和服务重启的完整流程。

#### 验收标准

1. 实现以下方法:
   - `switch_cwd(new_path: str)`
   - `_disable_controls()`
   - `_enable_controls()`
   - `_wait_for_server_stop(timeout: int) -> bool`
   - `_wait_for_server_start(timeout: int) -> bool`
2. 功能验证:
   - 目录验证失败时拒绝切换
   - 服务运行时触发停止-启动流程
   - 服务停止时仅更新配置
   - 切换失败时回滚到原目录
   - 并发切换时拒绝操作
3. UI 反馈:
   - 停止时显示 "Status: Stopping server..."
   - 启动时显示 "Status: Starting server..."
   - 成功时弹出确认对话框
   - 失败时弹出错误对话框并回滚
4. 按钮状态:
   - 切换期间所有控制按钮禁用
   - 完成后根据服务状态恢复
5. 修改 `browse_cwd()` 调用 `switch_cwd()`

#### 技术要点

```python
def switch_cwd(self, new_path: str):
    # 防并发
    if self._is_switching_cwd:
        QMessageBox.warning(self, "Warning", "工作目录切换正在进行中...")
        return

    # 验证
    is_valid, error_msg = self.cwd_manager.validate_directory(new_path)
    if not is_valid:
        QMessageBox.critical(self, "Invalid Directory", error_msg)
        return

    # 规范化
    normalized_path = str(Path(new_path).resolve())
    current_path = self.cwd_input.text() or os.getcwd()

    # 检查重复
    if normalized_path == str(Path(current_path).resolve()):
        return

    original_cwd = current_path
    is_server_running = (self.start_btn.text() == "Stop Server")

    self._is_switching_cwd = True

    try:
        if is_server_running:
            # 停止服务
            self.status_label.setText("Status: Stopping server...")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
            self._disable_controls()

            self.server_manager.stop_server()

            if not self._wait_for_server_stop(timeout=5000):
                raise Exception("服务停止超时")

        # 更新配置
        self.cwd_input.setText(normalized_path)
        self.settings.setValue("cwd", normalized_path)
        self.cwd_manager.add_to_history(normalized_path)

        if is_server_running:
            # 启动服务
            self.status_label.setText("Status: Starting server...")
            host = "0.0.0.0" if self.lan_checkbox.isChecked() else "127.0.0.1"
            port = self.port_input.value()

            self.server_manager.start_server(host, port, normalized_path)

            if not self._wait_for_server_start(timeout=10000):
                raise Exception("服务启动失败")

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

        QMessageBox.critical(
            self,
            "Error",
            f"切换失败: {str(e)}\n已回滚到原目录"
        )

        # 尝试恢复服务
        if is_server_running:
            try:
                host = "0.0.0.0" if self.lan_checkbox.isChecked() else "127.0.0.1"
                port = self.port_input.value()
                self.server_manager.start_server(host, port, original_cwd)
            except:
                pass

    finally:
        self._is_switching_cwd = False
        self._enable_controls()
```

#### TDD 步骤

1. 编写测试 `test_switch_cwd_server_stopped` (RED)
2. 实现基本切换逻辑（服务停止状态）(GREEN)
3. 编写测试 `test_switch_cwd_server_running` (RED)
4. 实现服务重启逻辑 (GREEN)
5. 编写测试 `test_switch_cwd_invalid_directory` (RED)
6. 添加验证逻辑 (GREEN)
7. 编写测试 `test_switch_cwd_start_failure_rollback` (RED)
8. 实现回滚机制 (GREEN)
9. 重构提取辅助方法 (REFACTOR)

#### 关联需求

- R-001: 工作目录选择
- R-002: 自动重启服务
- R-003: 当前目录显示
- R-004: 重启进度提示
- R-005: 错误处理
- R-006: 配置持久化

---

### T-004: 实现历史记录展示（show_cwd_history）

**优先级**: P1
**预估时间**: 1 小时
**依赖**: T-001
**可并行组**: Group-2

#### 任务描述

实现 `show_cwd_history()` 方法，展示历史目录选择菜单。

#### 验收标准

1. 实现 `show_cwd_history()` 方法
2. 历史记录为空时显示提示对话框
3. 有历史记录时显示下拉菜单
4. 菜单位置：按钮正下方
5. 点击菜单项调用 `switch_cwd()`
6. 在 `__init__()` 中初始化 `self.cwd_manager`

#### 技术要点

```python
def show_cwd_history(self):
    from PyQt6.QtWidgets import QMenu
    from PyQt6.QtGui import QAction

    history = self.cwd_manager.get_history()

    if not history:
        QMessageBox.information(self, "No History", "暂无历史记录")
        return

    menu = QMenu(self)

    for path in history:
        action = QAction(path, self)
        # 注意：lambda 需要捕获 path
        action.triggered.connect(lambda checked, p=path: self.switch_cwd(p))
        menu.addAction(action)

    # 显示在按钮下方
    menu.exec(self.cwd_history_btn.mapToGlobal(
        self.cwd_history_btn.rect().bottomLeft()
    ))
```

#### TDD 步骤

1. 手动测试：无历史记录时点击按钮
2. 手动测试：添加 2 条历史后点击按钮
3. 手动测试：从菜单选择目录，确认切换成功

#### 关联需求

- R-007: 历史目录记录

---

### T-005: 添加单元测试

**优先级**: P0
**预估时间**: 1 小时
**依赖**: T-001
**可并行组**: Group-3

#### 任务描述

为 `WorkingDirectoryManager` 类添加完整的单元测试。

#### 验收标准

1. 创建文件 `tests/unit/test_working_directory_manager.py`
2. 实现以下测试用例:
   - `test_validate_directory_valid`: 有效目录
   - `test_validate_directory_not_exists`: 不存在的目录
   - `test_validate_directory_not_a_directory`: 文件路径
   - `test_validate_directory_no_permission`: 权限不足（可选，需 mock）
   - `test_add_to_history_new`: 添加新目录
   - `test_add_to_history_duplicate`: 添加重复目录
   - `test_add_to_history_max_limit`: 超过 10 条限制
   - `test_save_load_settings`: 持久化
3. 测试覆盖率 > 90%
4. 所有测试通过

#### 技术要点

```python
import pytest
import tempfile
from pathlib import Path
from PyQt6.QtCore import QSettings
from docx_server_launcher.core.working_directory_manager import WorkingDirectoryManager

def test_validate_directory_valid():
    settings = QSettings("TestOrg", "TestApp")
    manager = WorkingDirectoryManager(settings)

    with tempfile.TemporaryDirectory() as tmpdir:
        is_valid, error = manager.validate_directory(tmpdir)
        assert is_valid is True
        assert error == ""

def test_validate_directory_not_exists():
    settings = QSettings("TestOrg", "TestApp")
    manager = WorkingDirectoryManager(settings)

    is_valid, error = manager.validate_directory("/nonexistent/path")
    assert is_valid is False
    assert "不存在" in error

def test_add_to_history_duplicate():
    settings = QSettings("TestOrg", "TestApp")
    manager = WorkingDirectoryManager(settings)

    with tempfile.TemporaryDirectory() as tmpdir:
        manager.add_to_history(tmpdir)
        manager.add_to_history(tmpdir)

        history = manager.get_history()
        assert len(history) == 1
        assert history[0] == str(Path(tmpdir).resolve())

def test_add_to_history_max_limit():
    settings = QSettings("TestOrg", "TestApp")
    manager = WorkingDirectoryManager(settings)

    with tempfile.TemporaryDirectory() as tmpdir:
        # 添加 12 个不同目录（通过子目录模拟）
        for i in range(12):
            subdir = Path(tmpdir) / f"dir{i}"
            subdir.mkdir()
            manager.add_to_history(str(subdir))

        history = manager.get_history()
        assert len(history) == 10
        assert str(Path(tmpdir) / "dir11") in history[0]
```

#### 运行命令

```bash
pytest tests/unit/test_working_directory_manager.py -v
```

#### 关联需求

- R-001, R-005, R-006, R-007（通过测试验证）

---

### T-006: 添加集成测试

**优先级**: P1
**预估时间**: 0.5 小时
**依赖**: T-003
**可并行组**: Group-3

#### 任务描述

为完整的切换流程添加集成测试（可选，优先级较低）。

#### 验收标准

1. 创建文件 `tests/integration/test_cwd_switch.py`
2. 实现以下测试场景:
   - `test_switch_cwd_server_stopped`: 服务停止状态下切换
   - `test_switch_cwd_server_running`: 服务运行状态下切换（需 mock ServerManager）
   - `test_history_integration`: 历史记录端到端测试
3. 所有测试通过

#### 技术要点

```python
import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication
from docx_server_launcher.gui.main_window import MainWindow

@pytest.fixture
def app():
    return QApplication([])

def test_switch_cwd_server_stopped(app):
    window = MainWindow()

    with tempfile.TemporaryDirectory() as tmpdir:
        window.switch_cwd(tmpdir)

        assert window.cwd_input.text() == str(Path(tmpdir).resolve())
        assert tmpdir in window.cwd_manager.get_history()
```

#### 运行命令

```bash
pytest tests/integration/test_cwd_switch.py -v
```

#### 关联需求

- F-001 ~ F-012（功能验收清单）

---

## 实施顺序建议

### 第一轮（Group-1）: 并行开发
- **开发者 A**: T-001（后端逻辑）
- **开发者 B**: T-002（UI 组件）

### 第二轮（Group-2）: 依赖 T-001
- **开发者 A**: T-003（核心切换逻辑）
- **开发者 B**: T-004（历史记录 UI）

### 第三轮（Group-3）: 测试验证
- **开发者 A**: T-005（单元测试）
- **开发者 B**: T-006（集成测试）

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| QEventLoop 阻塞 UI | 中 | 设置合理超时（5秒/10秒） |
| 跨平台权限检查差异 | 中 | 在 Windows/macOS/Linux 手动测试 |
| 服务启动失败难以模拟 | 低 | 使用 mock 和手动测试结合 |
| 历史记录路径过长 | 低 | UI 使用 tooltip 显示完整路径 |

---

## 验收检查清单

参考 requirements.md 的功能验收清单（F-001 ~ F-012），所有项目需标记为通过。

---

**最后更新**: 2026-01-21T09:55:00Z
**下一步**: 进入 Execution 阶段，按任务组顺序实施
