---
feature: launcher-command-display
complexity: standard
version: 1
generated_at: 2026-01-26T05:45:00Z
---

# 技术设计文档: Launcher Command Display

> **功能标识**: launcher-command-display
> **复杂度**: standard
> **生成时间**: 2026-01-26T05:45:00Z

## 1. 系统架构设计

### 1.1 架构概览

本功能采用 **UI 重构 + 逻辑简化** 的架构策略，移除自动启动功能，改为显示可复制的命令。

```
┌─────────────────────────────────────────────────────────┐
│                    MainWindow (GUI)                      │
├─────────────────────────────────────────────────────────┤
│  Integration Section (重构)                              │
│  ├── Command Display (QLineEdit, readonly)              │
│  ├── Copy Button (QPushButton)                          │
│  └── Additional Parameters (QLineEdit)                  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  CLILauncher (Core)                      │
├─────────────────────────────────────────────────────────┤
│  保留方法:                                               │
│  ├── generate_mcp_config()                              │
│  ├── build_command()                                    │
│  └── validate_cli_params()                              │
│                                                          │
│  移除方法:                                               │
│  └── launch() - 不再调用                                 │
└─────────────────────────────────────────────────────────┘
```

### 1.2 核心变更

| 组件 | 变更类型 | 说明 |
|------|---------|------|
| `main_window.py` | 重构 | 移除 CLI Parameters Group，添加命令显示框 |
| `cli_launcher.py` | 简化 | 保留命令生成逻辑，移除启动逻辑调用 |
| Integration Section | UI 重构 | 简化布局，移除复杂配置项 |

---

## 2. 组件设计

### 2.1 UI 组件设计

#### 2.1.1 Integration Section 重构

**移除的组件**:

```python
# 移除整个 CLI Parameters Group
cli_params_group = QGroupBox()  # 包含以下控件
├── model_checkbox (QCheckBox)
├── model_combo (QComboBox)
├── agent_checkbox (QCheckBox)
├── agent_input (QLineEdit)
├── verbose_checkbox (QCheckBox)
└── debug_checkbox (QCheckBox)

# 移除启动按钮
launch_btn = QPushButton("Launch Claude")
```

**新增的组件**:

```python
# 命令显示区域（水平布局）
command_layout = QHBoxLayout()
├── command_display (QLineEdit)
│   ├── setReadOnly(True)
│   ├── setPlaceholderText("Command will appear here...")
│   └── setStyleSheet("background-color: #f5f5f5;")
└── copy_btn (QPushButton)
    ├── setText("Copy Command")
    └── setMaximumWidth(120)

# 保留的组件
cli_params_input (QLineEdit)  # 自定义参数输入框
hint_label (QLabel)           # 提示文字（更新内容）
```

#### 2.1.2 布局对比

**原布局** (行数: ~60):
```
Integration Section
├── CLI Parameters Group (QGroupBox)
│   ├── Row 1: Model + Agent (QHBoxLayout)
│   │   ├── --model [checkbox] [combo]
│   │   └── --agent [checkbox] [input]
│   └── Row 2: Boolean flags (QHBoxLayout)
│       ├── --verbose [checkbox]
│       └── --debug [checkbox]
├── Hint Label
├── Additional Parameters [input]
└── Launch Claude [button]
```

**新布局** (行数: ~20):
```
Integration Section
├── Command Display Row (QHBoxLayout)
│   ├── Command Display [readonly input]
│   └── Copy Command [button]
├── Hint Label (updated)
└── Additional Parameters [input]
```

**代码行数减少**: ~40 行 (约 67% 减少)

---

### 2.2 核心逻辑设计

#### 2.2.1 命令生成流程

```
用户修改配置 (端口/主机/参数)
    ↓
触发信号 (valueChanged/textChanged)
    ↓
调用 update_command_display()
    ↓
┌─────────────────────────────────────┐
│ 1. 获取当前配置                      │
│    - host (从 lan_checkbox 推导)    │
│    - port (从 port_input 获取)      │
│    - extra_params (从 cli_params_input 获取) │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 2. 生成 MCP 配置                     │
│    server_url = f"http://{host}:{port}/sse" │
│    mcp_config = cli_launcher.generate_mcp_config(server_url, "sse") │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 3. 构建命令                          │
│    cmd_list = cli_launcher.build_command(mcp_config, extra_params) │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 4. 格式化为字符串                    │
│    - Windows: 保留 cmd.exe /c 前缀  │
│    - Linux/Mac: 移除列表格式         │
│    cmd_str = ' '.join(cmd_list)     │
└─────────────────────────────────────┘
    ↓
更新 command_display.setText(cmd_str)
```

