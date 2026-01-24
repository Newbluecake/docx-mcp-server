---
feature: launcher-cli-mode
version: 1.0
created_at: 2026-01-24T10:45:00Z
total_tasks: 12
estimated_duration: 8-12 hours
---

# Task Breakdown: GUI Launcher CLI Mode

> **Feature**: launcher-cli-mode
> **Complexity**: standard
> **Total Tasks**: 12
> **Parallel Groups**: 3

## Task Overview

| ID | Title | Priority | Complexity | Dependencies | Group |
|----|-------|----------|------------|--------------|-------|
| T-001 | Create CLILauncher core module | P0 | standard | - | G1 |
| T-002 | Implement Claude CLI detection | P0 | simple | T-001 | G1 |
| T-003 | Implement MCP config generation | P0 | simple | T-001 | G1 |
| T-004 | Implement CLI command builder | P0 | standard | T-001, T-003 | G1 |
| T-005 | Implement launch process manager | P0 | standard | T-001, T-004 | G1 |
| T-006 | Implement launch logging | P1 | simple | T-001 | G2 |
| T-007 | Add security validation | P0 | standard | T-004 | G2 |
| T-008 | Update MainWindow UI | P0 | standard | T-001 | G2 |
| T-009 | Integrate CLILauncher with UI | P0 | simple | T-005, T-008 | G3 |
| T-010 | Add error dialogs | P0 | simple | T-009 | G3 |
| T-011 | Update translations | P1 | simple | T-008 | G3 |
| T-012 | Add integration tests | P1 | standard | T-009 | G3 |

## Parallel Execution Groups

### Group 1: Core Module (Sequential)
Tasks T-001 → T-002, T-003 → T-004 → T-005

**Rationale**: Core module must be built sequentially as each task depends on previous

**Estimated Time**: 4-5 hours

### Group 2: Security & UI (Parallel after G1)
Tasks T-006, T-007, T-008 (can run in parallel)

**Rationale**: These tasks are independent and can be developed simultaneously

**Estimated Time**: 2-3 hours

### Group 3: Integration & Testing (Sequential after G2)
Tasks T-009 → T-010, T-011, T-012

**Rationale**: Integration must complete before testing

**Estimated Time**: 2-4 hours

---

## Task Details

### T-001: Create CLILauncher Core Module

**Priority**: P0
**Complexity**: standard
**Estimated Time**: 1 hour
**Dependencies**: None

**Description**:
Create the new `CLILauncher` class in `src/docx_server_launcher/core/cli_launcher.py` with basic structure and initialization.

**Implementation Steps**:
1. Create file `src/docx_server_launcher/core/cli_launcher.py`
2. Define `CLILauncher` class with `__init__` method
3. Add log directory initialization (`~/.docx-launcher`)
4. Add log file path setup (`launch.log`)
5. Implement `_ensure_log_dir()` helper method
6. Add type hints and docstrings

**Acceptance Criteria**:
- [ ] File `cli_launcher.py` created in correct location
- [ ] `CLILauncher` class defined with proper structure
- [ ] Log directory created on initialization
- [ ] All methods have type hints and docstrings
- [ ] Unit test: `test_cli_launcher_init()` passes

**Test Cases**:
```python
def test_cli_launcher_init():
    launcher = CLILauncher()
    assert launcher.log_dir.exists()
    assert launcher.log_file.name == "launch.log"
```

---

### T-002: Implement Claude CLI Detection

**Priority**: P0
**Complexity**: simple
**Estimated Time**: 30 minutes
**Dependencies**: T-001

**Description**:
Implement `is_claude_cli_available()` method to detect if Claude CLI is installed using `shutil.which()`.

**Implementation Steps**:
1. Import `shutil` module
2. Implement `is_claude_cli_available()` method
3. Use `shutil.which("claude")` to detect CLI
4. Return tuple of (is_available, path_or_error_message)
5. Add caching mechanism (5-minute TTL)

**Acceptance Criteria**:
- [ ] Method returns `(True, path)` when CLI found
- [ ] Method returns `(False, error_msg)` when CLI not found
- [ ] Caching works correctly (subsequent calls use cache)
- [ ] Unit test: `test_is_claude_cli_available_found()` passes
- [ ] Unit test: `test_is_claude_cli_available_not_found()` passes

