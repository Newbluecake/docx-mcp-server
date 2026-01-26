---
feature: launcher-command-display
complexity: standard
version: 1
generated_at: 2026-01-26T05:45:00Z
total_tasks: 8
---

# 任务拆分文档: Launcher Command Display

> **功能标识**: launcher-command-display
> **复杂度**: standard
> **生成时间**: 2026-01-26T05:45:00Z
> **任务总数**: 8

## 任务概览

| ID | 标题 | 优先级 | 依赖 | 预计工作量 | 类型 |
|----|------|--------|------|-----------|------|
| T-001 | 移除 CLI Parameters Group UI 代码 | P0 | - | 1h | 重构 |
| T-002 | 添加命令显示框和复制按钮 UI | P0 | T-001 | 1h | 新增 |
| T-003 | 实现命令生成和实时更新逻辑 | P0 | T-002 | 1h | 新增 |
| T-004 | 实现复制到剪贴板功能 | P0 | T-002 | 0.5h | 新增 |
| T-005 | 更新信号连接和初始化逻辑 | P0 | T-003, T-004 | 0.5h | 修改 |
| T-006 | 更新翻译和样式 | P1 | T-002 | 0.5h | 修改 |
| T-007 | 单元测试和 GUI 测试 | P0 | T-001~T-005 | 2h | 测试 |
| T-008 | 文档更新 | P1 | T-007 | 1h | 文档 |

**并行分组**:
- **Group 1** (串行): T-001 → T-002 → T-003, T-004 (并行) → T-005
- **Group 2** (并行): T-006 (可与 Group 1 并行)
- **Group 3** (串行): T-007 → T-008

---

## 任务详情

### T-001: 移除 CLI Parameters Group UI 代码

**优先级**: P0
**类型**: 重构
**预计工作量**: 1 小时
**依赖**: 无

#### 描述

移除 Integration Section 中的 CLI Parameters Group 及其所有子控件，包括 --model、--agent、--verbose、--debug 的配置项和启动按钮。

#### 验收标准

- [ ] 移除 `cli_params_group` (QGroupBox) 及其布局
- [ ] 移除 `model_checkbox`、`model_combo` 控件
- [ ] 移除 `agent_checkbox`、`agent_input` 控件
- [ ] 移除 `verbose_checkbox`、`debug_checkbox` 控件
- [ ] 移除 `launch_btn` (QPushButton)
- [ ] 移除 `launch_claude()` 方法
- [ ] 移除相关的信号连接代码
- [ ] 移除相关的配置保存/加载代码 (load_settings/save_settings)
- [ ] 代码编译通过，无语法错误

#### 实施步骤

1. **定位代码位置**
   - 文件: `src/docx_server_launcher/gui/main_window.py`
   - 方法: `init_ui()` (约 182-237 行)

2. **移除 UI 创建代码**
   ```python
   # 删除以下代码块 (约 182-237 行)
   cli_params_group = QGroupBox()
   cli_params_group.setObjectName("cli_params_group")
   # ... 所有子控件创建代码 ...
   integration_layout.addWidget(cli_params_group)

   # 删除启动按钮 (约 236-237 行)
   self.launch_btn = QPushButton()
   integration_layout.addWidget(self.launch_btn)
   ```

3. **移除信号连接**
   - 在 `connect_signals()` 方法中删除:
     ```python
     # 删除这些行
     self.model_checkbox.stateChanged.connect(...)
     self.agent_checkbox.stateChanged.connect(...)
     self.launch_btn.clicked.connect(self.launch_claude)
     ```

4. **移除方法**
   - 删除 `launch_claude()` 方法 (如存在)

5. **移除配置持久化**
   - 在 `load_settings()` 中删除:
     ```python
     # 删除这些配置加载
     self.model_checkbox.setChecked(...)
     self.agent_checkbox.setChecked(...)
     ```
   - 在 `save_settings()` 中删除对应的保存代码

6. **移除翻译**
   - 在 `retranslateUi()` 中删除相关控件的翻译代码

#### 测试要点

- 启动 launcher，确认 Integration Section 不再显示 CLI Parameters Group
- 确认没有 AttributeError (访问已删除的控件)
- 确认配置文件不再保存旧的配置项

#### 注意事项