#### 2.2.2 复制功能流程

```
用户点击 Copy Command 按钮
    ↓
调用 copy_command()
    ↓
┌─────────────────────────────────────┐
│ 1. 获取命令文本                      │
│    cmd = command_display.text()     │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 2. 复制到剪贴板                      │
│    clipboard = QApplication.clipboard() │
│    clipboard.setText(cmd)           │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 3. 视觉反馈                          │
│    copy_btn.setText("Copied!")      │
│    QTimer.singleShot(2000, reset)   │
└─────────────────────────────────────┘
    ↓
2 秒后恢复按钮文字为 "Copy Command"
```

#### 2.2.3 实时更新机制

**信号连接**:

```python
# 在 connect_signals() 中添加
self.port_input.valueChanged.connect(self.update_command_display)
self.lan_checkbox.stateChanged.connect(self.update_command_display)
self.cli_params_input.textChanged.connect(self.update_command_display)

# 初始化时调用一次
self.update_command_display()
```

---

### 2.3 数据流设计

#### 2.3.1 配置 → 命令 数据流

```
┌─────────────────┐
│  UI 配置状态     │
├─────────────────┤
│ lan_checkbox    │ → host = "0.0.0.0" if checked else "127.0.0.1"
│ port_input      │ → port = 8000 (default)
│ cli_params_input│ → extra_params = "--dangerously-skip-permission"
└─────────────────┘
        ↓
┌─────────────────┐
│  MCP 配置        │
├─────────────────┤
│ server_url      │ = f"http://{host}:{port}/sse"
│ transport       │ = "sse"
└─────────────────┘
        ↓
┌─────────────────┐
│  命令列表        │
├─────────────────┤
│ ["claude",      │
│  "--mcp-config",│
│  "{...}",       │
│  "--dangerously-skip-permission"] │
└─────────────────┘
        ↓
┌─────────────────┐
│  显示字符串      │
├─────────────────┤
│ "claude --mcp-config {...} --dangerously-skip-permission" │
└─────────────────┘
```

---

## 3. 接口设计

### 3.1 新增方法

#### 3.1.1 MainWindow.update_command_display()

```python
def update_command_display(self) -> None:
    """
    更新命令显示框的内容。

    根据当前配置（host、port、extra_params）生成完整的 Claude CLI 命令。

    触发时机:
    - 端口号变更
    - LAN 访问开关变更
    - 自定义参数变更
    - 窗口初始化

    异常处理:
    - 如果命令生成失败，显示错误提示
    """
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

#### 3.1.2 MainWindow.copy_command()

```python
def copy_command(self) -> None:
    """
    复制命令到剪贴板并提供视觉反馈。

    功能:
    - 复制 command_display 的文本到剪贴板
    - 按钮文字变为 "Copied!"
    - 2 秒后恢复为 "Copy Command"

    异常处理:
    - 如果剪贴板操作失败，显示错误消息框
    """
    try:
        cmd = self.command_display.text()

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

def _reset_copy_button(self, original_text: str) -> None:
    """恢复复制按钮状态"""
    self.copy_btn.setText(original_text)
    self.copy_btn.setEnabled(True)
```

### 3.2 修改的方法

#### 3.2.1 MainWindow.init_ui()

**变更点**:
- 移除 CLI Parameters Group 的创建代码 (约 40 行)
- 添加命令显示区域的创建代码 (约 15 行)
- 更新 hint_label 的文字

**伪代码**:
```python
def init_ui(self):
    # ... 前面的代码保持不变 ...

    # --- Integration Section ---
    self.integration_group = QGroupBox()
    integration_layout = QVBoxLayout()

    # 新增: 命令显示区域
    command_layout = QHBoxLayout()
    self.command_display = QLineEdit()
    self.command_display.setReadOnly(True)
    self.command_display.setPlaceholderText("Command will appear here...")
    command_layout.addWidget(self.command_display)

    self.copy_btn = QPushButton("Copy Command")
    self.copy_btn.setMaximumWidth(120)
    command_layout.addWidget(self.copy_btn)

    integration_layout.addLayout(command_layout)

    # 保留: Hint label (更新文字)
    hint_label = QLabel("Add custom parameters below (e.g., --dangerously-skip-permission)")
    integration_layout.addWidget(hint_label)

    # 保留: Additional Parameters
    self.cli_params_input = QLineEdit()
    self.cli_params_input.setPlaceholderText("e.g., --dangerously-skip-permission")
    integration_layout.addWidget(self.cli_params_input)

    # 移除: launch_btn

    self.integration_group.setLayout(integration_layout)
    main_layout.addWidget(self.integration_group)

    # ... 后面的代码保持不变 ...
