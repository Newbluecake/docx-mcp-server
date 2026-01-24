---
feature: launcher-cli-mode
version: 1.0
created_at: 2026-01-24T10:40:00Z
status: draft
---

# Technical Design: GUI Launcher CLI Mode

> **Feature**: launcher-cli-mode
> **Complexity**: standard
> **Design Version**: 1.0

## 1. Architecture Overview

### 1.1 System Context

```
┌─────────────────────────────────────────────────────────┐
│                  User (Developer/Tester)                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│           docx-server-launcher (PyQt6 GUI)              │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Main Window  │  │ CLI Launcher │  │ Server Mgr   │  │
│  │  (UI Layer)  │→ │   (New)      │  │  (Existing)  │  │
│  └──────────────┘  └──────┬───────┘  └──────────────┘  │
└────────────────────────────┼────────────────────────────┘
                             │
                             ↓ subprocess.Popen
┌─────────────────────────────────────────────────────────┐
│              Claude CLI (External Process)               │
│  claude --mcp-config '{...}' [extra params]             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓ MCP Protocol (SSE/HTTP)
┌─────────────────────────────────────────────────────────┐
│           docx-mcp-server (Running Server)              │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Key Changes

| Component | Before | After |
|-----------|--------|-------|
| Main Button | "Inject Config to Claude..." | "Launch Claude" |
| Core Logic | ConfigInjector (file modification) | CLILauncher (process spawn) |
| UI Elements | Config path input + browse button | CLI params input field |
| Integration | Modify claude_desktop_config.json | Pass --mcp-config to CLI |

## 2. Component Design

### 2.1 New Component: CLILauncher

**Location**: `src/docx_server_launcher/core/cli_launcher.py`

**Responsibilities**:
- Detect Claude CLI installation
- Generate MCP configuration JSON
- Build and execute Claude CLI command
- Capture and log CLI output
- Handle launch errors

**Class Structure**:

```python
class CLILauncher:
    """Manages Claude CLI launching with MCP configuration."""

    def __init__(self, log_dir: str = "~/.docx-launcher"):
        """
        Initialize CLI launcher.

        Args:
            log_dir: Directory for launch logs
        """
        self.log_dir = Path(log_dir).expanduser()
        self.log_file = self.log_dir / "launch.log"
        self._ensure_log_dir()

    def is_claude_cli_available(self) -> Tuple[bool, str]:
        """
        Check if Claude CLI is installed.

        Returns:
            Tuple of (is_available, path_or_error_message)
        """

    def generate_mcp_config(self, server_url: str, transport: str) -> Dict[str, Any]:
        """
        Generate MCP configuration dictionary.

        Args:
            server_url: MCP server URL (e.g., http://127.0.0.1:8000/sse)
            transport: Transport type (sse, stdio, streamable-http)

        Returns:
            MCP configuration dictionary
        """

    def build_command(self, mcp_config: Dict[str, Any], extra_params: str = "") -> List[str]:
        """
        Build Claude CLI command with MCP config.

        Args:
            mcp_config: MCP configuration dictionary
            extra_params: Additional CLI parameters (e.g., "--model opus")

        Returns:
            Command as list of strings
        """

    def launch(self, server_url: str, transport: str, extra_params: str = "") -> Tuple[bool, str]:
        """
        Launch Claude CLI with MCP configuration.

        Args:
            server_url: MCP server URL
            transport: Transport type
            extra_params: Additional CLI parameters

        Returns:
            Tuple of (success, message_or_error)
        """

    def _log_launch(self, command: List[str], mcp_config: Dict[str, Any], success: bool, error: str = ""):
        """Log launch attempt to file."""
```

**Key Methods**:

1. **is_claude_cli_available()**: Uses `shutil.which("claude")` to detect CLI
2. **generate_mcp_config()**: Creates MCP config dict from server settings
3. **build_command()**: Constructs command list with proper escaping
4. **launch()**: Spawns Claude CLI process using subprocess.Popen
5. **_log_launch()**: Writes launch details to log file

### 2.2 Modified Component: MainWindow

**Location**: `src/docx_server_launcher/gui/main_window.py`

**Changes**:

1. **Remove**:
   - `self.config_injector` instance
   - `inject_config()` method
   - Config path input and browse button UI elements

2. **Add**:
   - `self.cli_launcher` instance (CLILauncher)
   - `self.cli_params_input` (QLineEdit for extra CLI parameters)
   - `launch_claude()` method (replaces inject_config)
   - "View Launch Log" button in status bar

3. **Modify**:
   - `inject_btn` → `launch_btn` (button text: "Launch Claude")
   - `inject_btn.clicked` → connect to `launch_claude()`

**New UI Layout**:

```python
# In init_ui(), Integration Section:
self.integration_group = QGroupBox()
integration_layout = QVBoxLayout()