- **保留** `cli_params_input` (Additional Parameters 输入框)
- **保留** `hint_label` (提示文字，但需要更新内容)
- 确保删除所有对已移除控件的引用，避免运行时错误

---

### T-002: 添加命令显示框和复制按钮 UI

**优先级**: P0
**类型**: 新增
**预计工作量**: 1 小时
**依赖**: T-001

#### 描述

在 Integration Section 中添加命令显示框 (QLineEdit, readonly) 和复制按钮 (QPushButton)，用于显示和复制 Claude CLI 启动命令。

#### 验收标准

- [ ] 添加 `command_display` (QLineEdit) 控件
  - 设置为只读 (`setReadOnly(True)`)
  - 设置占位符文本 ("Command will appear here...")
  - 设置背景色为浅灰色 (`#f5f5f5`)
- [ ] 添加 `copy_btn` (QPushButton) 控件
  - 文字为 "Copy Command"
  - 最大宽度为 120px
- [ ] 使用 QHBoxLayout 水平排列两个控件
- [ ] 更新 `hint_label` 的文字为新的提示内容
- [ ] UI 布局美观，控件对齐正确

#### 实施步骤

1. **在 `init_ui()` 中添加控件**
   ```python
   # 在 Integration Section 中添加 (约 178 行之后)
   self.integration_group = QGroupBox()
   integration_layout = QVBoxLayout()

   # 新增: 命令显示区域
   command_layout = QHBoxLayout()

   self.command_display = QLineEdit()
   self.command_display.setReadOnly(True)
   self.command_display.setPlaceholderText("Command will appear here...")
   self.command_display.setStyleSheet("background-color: #f5f5f5;")
   command_layout.addWidget(self.command_display)

   self.copy_btn = QPushButton("Copy Command")
   self.copy_btn.setMaximumWidth(120)
   command_layout.addWidget(self.copy_btn)

   integration_layout.addLayout(command_layout)
   ```

2. **更新 hint_label**
   ```python
   # 更新提示文字
   hint_label = QLabel("Add custom parameters below (e.g., --dangerously-skip-permission)")
   hint_label.setObjectName("cli_params_hint")
   integration_layout.addWidget(hint_label)
   ```

3. **保留 Additional Parameters 输入框**
   ```python
   # 保持不变
   self.cli_params_input = QLineEdit()
   self.cli_params_input.setPlaceholderText("e.g., --dangerously-skip-permission")
   integration_layout.addWidget(self.cli_params_input)
   ```

4. **完成布局**
   ```python
   self.integration_group.setLayout(integration_layout)
   main_layout.addWidget(self.integration_group)
   ```

#### 测试要点

- 启动 launcher，确认命令显示框和复制按钮正确显示
- 确认命令显示框为只读（无法编辑）
- 确认复制按钮宽度合适，不会过宽
- 确认提示文字已更新

#### 注意事项

- 命令显示框应占据大部分宽度，复制按钮固定宽度
- 背景色 `#f5f5f5` 用于区分只读状态
- 占位符文本应清晰提示用户

---

### T-003: 实现命令生成和实时更新逻辑

**优先级**: P0
**类型**: 新增
**预计工作量**: 1 小时
**依赖**: T-002

#### 描述

实现 `update_command_display()` 方法，根据当前配置（host、port、extra_params）生成完整的 Claude CLI 命令，并在配置变更时实时更新。

#### 验收标准

- [ ] 实现 `update_command_display()` 方法
- [ ] 实现 `_do_update_command_display()` 方法（防抖优化）
- [ ] 命令格式正确（包含 --mcp-config 和 JSON 配置）
- [ ] Windows 平台包含 `cmd.exe /c` 前缀
- [ ] Linux/Mac 平台不包含 `cmd.exe /c`
- [ ] 错误处理：命令生成失败时显示错误信息
- [ ] 防抖机制：用户停止输入 300ms 后才更新

#### 实施步骤

1. **添加防抖定时器**
   ```python
   def __init__(self):
       # ... 其他初始化 ...
       self._update_timer = QTimer()
       self._update_timer.setSingleShot(True)
       self._update_timer.timeout.connect(self._do_update_command_display)
   ```

2. **实现防抖入口方法**
   ```python
   def update_command_display(self) -> None:
       """延迟更新命令显示（防抖）"""
       self._update_timer.stop()
       self._update_timer.start(300)  # 300ms 延迟
   ```