```

#### 3.2.2 MainWindow.connect_signals()

**变更点**:
- 移除 launch_btn 的信号连接
- 添加 copy_btn 的信号连接
- 添加配置变更的信号连接到 update_command_display

**伪代码**:
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

#### 3.2.3 MainWindow.retranslateUi()

**变更点**:
- 移除 CLI Parameters Group 相关的翻译
- 添加命令显示相关的翻译

**伪代码**:
```python
def retranslateUi(self):
    # ... 前面的代码保持不变 ...

    # Integration Section
    self.integration_group.setTitle(self.tr("Claude Integration"))
    self.command_display.setPlaceholderText(self.tr("Command will appear here..."))
    self.copy_btn.setText(self.tr("Copy Command"))

    # 移除: model_checkbox, agent_checkbox, verbose_checkbox, debug_checkbox 的翻译

    # ... 后面的代码保持不变 ...
```

### 3.3 移除的方法

```python
# 移除整个方法（不再需要）
def launch_claude(self) -> None:
    """启动 Claude CLI（已移除）"""
    pass
```

---

## 4. 数据设计

### 4.1 配置持久化

**保留的配置项**:
- `port`: 端口号 (QSettings)
- `lan_access`: LAN 访问开关 (QSettings)
- `cli_params`: 自定义参数 (QSettings)

**移除的配置项**:
- `cli_model`: --model 参数
- `cli_agent`: --agent 参数
- `cli_verbose`: --verbose 标志
- `cli_debug`: --debug 标志

**配置文件位置**: `~/.config/DocxMCP/Launcher.conf` (Linux/Mac) 或注册表 (Windows)

---

## 5. 安全设计

### 5.1 命令注入防护

**保留的安全机制**:
- `CLILauncher.validate_cli_params()`: 验证自定义参数，防止 shell 注入
- `CLILauncher.sanitize_for_log()`: 日志中隐藏敏感信息

**新增的安全考虑**:
- 命令显示框为只读，用户无法直接编辑
- 复制到剪贴板的命令经过验证

### 5.2 错误处理

| 场景 | 处理方式 |
|------|---------|
| 命令生成失败 | 在 command_display 显示 "Error: ..." |
| 剪贴板复制失败 | 显示错误消息框 |
| 参数验证失败 | 在 command_display 显示错误信息 |

---

## 6. 性能设计

### 6.1 实时更新优化

**问题**: 用户快速输入参数时，频繁触发命令更新可能导致 UI 卡顿。

**解决方案**: 使用防抖（Debounce）机制

```python
def __init__(self):
    # ... 其他初始化 ...
    self._update_timer = QTimer()
    self._update_timer.setSingleShot(True)
    self._update_timer.timeout.connect(self._do_update_command_display)

def update_command_display(self) -> None:
    """延迟更新命令显示（防抖）"""
    self._update_timer.stop()
    self._update_timer.start(300)  # 300ms 延迟

def _do_update_command_display(self) -> None:
    """实际执行命令更新"""
    # ... 原 update_command_display 的逻辑 ...