# CLI params input
params_layout = QHBoxLayout()
params_label = QLabel("Extra CLI Parameters (optional):")
params_layout.addWidget(params_label)

self.cli_params_input = QLineEdit()
self.cli_params_input.setPlaceholderText("e.g., --model opus --agent reviewer")
params_layout.addWidget(self.cli_params_input)
integration_layout.addLayout(params_layout)

# Launch button
self.launch_btn = QPushButton("Launch Claude")
integration_layout.addWidget(self.launch_btn)

self.integration_group.setLayout(integration_layout)
```

### 2.3 Removed Component: ConfigInjector

**Status**: Deprecated (kept for backward compatibility, not used)

**Rationale**: CLI mode eliminates need for config file modification

## 3. Interface Design

### 3.1 UI Changes

#### Before (Config Injection Mode):
```
┌─────────────────────────────────────────┐
│  Claude Desktop Integration             │
├─────────────────────────────────────────┤
│  [Inject Config to Claude...]           │
└─────────────────────────────────────────┘
```

#### After (CLI Launch Mode):
```
┌─────────────────────────────────────────┐
│  Claude Desktop Integration             │
├─────────────────────────────────────────┤
│  Extra CLI Parameters (optional):       │
│  Hint: e.g., --model opus --agent rev   │
│  [_________________________________]     │
│                                          │
│  [Launch Claude]                         │
└─────────────────────────────────────────┘
```

### 3.2 CLI Integration Interface

**Command Format**:
```bash
claude --mcp-config '{"mcpServers":{"docx-server":{"url":"http://127.0.0.1:8000/sse","transport":"sse"}}}' [extra_params]
```

**Parameter Parsing**:
- Split `extra_params` by whitespace
- Preserve quoted strings (e.g., `--prompt "Hello World"`)
- Use `shlex.split()` for proper shell parsing

**Process Management**:
```python
import subprocess
import shlex

# Build command
cmd = ["claude", "--mcp-config", json.dumps(mcp_config)]
if extra_params:
    cmd.extend(shlex.split(extra_params))

# Launch (non-blocking)
process = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1  # Line buffered
)
```

## 4. Data Design

### 4.1 MCP Configuration JSON

**Structure**:
```json
{
  "mcpServers": {
    "docx-server": {
      "url": "http://127.0.0.1:8000/sse",
      "transport": "sse"
    }
  }
}
```

**Field Mapping**:
| GUI Setting | JSON Field | Example |
|-------------|------------|---------|
| Host (LAN checkbox) | url (host part) | 0.0.0.0 or 127.0.0.1 |
| Port | url (port part) | 8000 |
| Transport | transport | sse, stdio, streamable-http |

**URL Generation Logic**:
```python
def generate_server_url(host: str, port: int, transport: str) -> str:
    if transport == "sse":
        return f"http://{host}:{port}/sse"
    elif transport == "streamable-http":
        return f"http://{host}:{port}/mcp"
    else:  # stdio
        # STDIO mode not supported for CLI launch
        raise ValueError("STDIO transport not supported for CLI launch")