3. **实现实际更新逻辑**
   ```python
   def _do_update_command_display(self) -> None:
       """实际执行命令更新"""
       try:
           # 1. 获取配置
           host = "0.0.0.0" if self.lan_checkbox.isChecked() else "127.0.0.1"
           port = self.port_input.value()
           extra_params = self.cli_params_input.text().strip()

           # 2. 生成 MCP 配置
           server_url = f"http://{host}:{port}/sse"
           mcp_config = self.cli_launcher.generate_mcp_config(server_url, "sse")

           # 3. 构建命令
           cmd_list = self.cli_launcher.build_command(mcp_config, extra_params)

           # 4. 格式化为字符串
           cmd_str = ' '.join(cmd_list)

           # 5. 更新显示
           self.command_display.setText(cmd_str)

       except Exception as e:
           self.command_display.setText(f"Error: {str(e)}")
   ```

#### 测试要点

- 修改端口号，确认命令中的端口立即更新
- 勾选 LAN 访问，确认 host 变为 `0.0.0.0`
- 输入自定义参数，确认附加到命令末尾
- 快速输入参数，确认防抖生效（不会频繁更新）
- 在 Windows 上测试，确认包含 `cmd.exe /c`
- 在 Linux/Mac 上测试，确认不包含 `cmd.exe /c`

#### 注意事项

- 使用 `cli_launcher.generate_mcp_config()` 和 `build_command()` 复用现有逻辑
- 防抖延迟设置为 300ms，平衡响应速度和性能
- 错误信息应清晰，便于用户排查问题

---

### T-004: 实现复制到剪贴板功能

**优先级**: P0
**类型**: 新增
**预计工作量**: 0.5 小时
**依赖**: T-002

#### 描述

实现 `copy_command()` 方法，将命令显示框的文本复制到剪贴板，并提供视觉反馈（按钮文字变化）。

#### 验收标准

- [ ] 实现 `copy_command()` 方法
- [ ] 实现 `_reset_copy_button()` 辅助方法
- [ ] 复制成功后，按钮文字变为 "Copied!"
- [ ] 2 秒后按钮文字恢复为 "Copy Command"
- [ ] 复制期间按钮禁用，防止重复点击
- [ ] 错误处理：剪贴板操作失败时显示错误消息框
- [ ] 边界情况：命令为空或错误时，显示警告

#### 实施步骤

1. **实现复制方法**
   ```python
   def copy_command(self) -> None:
       """复制命令到剪贴板并提供视觉反馈"""
       try:
           cmd = self.command_display.text()

           # 边界检查
           if not cmd or cmd.startswith("Error:"):
               QMessageBox.warning(
                   self,
                   "Copy Failed",
                   "No valid command to copy."
               )
               return

           # 复制到剪贴板
           clipboard = QApplication.clipboard()
           clipboard.setText(cmd)

           # 视觉反馈
           original_text = self.copy_btn.text()
           self.copy_btn.setText("Copied!")
           self.copy_btn.setEnabled(False)

           # 2 秒后恢复
           QTimer.singleShot(2000, lambda: self._reset_copy_button(original_text))

       except Exception as e:
           QMessageBox.critical(
               self,
               "Copy Error",
               f"Failed to copy command: {str(e)}"
           )
   ```

2. **实现恢复方法**
   ```python
   def _reset_copy_button(self, original_text: str) -> None:
       """恢复复制按钮状态"""
       self.copy_btn.setText(original_text)
       self.copy_btn.setEnabled(True)
   ```

#### 测试要点

- 点击复制按钮，确认剪贴板包含完整命令
- 确认按钮文字变为 "Copied!"
- 确认 2 秒后按钮文字恢复
- 确认复制期间按钮禁用
- 测试边界情况：命令为空时显示警告
- 测试边界情况：命令为错误信息时显示警告

#### 注意事项

- 使用 `QApplication.clipboard()` 访问系统剪贴板
- 使用 `QTimer.singleShot()` 实现延迟恢复
- 错误消息框应使用 `QMessageBox.critical()` 或 `warning()`

---

### T-005: 更新信号连接和初始化逻辑

**优先级**: P0
**类型**: 修改
**预计工作量**: 0.5 小时
**依赖**: T-003, T-004