```

**效果**: 用户停止输入 300ms 后才更新命令，减少不必要的计算。

---

## 7. 测试设计

### 7.1 单元测试

**测试文件**: `tests/unit/test_command_display.py`

**测试用例**:

| 测试用例 | 输入 | 预期输出 |
|---------|------|---------|
| `test_command_generation_default` | host=127.0.0.1, port=8000, params="" | `claude --mcp-config {...}` |
| `test_command_generation_with_params` | host=127.0.0.1, port=8000, params="--dangerously-skip-permission" | `claude --mcp-config {...} --dangerously-skip-permission` |
| `test_command_generation_lan` | host=0.0.0.0, port=8000, params="" | `claude --mcp-config {"mcpServers":{"docx-server":{"url":"http://0.0.0.0:8000/sse",...}}}` |
| `test_command_update_on_port_change` | 修改端口为 9000 | 命令中端口更新为 9000 |
| `test_copy_command_success` | 点击复制按钮 | 剪贴板包含完整命令 |
| `test_copy_button_feedback` | 点击复制按钮 | 按钮文字变为 "Copied!"，2秒后恢复 |

### 7.2 GUI 测试

**测试文件**: `tests/integration/test_gui_command_display.py`

**测试场景**:
1. 启动 launcher，确认命令框显示默认命令
2. 修改端口号，确认命令实时更新
3. 勾选 LAN 访问，确认 host 变为 0.0.0.0
4. 输入自定义参数，确认附加到命令末尾
5. 点击复制按钮，确认剪贴板内容正确
6. 确认按钮反馈（"Copied!" → "Copy Command"）

---

## 8. 部署设计

### 8.1 向后兼容性

**配置迁移**:
- 旧版本的 `cli_model`、`cli_agent` 等配置项将被忽略
- 用户需要手动将这些参数添加到 "Additional Parameters" 输入框

**用户通知**:
- 在 CHANGELOG.md 中说明此变更
- 在 README.md 中更新使用说明

### 8.2 文档更新

**需要更新的文档**:
1. `README.md`: 更新 "Claude Integration" 章节
2. `CHANGELOG.md`: 添加 v2.x 版本说明
3. `docs/usage.md`: 更新使用指南（如存在）

---

## 9. 风险与缓解

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| JSON 转义问题 | 命令在终端执行失败 | 中 | 使用 `json.dumps()` 确保正确转义，添加单元测试验证 |
| 剪贴板权限 | 复制功能失败 | 低 | 捕获异常并显示错误提示 |
| 跨平台兼容性 | Windows/Linux/Mac 命令格式不同 | 低 | 复用现有 `build_command()` 的平台判断逻辑 |
| 用户习惯变更 | 用户不适应新的交互方式 | 中 | 在文档中清晰说明变更原因和使用方法 |

---

## 10. 实施计划

### 10.1 开发阶段

| 阶段 | 任务 | 预计工作量 |
|------|------|-----------|
| Phase 1 | 移除 CLI Parameters Group UI 代码 | 1 小时 |
| Phase 2 | 添加命令显示框和复制按钮 | 1 小时 |
| Phase 3 | 实现 update_command_display() 方法 | 1 小时 |
| Phase 4 | 实现 copy_command() 方法 | 0.5 小时 |
| Phase 5 | 连接信号和实时更新 | 0.5 小时 |
| Phase 6 | 更新翻译和样式 | 0.5 小时 |
| Phase 7 | 单元测试和 GUI 测试 | 2 小时 |
| Phase 8 | 文档更新 | 1 小时 |

**总计**: 约 7.5 小时

### 10.2 测试阶段

- 单元测试: 1 小时
- GUI 测试: 1 小时
- 跨平台测试 (Windows/Linux/Mac): 1 小时

**总计**: 约 3 小时

---

## 11. 附录

### 11.1 命令格式示例

**Linux/Mac**:
```bash
claude --mcp-config {"mcpServers":{"docx-server":{"url":"http://127.0.0.1:8000/sse","transport":"sse"}}} --dangerously-skip-permission
```

**Windows**:
```cmd
cmd.exe /c claude --mcp-config {"mcpServers":{"docx-server":{"url":"http://127.0.0.1:8000/sse","transport":"sse"}}} --dangerously-skip-permission
```

### 11.2 UI 截图（概念）

```
┌─────────────────────────────────────────────────────────┐
│ Claude Integration                                       │
├─────────────────────────────────────────────────────────┤
│ [claude --mcp-config {...}        ] [Copy Command]      │
│                                                          │
│ Add custom parameters below (e.g., --dangerously-skip-permission) │
│ [e.g., --dangerously-skip-permission                   ] │
└─────────────────────────────────────────────────────────┘
```

---

**文档版本**: v1
**最后更新**: 2026-01-26
**作者**: Claude Sonnet 4.5 (via architect-planner)