```

### 4.2 Launch Log Format

**File**: `~/.docx-launcher/launch.log`

**Format**:
```
[2026-01-24 10:45:00] INFO: ========== Launch Attempt ==========
[2026-01-24 10:45:00] INFO: Command: claude --mcp-config '{"mcpServers":{"docx-server":{"url":"http://127.0.0.1:8000/sse","transport":"sse"}}}' --model opus
[2026-01-24 10:45:00] INFO: MCP Config: {"mcpServers":{"docx-server":{"url":"http://127.0.0.1:8000/sse","transport":"sse"}}}
[2026-01-24 10:45:00] INFO: Extra Params: --model opus
[2026-01-24 10:45:01] INFO: Claude CLI started successfully (PID: 12345)
[2026-01-24 10:45:01] INFO: ========== End Launch ==========
```

**Log Rotation**:
- Max file size: 10 MB
- Keep last 3 log files (launch.log, launch.log.1, launch.log.2)
- Use Python's `logging.handlers.RotatingFileHandler`

### 4.3 QSettings Storage

**New Settings Keys**:
| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `cli/extra_params` | string | "" | Last used CLI parameters |
| `cli/last_launch_time` | string | "" | ISO timestamp of last launch |

## 5. Security Considerations

### 5.1 Command Injection Prevention

**Risk**: User-provided `extra_params` could contain malicious shell commands

**Mitigation**:
1. **Use subprocess with list arguments** (not shell=True)
   ```python
   # Safe: subprocess interprets as separate arguments
   subprocess.Popen(["claude", "--mcp-config", config, "--model", "opus"])

   # Unsafe: shell interprets special characters
   subprocess.Popen("claude --mcp-config ... --model opus", shell=True)
   ```

2. **Use shlex.split() for parsing**
   ```python
   import shlex
   # Properly handles quotes and escapes
   params = shlex.split(user_input)  # "--model opus" → ["--model", "opus"]
   ```

3. **Validate parameter format**
   ```python
   def validate_cli_params(params: str) -> Tuple[bool, str]:
       """Validate CLI parameters for safety."""
       # Check for shell metacharacters
       dangerous_chars = [";", "&", "|", "`", "$", "(", ")", "<", ">"]
       for char in dangerous_chars:
           if char in params:
               return False, f"Invalid character: {char}"

       # Try parsing
       try:
           shlex.split(params)
       except ValueError as e:
           return False, f"Parse error: {e}"

       return True, ""
   ```

### 5.2 Log File Security

**Risk**: Log files may contain sensitive information (API keys in params)

**Mitigation**:
1. **Sanitize logged parameters**
   ```python
   def sanitize_for_log(params: str) -> str:
       """Remove sensitive data from log output."""
       # Redact API keys
       params = re.sub(r'--api-key\s+\S+', '--api-key [REDACTED]', params)
       return params
   ```

2. **Set restrictive file permissions**
   ```python
   import os
   # Owner read/write only (0600)
   os.chmod(log_file, 0o600)
   ```

### 5.3 Path Traversal Prevention

**Risk**: User could specify malicious log directory path

**Mitigation**:
1. **Use fixed log directory** (not user-configurable)
2. **Validate and normalize paths**
   ```python
   from pathlib import Path
   log_dir = Path("~/.docx-launcher").expanduser().resolve()
   # Ensure it's under home directory
   if not str(log_dir).startswith(str(Path.home())):
       raise ValueError("Invalid log directory")
   ```

## 6. Error Handling

### 6.1 Error Scenarios

| Scenario | Detection | User Message | System Action |
|----------|-----------|--------------|---------------|
| Claude CLI not found | `shutil.which("claude")` returns None | "Claude CLI not found. Please install..." | Show error dialog with install instructions |
| Invalid CLI params | `shlex.split()` raises ValueError | "Invalid parameter format: {error}" | Show error dialog, don't launch |
| MCP server not running | Launch succeeds but connection fails | "Claude launched, but MCP connection failed" | Show warning, suggest starting server |
| Launch process fails | `subprocess.Popen` raises exception | "Failed to launch Claude: {error}" | Show error dialog, log details |
| Log write fails | File I/O error | "Launch succeeded, but logging failed" | Show warning, continue |

### 6.2 Error Dialog: Claude CLI Not Found

**Content**:
```
Claude CLI Not Found

Claude CLI is required to use this feature.

Installation Options:

1. Using npm (recommended):
   npm install -g @anthropic-ai/claude-code

2. Using pip:
   pip install claude-code

After installation, restart this application.