#### 描述

更新 `connect_signals()` 方法，连接新增的信号（复制按钮点击、配置变更），并在 `__init__()` 中调用 `update_command_display()` 进行初始化。

#### 验收标准

- [ ] 连接 `copy_btn.clicked` 信号到 `copy_command` 槽
- [ ] 连接 `port_input.valueChanged` 信号到 `update_command_display` 槽
- [ ] 连接 `lan_checkbox.stateChanged` 信号到 `update_command_display` 槽
- [ ] 连接 `cli_params_input.textChanged` 信号到 `update_command_display` 槽
- [ ] 在 `__init__()` 末尾调用 `update_command_display()` 进行初始化
- [ ] 移除已删除控件的信号连接（如 `launch_btn`）

#### 实施步骤

1. **在 `connect_signals()` 中添加信号连接**
   ```python
   def connect_signals(self):
       # ... 前面的代码保持不变 ...

       # 移除: self.launch_btn.clicked.connect(self.launch_claude)

       # 新增: 复制按钮
       self.copy_btn.clicked.connect(self.copy_command)

       # 新增: 实时更新命令显示
       self.port_input.valueChanged.connect(self.update_command_display)
       self.lan_checkbox.stateChanged.connect(self.update_command_display)
       self.cli_params_input.textChanged.connect(self.update_command_display)

       # ... 后面的代码保持不变 ...
   ```

2. **在 `__init__()` 中初始化命令显示**
   ```python
   def __init__(self):
       # ... 前面的代码保持不变 ...

       # Initial translation
       self.retranslateUi()

       # 新增: 初始化命令显示
       self.update_command_display()
   ```

#### 测试要点

- 启动 launcher，确认命令框立即显示默认命令
- 修改端口号，确认命令实时更新
- 勾选 LAN 访问，确认命令实时更新
- 输入自定义参数，确认命令实时更新
- 点击复制按钮，确认复制功能正常

#### 注意事项

- 确保所有信号连接在 `load_settings()` 之前，避免触发不必要的更新
- 初始化调用 `update_command_display()` 应在 `load_settings()` 之后

---

### T-006: 更新翻译和样式

**优先级**: P1
**类型**: 修改
**预计工作量**: 0.5 小时
**依赖**: T-002

#### 描述

更新 `retranslateUi()` 方法中的翻译文本，移除已删除控件的翻译，添加新增控件的翻译。

#### 验收标准

- [ ] 更新 `integration_group` 的标题翻译
- [ ] 添加 `command_display` 的占位符翻译
- [ ] 添加 `copy_btn` 的文字翻译
- [ ] 移除已删除控件的翻译（model_checkbox、agent_checkbox 等）
- [ ] 确认所有文本支持国际化（使用 `self.tr()`）

#### 实施步骤

1. **在 `retranslateUi()` 中更新翻译**
   ```python
   def retranslateUi(self):
       # ... 前面的代码保持不变 ...

       # Integration Section
       self.integration_group.setTitle(self.tr("Claude Integration"))
       self.command_display.setPlaceholderText(self.tr("Command will appear here..."))
       self.copy_btn.setText(self.tr("Copy Command"))

       # 移除以下翻译代码（已删除的控件）:
       # self.model_checkbox.setText(...)
       # self.agent_checkbox.setText(...)
       # self.verbose_checkbox.setText(...)
       # self.debug_checkbox.setText(...)
       # self.launch_btn.setText(...)

       # ... 后面的代码保持不变 ...
   ```

2. **更新 hint_label 的翻译**
   ```python
   # 在 init_ui() 中，确保使用 self.tr()
   hint_label = QLabel(self.tr("Add custom parameters below (e.g., --dangerously-skip-permission)"))
   ```

3. **更新复制反馈的翻译**
   ```python
   # 在 copy_command() 中使用 self.tr()
   self.copy_btn.setText(self.tr("Copied!"))

   # 在 _reset_copy_button() 中
   self.copy_btn.setText(self.tr("Copy Command"))
   ```

#### 测试要点

- 切换语言，确认所有文本正确翻译
- 确认没有遗留的已删除控件的翻译
- 确认新增控件的翻译完整

#### 注意事项