**Test Cases**:
```python
def test_is_claude_cli_available_found(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/claude")
    launcher = CLILauncher()
    is_available, path = launcher.is_claude_cli_available()
    assert is_available is True
    assert path == "/usr/bin/claude"

def test_is_claude_cli_available_not_found(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda x: None)
    launcher = CLILauncher()
    is_available, msg = launcher.is_claude_cli_available()
    assert is_available is False
    assert "not found" in msg.lower()
```

---

### T-003: Implement MCP Config Generation

**Priority**: P0
**Complexity**: simple
**Estimated Time**: 30 minutes
**Dependencies**: T-001

**Description**:
Implement `generate_mcp_config()` method to create MCP configuration dictionary from server settings.

**Implementation Steps**:
1. Implement `generate_mcp_config(server_url, transport)` method
2. Create nested dictionary structure: `{"mcpServers": {"docx-server": {...}}}`
3. Set `url` and `transport` fields
4. Add validation for transport type (sse, streamable-http)
5. Raise error for unsupported STDIO transport

**Acceptance Criteria**:
- [ ] Method returns correct dict structure for SSE transport
- [ ] Method returns correct dict structure for HTTP transport
- [ ] Method raises ValueError for STDIO transport
- [ ] Unit test: `test_generate_mcp_config_sse()` passes
- [ ] Unit test: `test_generate_mcp_config_http()` passes
- [ ] Unit test: `test_generate_mcp_config_stdio_error()` passes

**Test Cases**:
```python
def test_generate_mcp_config_sse():
    launcher = CLILauncher()
    config = launcher.generate_mcp_config("http://127.0.0.1:8000/sse", "sse")
    assert config == {
        "mcpServers": {
            "docx-server": {
                "url": "http://127.0.0.1:8000/sse",
                "transport": "sse"
            }
        }
    }

def test_generate_mcp_config_stdio_error():
    launcher = CLILauncher()
    with pytest.raises(ValueError, match="STDIO.*not supported"):
        launcher.generate_mcp_config("", "stdio")
```

---

### T-004: Implement CLI Command Builder

**Priority**: P0
**Complexity**: standard
**Estimated Time**: 1 hour
**Dependencies**: T-001, T-003

**Description**:
Implement `build_command()` method to construct Claude CLI command with MCP config and extra parameters.

**Implementation Steps**:
1. Import `json` and `shlex` modules
2. Implement `build_command(mcp_config, extra_params)` method
3. Build base command: `["claude", "--mcp-config", json.dumps(mcp_config)]`
4. Parse `extra_params` using `shlex.split()`
5. Extend command with parsed params
6. Handle empty `extra_params` gracefully

**Acceptance Criteria**:
- [ ] Method returns list of command arguments
- [ ] MCP config is JSON-serialized correctly
- [ ] Extra params are parsed with `shlex.split()`
- [ ] Empty extra params handled correctly
- [ ] Unit test: `test_build_command_no_params()` passes
- [ ] Unit test: `test_build_command_with_params()` passes
- [ ] Unit test: `test_build_command_quoted_params()` passes

**Test Cases**:
```python
def test_build_command_no_params():
    launcher = CLILauncher()
    config = {"mcpServers": {"docx-server": {"url": "http://127.0.0.1:8000/sse", "transport": "sse"}}}
    cmd = launcher.build_command(config, "")
    assert cmd == ["claude", "--mcp-config", json.dumps(config)]

def test_build_command_with_params():
    launcher = CLILauncher()
    config = {"mcpServers": {"docx-server": {"url": "http://127.0.0.1:8000/sse", "transport": "sse"}}}
    cmd = launcher.build_command(config, "--model opus --agent reviewer")
    assert cmd == ["claude", "--mcp-config", json.dumps(config), "--model", "opus", "--agent", "reviewer"]

def test_build_command_quoted_params():
    launcher = CLILauncher()
    config = {"mcpServers": {"docx-server": {"url": "http://127.0.0.1:8000/sse", "transport": "sse"}}}
    cmd = launcher.build_command(config, '--prompt "Hello World"')
    assert cmd == ["claude", "--mcp-config", json.dumps(config), "--prompt", "Hello World"]
```

---

### T-005: Implement Launch Process Manager

**Priority**: P0
**Complexity**: standard
**Estimated Time**: 1.5 hours
**Dependencies**: T-001, T-004

**Description**:
Implement `launch()` method to spawn Claude CLI process using `subprocess.Popen`.