[View Documentation]  [OK]
```

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

## 7. Testing Strategy

### 7.1 Unit Tests

**Test File**: `tests/unit/test_cli_launcher.py`

**Test Cases**:
1. `test_is_claude_cli_available_found()` - CLI detected
2. `test_is_claude_cli_available_not_found()` - CLI not found
3. `test_generate_mcp_config_sse()` - SSE config generation
4. `test_generate_mcp_config_http()` - HTTP config generation
5. `test_build_command_no_params()` - Command without extra params
6. `test_build_command_with_params()` - Command with extra params
7. `test_validate_cli_params_safe()` - Safe parameter validation
8. `test_validate_cli_params_dangerous()` - Dangerous character detection
9. `test_sanitize_for_log()` - API key redaction

### 7.2 Integration Tests

**Test File**: `tests/integration/test_cli_launch.py`

**Test Cases**:
1. `test_launch_with_mock_cli()` - Mock Claude CLI launch
2. `test_launch_log_creation()` - Verify log file created
3. `test_launch_log_rotation()` - Verify log rotation works
4. `test_ui_launch_button_click()` - UI integration test

### 7.3 Manual Testing Checklist

- [ ] Launch Claude with SSE transport
- [ ] Launch Claude with extra params (--model haiku)
- [ ] Launch Claude when CLI not installed (error dialog)
- [ ] Launch Claude when server not running (warning)
- [ ] View launch log file
- [ ] Verify log rotation after 10MB
- [ ] Test with special characters in params (should be rejected)
- [ ] Test with quoted params (--prompt "Hello World")

## 8. Migration Path

### 8.1 Backward Compatibility

**Config Injector**: Keep `ConfigInjector` class but mark as deprecated

```python
# In config_injector.py
import warnings

class ConfigInjector:
    """
    DEPRECATED: Use CLILauncher instead.

    This class is kept for backward compatibility but will be removed in v2.0.
    """

    def __init__(self):
        warnings.warn(
            "ConfigInjector is deprecated. Use CLILauncher instead.",
            DeprecationWarning,
            stacklevel=2
        )
```

### 8.2 User Migration

**First Launch After Update**:
1. Show info dialog: "New Feature: Direct Claude Launch"
2. Explain CLI mode benefits
3. Provide link to documentation

**Implementation**:
```python
def check_first_launch_after_update(self):
    """Show migration info on first launch after update."""
    last_version = self.settings.value("app/last_version", "0.0.0")
    current_version = "2.0.0"  # Version with CLI mode

    if last_version < "2.0.0":
        self.show_cli_mode_intro_dialog()
        self.settings.setValue("app/last_version", current_version)
```

## 9. Performance Considerations

### 9.1 CLI Detection Caching

**Problem**: `shutil.which()` is called on every launch attempt

**Solution**: Cache result for 5 minutes

```python
class CLILauncher:
    def __init__(self):
        self._cli_path_cache: Optional[str] = None
        self._cache_time: Optional[float] = None
        self._cache_ttl = 300  # 5 minutes

    def is_claude_cli_available(self) -> Tuple[bool, str]:
        now = time.time()
        if self._cli_path_cache and self._cache_time:
            if now - self._cache_time < self._cache_ttl:
                return True, self._cli_path_cache

        # Perform detection
        cli_path = shutil.which("claude")
        if cli_path:
            self._cli_path_cache = cli_path
            self._cache_time = now
            return True, cli_path
        else:
            return False, "Claude CLI not found in PATH"
```

### 9.2 Log File Performance

**Problem**: Large log files slow down writes

**Solution**: Use RotatingFileHandler with 10MB limit

```python
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    self.log_file,
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=3
)
```

## 10. Future Enhancements

### 10.1 Process Management (v2.1)

**Feature**: Track and manage launched Claude CLI processes

**UI Addition**:
- "Stop Claude" button (enabled when process running)
- Process status indicator (PID, uptime)

**Implementation**:
```python
class CLILauncher:
    def __init__(self):
        self._active_process: Optional[subprocess.Popen] = None

    def stop_claude(self) -> bool:
        """Terminate active Claude CLI process."""
        if self._active_process:
            self._active_process.terminate()
            self._active_process.wait(timeout=5)
            return True
        return False
```

### 10.2 Launch Profiles (v2.2)

**Feature**: Save and load CLI parameter presets

**UI Addition**:
- "Save Profile" button
- Profile dropdown (e.g., "Opus + Reviewer", "Haiku + Fast")

**Data Structure**:
```json
{
  "profiles": [
    {
      "name": "Opus + Reviewer",
      "params": "--model opus --agent reviewer"
    },
    {
      "name": "Haiku + Fast",
      "params": "--model haiku --fast"
    }
  ]
}
```

### 10.3 STDIO Mode Support (v2.3)

**Challenge**: STDIO transport requires different launch approach

**Solution**: Use `--mcp-stdio` parameter with command

```bash
claude --mcp-stdio "uv run mcp-server-docx"
```

---

**Document Version**: 1.0
**Last Updated**: 2026-01-24
**Status**: Ready for Implementation