- 所有用户可见的文本都应使用 `self.tr()` 包裹
- 如果项目使用翻译文件 (.ts/.qm)，需要运行 `pylupdate` 更新翻译

---

### T-007: 单元测试和 GUI 测试

**优先级**: P0
**类型**: 测试
**预计工作量**: 2 小时
**依赖**: T-001~T-005

#### 描述

编写单元测试和 GUI 集成测试，验证命令生成、复制功能、实时更新等核心功能。

#### 验收标准

- [ ] 单元测试覆盖命令生成逻辑
- [ ] 单元测试覆盖复制功能
- [ ] GUI 测试覆盖实时更新
- [ ] GUI 测试覆盖跨平台兼容性 (Windows/Linux)
- [ ] 测试覆盖率 > 80%
- [ ] 所有测试通过

#### 实施步骤

1. **创建单元测试文件**
   - 文件: `tests/unit/test_command_display.py`

2. **编写命令生成测试**
   ```python
   import pytest
   from docx_server_launcher.core.cli_launcher import CLILauncher

   def test_command_generation_default():
       launcher = CLILauncher()
       mcp_config = launcher.generate_mcp_config("http://127.0.0.1:8000/sse", "sse")
       cmd = launcher.build_command(mcp_config, "")
       assert "claude" in cmd
       assert "--mcp-config" in cmd

   def test_command_generation_with_params():
       launcher = CLILauncher()
       mcp_config = launcher.generate_mcp_config("http://127.0.0.1:8000/sse", "sse")
       cmd = launcher.build_command(mcp_config, "--dangerously-skip-permission")
       assert "--dangerously-skip-permission" in cmd

   def test_command_generation_lan():
       launcher = CLILauncher()
       mcp_config = launcher.generate_mcp_config("http://0.0.0.0:8000/sse", "sse")
       cmd = launcher.build_command(mcp_config, "")
       cmd_str = ' '.join(cmd)
       assert "0.0.0.0" in cmd_str
   ```

3. **编写 GUI 测试文件**
   - 文件: `tests/integration/test_gui_command_display.py`

4. **编写 GUI 测试用例**
   ```python
   import pytest
   from PyQt6.QtWidgets import QApplication
   from docx_server_launcher.gui.main_window import MainWindow

   @pytest.fixture
   def app(qtbot):
       window = MainWindow()
       qtbot.addWidget(window)
       return window

   def test_command_display_initial(app):
       # 确认命令框显示默认命令
       cmd = app.command_display.text()
       assert "claude" in cmd
       assert "127.0.0.1" in cmd

   def test_command_update_on_port_change(app):
       # 修改端口号
       app.port_input.setValue(9000)
       # 等待防抖
       QTimer.singleShot(500, lambda: None)
       # 确认命令更新
       cmd = app.command_display.text()
       assert "9000" in cmd

   def test_copy_command(app, qtbot):
       # 点击复制按钮
       qtbot.mouseClick(app.copy_btn, Qt.MouseButton.LeftButton)
       # 确认剪贴板内容
       clipboard = QApplication.clipboard()
       assert clipboard.text() == app.command_display.text()
       # 确认按钮反馈
       assert app.copy_btn.text() == "Copied!"
   ```

5. **运行测试**
   ```bash
   QT_QPA_PLATFORM=offscreen uv run pytest tests/unit/test_command_display.py
   QT_QPA_PLATFORM=offscreen uv run pytest tests/integration/test_gui_command_display.py
   ```

#### 测试要点

- 测试命令格式正确性
- 测试跨平台兼容性（Windows cmd.exe 前缀）
- 测试实时更新机制
- 测试复制功能和按钮反馈
- 测试边界情况（空命令、错误命令）

#### 注意事项

- GUI 测试需要使用 `pytest-qt` 插件
- Linux 环境需要设置 `QT_QPA_PLATFORM=offscreen`
- 测试文件应遵循项目现有的测试结构

---

### T-008: 文档更新

**优先级**: P1
**类型**: 文档
**预计工作量**: 1 小时
**依赖**: T-007

#### 描述

更新项目文档，说明新的交互方式和配置变更，包括 README.md、CHANGELOG.md 等。

#### 验收标准