**Implementation Steps**:
1. Import `subprocess` module
2. Implement `launch(server_url, transport, extra_params)` method
3. Call `is_claude_cli_available()` to check CLI
4. Generate MCP config using `generate_mcp_config()`
5. Build command using `build_command()`
6. Spawn process with `subprocess.Popen(cmd, stdout=PIPE, stderr=PIPE)`
7. Return tuple of (success, message_or_error)
8. Handle exceptions and return error messages

**Acceptance Criteria**:
- [ ] Method checks CLI availability before launch
- [ ] Method spawns process using `subprocess.Popen`
- [ ] Process is non-blocking (doesn't wait for completion)
- [ ] Method returns `(True, success_msg)` on success
- [ ] Method returns `(False, error_msg)` on failure
- [ ] Unit test: `test_launch_success()` passes (with mock)
- [ ] Unit test: `test_launch_cli_not_found()` passes
- [ ] Unit test: `test_launch_process_error()` passes

**Test Cases**:
```python
def test_launch_success(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/claude")
    monkeypatch.setattr("subprocess.Popen", lambda *args, **kwargs: MockProcess())
    launcher = CLILauncher()
    success, msg = launcher.launch("http://127.0.0.1:8000/sse", "sse", "")
    assert success is True
    assert "started" in msg.lower()

def test_launch_cli_not_found(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda x: None)
    launcher = CLILauncher()
    success, msg = launcher.launch("http://127.0.0.1:8000/sse", "sse", "")
    assert success is False
    assert "not found" in msg.lower()
```

---

### T-006: Implement Launch Logging

**Priority**: P1
**Complexity**: simple
**Estimated Time**: 45 minutes
**Dependencies**: T-001

**Description**:
Implement `_log_launch()` method to write launch details to log file with rotation.

**Implementation Steps**:
1. Import `logging` and `logging.handlers` modules
2. Set up `RotatingFileHandler` (10MB max, 3 backups)
3. Implement `_log_launch(command, mcp_config, success, error)` method
4. Log timestamp, command, MCP config, result
5. Call `_log_launch()` from `launch()` method
6. Set file permissions to 0600 (owner read/write only)

**Acceptance Criteria**:
- [ ] Log file created at `~/.docx-launcher/launch.log`
- [ ] Log entries include timestamp, command, config, result
- [ ] Log rotation works (max 10MB, 3 backups)
- [ ] File permissions set to 0600
- [ ] Unit test: `test_log_launch_success()` passes
- [ ] Unit test: `test_log_rotation()` passes

**Test Cases**:
```python
def test_log_launch_success(tmp_path):
    launcher = CLILauncher(log_dir=str(tmp_path))
    cmd = ["claude", "--mcp-config", "{}"]
    config = {"mcpServers": {}}
    launcher._log_launch(cmd, config, True, "")
    log_content = (tmp_path / "launch.log").read_text()
    assert "INFO" in log_content
    assert "claude" in log_content
    assert "started successfully" in log_content
```

---

### T-007: Add Security Validation

**Priority**: P0
**Complexity**: standard
**Estimated Time**: 1 hour
**Dependencies**: T-004

**Description**:
Implement `validate_cli_params()` and `sanitize_for_log()` methods for security.

**Implementation Steps**:
1. Implement `validate_cli_params(params)` method
2. Check for dangerous shell metacharacters (`;`, `&`, `|`, etc.)
3. Try parsing with `shlex.split()` to catch syntax errors
4. Return tuple of (is_valid, error_message)
5. Implement `sanitize_for_log(params)` method
6. Redact sensitive data (e.g., `--api-key [REDACTED]`)
7. Call validation in `launch()` before building command

**Acceptance Criteria**:
- [ ] Validation rejects dangerous characters
- [ ] Validation catches `shlex` parse errors
- [ ] Sanitization redacts API keys
- [ ] Launch method calls validation before proceeding
- [ ] Unit test: `test_validate_cli_params_safe()` passes
- [ ] Unit test: `test_validate_cli_params_dangerous()` passes
- [ ] Unit test: `test_sanitize_for_log()` passes

**Test Cases**:
```python
def test_validate_cli_params_safe():
    launcher = CLILauncher()
    is_valid, msg = launcher.validate_cli_params("--model opus --agent reviewer")
    assert is_valid is True

def test_validate_cli_params_dangerous():
    launcher = CLILauncher()
    is_valid, msg = launcher.validate_cli_params("--model opus; rm -rf /")
    assert is_valid is False
    assert ";" in msg

def test_sanitize_for_log():
    launcher = CLILauncher()
    sanitized = launcher.sanitize_for_log("--api-key sk-1234567890 --model opus")
    assert "sk-1234567890" not in sanitized
    assert "[REDACTED]" in sanitized
```

---

### T-008: Update MainWindow UI

**Priority**: P0
**Complexity**: standard
**Estimated Time**: 1.5 hours
**Dependencies**: T-001

**Description**:
Modify `MainWindow` class to replace config injection UI with CLI launch UI.

**Implementation Steps**:
1. Remove config path input and browse button from UI
2. Add `cli_params_input` (QLineEdit) for extra CLI parameters
3. Add hint label above input ("e.g., --model opus --agent reviewer")
4. Rename `inject_btn` to `launch_btn`
5. Update button text to "Launch Claude"
6. Add "View Launch Log" button in status bar
7. Update `load_settings()` to load `cli/extra_params`
8. Update `save_settings()` to save `cli/extra_params`

**Acceptance Criteria**:
- [ ] Config path input removed from UI
- [ ] CLI params input added with placeholder text
- [ ] Launch button text updated
- [ ] View log button added
- [ ] Settings persistence works for CLI params
- [ ] UI layout matches design mockup
- [ ] Manual test: UI displays correctly

**UI Code**:
```python
# In init_ui(), Integration Section
self.integration_group = QGroupBox()
integration_layout = QVBoxLayout()

# Hint label
hint_label = QLabel("Extra CLI Parameters (optional):")
hint_label.setToolTip("e.g., --model opus --agent reviewer")
integration_layout.addWidget(hint_label)

# CLI params input
self.cli_params_input = QLineEdit()
self.cli_params_input.setPlaceholderText("e.g., --model opus --agent reviewer")
integration_layout.addWidget(self.cli_params_input)

# Launch button
self.launch_btn = QPushButton("Launch Claude")
integration_layout.addWidget(self.launch_btn)

self.integration_group.setLayout(integration_layout)
```

---

### T-009: Integrate CLILauncher with UI

**Priority**: P0
**Complexity**: simple
**Estimated Time**: 45 minutes
**Dependencies**: T-005, T-008

**Description**:
Connect `launch_btn` to `launch_claude()` method that uses `CLILauncher`.

**Implementation Steps**:
1. Import `CLILauncher` in `main_window.py`
2. Initialize `self.cli_launcher = CLILauncher()` in `__init__`
3. Implement `launch_claude()` method
4. Get server URL from current settings (host, port)
5. Get extra params from `cli_params_input.text()`
6. Call `cli_launcher.launch(server_url, "sse", extra_params)`
7. Show success/error message based on result
8. Connect `launch_btn.clicked` to `launch_claude()`
9. Save CLI params to settings after successful launch

**Acceptance Criteria**:
- [ ] `CLILauncher` instance created in MainWindow
- [ ] `launch_claude()` method implemented
- [ ] Button click triggers launch
- [ ] Success message shown on successful launch
- [ ] Error message shown on failure
- [ ] CLI params saved to settings
- [ ] Integration test: `test_launch_button_click()` passes

**Implementation**:
```python
def launch_claude(self):
    """Launch Claude CLI with MCP configuration."""
    # Get settings
    host = "127.0.0.1"  # Always use localhost for CLI
    port = self.port_input.value()
    server_url = f"http://{host}:{port}/sse"
    extra_params = self.cli_params_input.text().strip()

    # Launch
    success, msg = self.cli_launcher.launch(server_url, "sse", extra_params)

    if success:
        QMessageBox.information(self, "Success", msg)
        self.save_settings()  # Save CLI params
    else:
        QMessageBox.critical(self, "Error", msg)
```

---

### T-010: Add Error Dialogs

**Priority**: P0
**Complexity**: simple
**Estimated Time**: 30 minutes
**Dependencies**: T-009

**Description**:
Implement specialized error dialogs for common failure scenarios.

**Implementation Steps**:
1. Implement `show_cli_not_found_dialog()` method
2. Add installation instructions (npm, pip)
3. Add "View Documentation" button (opens URL)
4. Implement `show_mcp_connection_warning()` method
5. Suggest starting MCP server first
6. Call appropriate dialog from `launch_claude()` based on error type

**Acceptance Criteria**:
- [ ] CLI not found dialog shows installation instructions
- [ ] MCP connection warning shows helpful message
- [ ] Dialogs have proper icons (Warning, Critical)
- [ ] "View Documentation" button opens correct URL
- [ ] Manual test: Dialogs display correctly

**Implementation**:
```python
def show_cli_not_found_dialog(self):
    msg = QMessageBox(self)
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setWindowTitle("Claude CLI Not Found")
    msg.setText("Claude CLI is required to use this feature.")
    msg.setInformativeText(
        "Installation Options:\n\n"
        "1. Using npm (recommended):\n"
        "   npm install -g @anthropic-ai/claude-code\n\n"
        "2. Using pip:\n"
        "   pip install claude-code\n\n"
        "After installation, restart this application."
    )
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.exec()
```

---

### T-011: Update Translations

**Priority**: P1
**Complexity**: simple
**Estimated Time**: 30 minutes
**Dependencies**: T-008

**Description**:
Update translation files for new UI elements and messages.

**Implementation Steps**:
1. Update `retranslateUi()` method with new strings
2. Add translations for "Launch Claude" button
3. Add translations for "Extra CLI Parameters" label
4. Add translations for error messages
5. Update Chinese translation file (if exists)
6. Test language switching

**Acceptance Criteria**:
- [ ] All new UI elements have translations
- [ ] Error messages have translations
- [ ] Language switching works correctly
- [ ] Manual test: Switch to Chinese, verify translations

**Translation Strings**:
```python
def retranslateUi(self):
    # ... existing translations ...

    # Integration
    self.integration_group.setTitle(self.tr("Claude Desktop Integration"))
    self.launch_btn.setText(self.tr("Launch Claude"))
    self.cli_params_input.setPlaceholderText(
        self.tr("e.g., --model opus --agent reviewer")
    )
```

---

### T-012: Add Integration Tests

**Priority**: P1
**Complexity**: standard
**Estimated Time**: 1.5 hours
**Dependencies**: T-009

**Description**:
Create integration tests for end-to-end CLI launch workflow.

**Implementation Steps**:
1. Create `tests/integration/test_cli_launch.py`
2. Test: Launch with mock Claude CLI
3. Test: Launch log file creation
4. Test: Launch log rotation
5. Test: UI button click triggers launch
6. Test: Error handling (CLI not found, invalid params)
7. Use `pytest-qt` for UI testing

**Acceptance Criteria**:
- [ ] Integration test file created
- [ ] All test cases pass
- [ ] Test coverage > 80% for CLILauncher
- [ ] Test coverage > 70% for MainWindow launch code
- [ ] CI pipeline runs tests successfully

**Test Cases**:
```python
def test_launch_with_mock_cli(qtbot, monkeypatch):
    """Test launching Claude CLI with mocked subprocess."""
    monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/claude")
    monkeypatch.setattr("subprocess.Popen", lambda *args, **kwargs: MockProcess())

    window = MainWindow()
    qtbot.addWidget(window)

    window.cli_params_input.setText("--model opus")
    qtbot.mouseClick(window.launch_btn, Qt.MouseButton.LeftButton)

    # Verify success message shown
    # (Check QMessageBox or log output)

def test_launch_log_creation(tmp_path):
    """Test that launch log file is created."""
    launcher = CLILauncher(log_dir=str(tmp_path))
    # ... perform launch ...
    assert (tmp_path / "launch.log").exists()
```

---

## Risk Assessment

### High Risk Tasks
- **T-005** (Launch Process Manager): Complex subprocess handling, potential for race conditions
- **T-007** (Security Validation): Critical for preventing command injection

### Medium Risk Tasks
- **T-009** (UI Integration): Integration points can have unexpected interactions
- **T-012** (Integration Tests): Mocking subprocess can be tricky

### Low Risk Tasks
- **T-002**, **T-003**, **T-006**, **T-010**, **T-011**: Straightforward implementations

## Mitigation Strategies

1. **T-005 Risk**: Use extensive unit tests with mocked subprocess, test error paths
2. **T-007 Risk**: Follow OWASP guidelines, use whitelist approach for validation
3. **T-009 Risk**: Test with real MCP server running, verify all code paths
4. **T-012 Risk**: Use pytest-qt fixtures, test in isolated environment

---

**Document Version**: 1.0
**Last Updated**: 2026-01-24
**Status**: Ready for Implementation