- [ ] 更新 `README.md` 的 "Claude Integration" 章节
- [ ] 添加 `CHANGELOG.md` 条目（版本 v2.x）
- [ ] 更新使用说明（如存在 `docs/usage.md`）
- [ ] 添加迁移指南（从旧版本升级）
- [ ] 文档格式正确，无拼写错误

#### 实施步骤

1. **更新 README.md**
   ```markdown
   ## Claude Integration

   **New in v2.x**: The launcher now displays the full Claude CLI command instead of auto-launching. This improves reliability and flexibility.

   ### Usage

   1. Configure your server settings (host, port)
   2. Add custom CLI parameters if needed (e.g., `--dangerously-skip-permission`)
   3. Click "Copy Command" to copy the full command to your clipboard
   4. Paste and execute the command in your terminal

   ### Example Command

   **Linux/Mac**:
   ```bash
   claude --mcp-config {"mcpServers":{"docx-server":{"url":"http://127.0.0.1:8000/sse","transport":"sse"}}} --dangerously-skip-permission
   ```

   **Windows**:
   ```cmd
   cmd.exe /c claude --mcp-config {"mcpServers":{"docx-server":{"url":"http://127.0.0.1:8000/sse","transport":"sse"}}} --dangerously-skip-permission
   ```
   ```

2. **更新 CHANGELOG.md**
   ```markdown
   ## [2.0.0] - 2026-01-26

   ### Changed
   - **Breaking**: Removed auto-launch functionality in favor of manual command execution
   - Replaced "Launch Claude" button with command display and copy functionality
   - Simplified CLI parameters configuration (removed --model, --agent, --verbose, --debug UI)

   ### Added
   - Command display box showing the full Claude CLI command
   - "Copy Command" button for easy clipboard copying
   - Real-time command updates when configuration changes

   ### Migration Guide
   - If you previously used `--model` or `--agent` parameters, add them manually to the "Additional Parameters" field
   - The command is no longer executed automatically - you need to copy and run it in your terminal
   ```

3. **添加迁移指南**
   - 创建 `docs/migration-v2.md`（如需要）
   - 说明配置迁移方法

#### 测试要点

- 确认文档链接正确
- 确认示例命令可以正常执行
- 确认迁移指南清晰易懂

#### 注意事项

- 文档应清晰说明为什么做此变更（提高可靠性）
- 提供清晰的迁移路径，避免用户困惑

---

## 任务依赖关系图

```
T-001 (移除 CLI Parameters Group)
  ↓
T-002 (添加命令显示框)
  ├──→ T-003 (命令生成逻辑)
  ├──→ T-004 (复制功能)
  └──→ T-006 (翻译和样式) [可并行]
  ↓
T-005 (信号连接)
  ↓
T-007 (测试)
  ↓
T-008 (文档)
```

---

## 并行分组建议

### Group 1: 核心功能 (串行)
- T-001 → T-002 → (T-003 + T-004 并行) → T-005

### Group 2: 样式和翻译 (可与 Group 1 部分并行)
- T-006 (依赖 T-002，可与 T-003/T-004 并行)

### Group 3: 质量保证 (串行)
- T-007 → T-008

**总预计工作量**: 7.5 小时
**并行执行预计**: 5-6 小时

---

## 验收清单

### 功能验收

- [ ] F-001: 命令框显示 - Integration Section 显示只读命令框
- [ ] F-002: 复制按钮功能 - 点击复制按钮，剪贴板包含完整命令
- [ ] F-003: 命令格式正确 - 包含 `claude --mcp-config` 和正确的 JSON
- [ ] F-004: 实时更新 - 修改配置后命令立即更新
- [ ] F-005: 简化配置 - 移除 model/agent/verbose/debug 配置
- [ ] F-006: 复制反馈 - 按钮文字变为 "Copied!"，2秒后恢复

### 质量验收

- [ ] 所有单元测试通过
- [ ] 所有 GUI 测试通过
- [ ] 测试覆盖率 > 80%
- [ ] 代码符合项目规范
- [ ] 文档完整且准确

### 跨平台验收

- [ ] Windows 上命令包含 `cmd.exe /c`
- [ ] Linux 上命令不包含 `cmd.exe /c`
- [ ] Mac 上命令不包含 `cmd.exe /c`

---

**文档版本**: v1
**最后更新**: 2026-01-26
**作者**: Claude Sonnet 4.5 (via architect-planner)
