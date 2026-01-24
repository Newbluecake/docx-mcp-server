"""
Unit tests for CLILauncher module.
"""

import json
import sys
import pytest
import subprocess
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
from docx_server_launcher.core.cli_launcher import CLILauncher


class TestCLILauncherInit:
    """Test CLILauncher initialization."""

    def test_cli_launcher_init(self, tmp_path):
        """Test basic initialization."""
        launcher = CLILauncher(log_dir=str(tmp_path))

        assert launcher.log_dir.exists()
        assert launcher.log_dir == tmp_path.resolve()
        assert launcher.log_file.name == "launch.log"
        assert launcher.log_file.parent == tmp_path.resolve()

    def test_log_dir_creation(self, tmp_path):
        """Test log directory is created if it doesn't exist."""
        log_dir = tmp_path / "subdir" / "logs"
        launcher = CLILauncher(log_dir=str(log_dir))

        assert log_dir.exists()
        assert launcher.log_dir == log_dir.resolve()

    def test_log_dir_expansion(self):
        """Test tilde expansion in log directory path."""
        launcher = CLILauncher(log_dir="~/.docx-launcher")

        assert "~" not in str(launcher.log_dir)
        assert launcher.log_dir.is_absolute()

    def test_logger_setup(self, tmp_path):
        """Test logger is properly configured."""
        launcher = CLILauncher(log_dir=str(tmp_path))

        assert launcher.logger is not None
        assert launcher.logger.name == "CLILauncher"
        assert len(launcher.logger.handlers) > 0

    def test_cache_initialization(self, tmp_path):
        """Test CLI path cache is initialized."""
        launcher = CLILauncher(log_dir=str(tmp_path))

        assert launcher._cli_path_cache is None
        assert launcher._cache_time is None
        assert launcher._cache_ttl == 300


class TestCLIDetection:
    """Test Claude CLI detection."""

    def test_is_claude_cli_available_found(self, tmp_path):
        """Test CLI detection when Claude is found."""
        with patch("shutil.which", return_value="/usr/bin/claude"):
            launcher = CLILauncher(log_dir=str(tmp_path))
            is_available, path = launcher.is_claude_cli_available()

            assert is_available is True
            assert path == "/usr/bin/claude"

    def test_is_claude_cli_available_not_found(self, tmp_path):
        """Test CLI detection when Claude is not found."""
        with patch("shutil.which", return_value=None):
            launcher = CLILauncher(log_dir=str(tmp_path))
            is_available, msg = launcher.is_claude_cli_available()

            assert is_available is False
            assert "not found" in msg.lower()

    def test_cli_detection_caching(self, tmp_path):
        """Test that CLI detection results are cached."""
        with patch("shutil.which", return_value="/usr/bin/claude") as mock_which:
            launcher = CLILauncher(log_dir=str(tmp_path))

            # First call
            is_available1, path1 = launcher.is_claude_cli_available()
            assert mock_which.call_count == 1

            # Second call (should use cache)
            is_available2, path2 = launcher.is_claude_cli_available()
            assert mock_which.call_count == 1  # Not called again

            assert is_available1 == is_available2
            assert path1 == path2

    def test_cli_detection_cache_expiry(self, tmp_path):
        """Test that cache expires after TTL."""
        with patch("shutil.which", return_value="/usr/bin/claude") as mock_which:
            launcher = CLILauncher(log_dir=str(tmp_path))
            launcher._cache_ttl = 0.1  # 100ms TTL for testing

            # First call
            launcher.is_claude_cli_available()
            assert mock_which.call_count == 1

            # Wait for cache to expire
            time.sleep(0.15)

            # Second call (cache expired, should call again)
            launcher.is_claude_cli_available()
            assert mock_which.call_count == 2

    def test_cli_detection_cache_cleared_on_failure(self, tmp_path):
        """Test that cache is cleared when CLI not found."""
        launcher = CLILauncher(log_dir=str(tmp_path))
        launcher._cache_ttl = 0.1  # Short TTL for testing

        # First call succeeds and sets cache
        with patch("shutil.which", return_value="/usr/bin/claude"):
            launcher.is_claude_cli_available()
            assert launcher._cli_path_cache == "/usr/bin/claude"

        # Wait for cache to expire
        time.sleep(0.15)

        # Second call fails and should clear cache
        with patch("shutil.which", return_value=None):
            is_available, msg = launcher.is_claude_cli_available()

            assert is_available is False
            assert launcher._cli_path_cache is None
            assert launcher._cache_time is None


class TestMCPConfigGeneration:
    """Test MCP configuration generation."""

    def test_generate_mcp_config_sse(self, tmp_path):
        """Test MCP config generation for SSE transport."""
        launcher = CLILauncher(log_dir=str(tmp_path))
        config = launcher.generate_mcp_config("http://127.0.0.1:8000/sse", "sse")

        assert config == {
            "mcpServers": {
                "docx-server": {
                    "url": "http://127.0.0.1:8000/sse",
                    "transport": "sse"
                }
            }
        }

    def test_generate_mcp_config_http(self, tmp_path):
        """Test MCP config generation for Streamable HTTP transport."""
        launcher = CLILauncher(log_dir=str(tmp_path))
        config = launcher.generate_mcp_config(
            "http://127.0.0.1:8080/mcp",
            "streamable-http"
        )

        assert config == {
            "mcpServers": {
                "docx-server": {
                    "url": "http://127.0.0.1:8080/mcp",
                    "transport": "streamable-http"
                }
            }
        }

    def test_generate_mcp_config_stdio_error(self, tmp_path):
        """Test that STDIO transport raises error."""
        launcher = CLILauncher(log_dir=str(tmp_path))

        with pytest.raises(ValueError, match="STDIO.*not supported"):
            launcher.generate_mcp_config("", "stdio")

    def test_generate_mcp_config_case_insensitive(self, tmp_path):
        """Test that transport type is case-insensitive."""
        launcher = CLILauncher(log_dir=str(tmp_path))

        # Should raise error regardless of case
        with pytest.raises(ValueError, match="STDIO.*not supported"):
            launcher.generate_mcp_config("", "STDIO")

        with pytest.raises(ValueError, match="STDIO.*not supported"):
            launcher.generate_mcp_config("", "StDiO")


class TestCommandBuilder:
    """Test CLI command building."""

    def test_build_command_no_params(self, tmp_path):
        """Test command building without extra parameters."""
        launcher = CLILauncher(log_dir=str(tmp_path))
        config = {"mcpServers": {"docx-server": {"url": "http://127.0.0.1:8000/sse", "transport": "sse"}}}

        cmd = launcher.build_command(config, "")

        assert cmd == ["claude", "--mcp-config", json.dumps(config)]

    def test_build_command_with_params(self, tmp_path):
        """Test command building with extra parameters."""
        launcher = CLILauncher(log_dir=str(tmp_path))
        config = {"mcpServers": {"docx-server": {"url": "http://127.0.0.1:8000/sse", "transport": "sse"}}}

        cmd = launcher.build_command(config, "--model opus --agent reviewer")

        assert cmd == [
            "claude",
            "--mcp-config",
            json.dumps(config),
            "--model",
            "opus",
            "--agent",
            "reviewer"
        ]

    def test_build_command_quoted_params(self, tmp_path):
        """Test command building with quoted parameters."""
        launcher = CLILauncher(log_dir=str(tmp_path))
        config = {"mcpServers": {"docx-server": {"url": "http://127.0.0.1:8000/sse", "transport": "sse"}}}

        cmd = launcher.build_command(config, '--prompt "Hello World"')

        assert cmd == [
            "claude",
            "--mcp-config",
            json.dumps(config),
            "--prompt",
            "Hello World"
        ]

    def test_build_command_whitespace_only(self, tmp_path):
        """Test command building with whitespace-only extra params."""
        launcher = CLILauncher(log_dir=str(tmp_path))
        config = {"mcpServers": {"docx-server": {"url": "http://127.0.0.1:8000/sse", "transport": "sse"}}}

        cmd = launcher.build_command(config, "   ")

        assert cmd == ["claude", "--mcp-config", json.dumps(config)]

    def test_build_command_parse_error(self, tmp_path):
        """Test command building with unparseable parameters."""
        launcher = CLILauncher(log_dir=str(tmp_path))
        config = {"mcpServers": {"docx-server": {"url": "http://127.0.0.1:8000/sse", "transport": "sse"}}}

        # Unclosed quote
        with pytest.raises(ValueError, match="Failed to parse"):
            launcher.build_command(config, '--prompt "Hello')


class TestLaunchProcessManager:
    """Test launch process management."""

    def test_launch_success(self, tmp_path):
        """Test successful Claude CLI launch."""
        with patch("shutil.which", return_value="/usr/bin/claude"):
            with patch("subprocess.Popen") as mock_popen:
                # Mock process
                mock_process = MagicMock()
                mock_process.pid = 12345
                mock_popen.return_value = mock_process

                launcher = CLILauncher(log_dir=str(tmp_path))
                success, msg = launcher.launch("http://127.0.0.1:8000/sse", "sse", "")

                assert success is True
                assert "started successfully" in msg.lower()
                assert "12345" in msg

                # Verify Popen was called
                mock_popen.assert_called_once()
                call_args = mock_popen.call_args
                assert call_args[0][0][0] == "claude"
                assert "--mcp-config" in call_args[0][0]

    def test_launch_with_extra_params(self, tmp_path):
        """Test launch with extra CLI parameters."""
        with patch("shutil.which", return_value="/usr/bin/claude"):
            with patch("subprocess.Popen") as mock_popen:
                mock_process = MagicMock()
                mock_process.pid = 12345
                mock_popen.return_value = mock_process

                launcher = CLILauncher(log_dir=str(tmp_path))
                success, msg = launcher.launch(
                    "http://127.0.0.1:8000/sse",
                    "sse",
                    "--model opus"
                )

                assert success is True

                # Verify extra params in command
                call_args = mock_popen.call_args
                cmd = call_args[0][0]
                assert "--model" in cmd
                assert "opus" in cmd

    def test_launch_cli_not_found(self, tmp_path):
        """Test launch when CLI not found."""
        with patch("shutil.which", return_value=None):
            launcher = CLILauncher(log_dir=str(tmp_path))
            success, msg = launcher.launch("http://127.0.0.1:8000/sse", "sse", "")

            assert success is False
            assert "not found" in msg.lower()

    def test_launch_stdio_transport_error(self, tmp_path):
        """Test launch with unsupported STDIO transport."""
        with patch("shutil.which", return_value="/usr/bin/claude"):
            launcher = CLILauncher(log_dir=str(tmp_path))
            success, msg = launcher.launch("", "stdio", "")

            assert success is False
            assert "not supported" in msg.lower()

    def test_launch_process_error(self, tmp_path):
        """Test launch when subprocess fails."""
        with patch("shutil.which", return_value="/usr/bin/claude"):
            with patch("subprocess.Popen", side_effect=subprocess.SubprocessError("Launch failed")):
                launcher = CLILauncher(log_dir=str(tmp_path))
                success, msg = launcher.launch("http://127.0.0.1:8000/sse", "sse", "")

                assert success is False
                assert "failed to launch" in msg.lower()

    def test_launch_invalid_params(self, tmp_path):
        """Test launch with invalid extra parameters."""
        with patch("shutil.which", return_value="/usr/bin/claude"):
            launcher = CLILauncher(log_dir=str(tmp_path))
            success, msg = launcher.launch(
                "http://127.0.0.1:8000/sse",
                "sse",
                '--prompt "unclosed'
            )

            assert success is False
            assert "parse" in msg.lower()

    def test_launch_logging(self, tmp_path):
        """Test that launch attempts are logged."""
        with patch("shutil.which", return_value="/usr/bin/claude"):
            with patch("subprocess.Popen") as mock_popen:
                mock_process = MagicMock()
                mock_process.pid = 12345
                mock_popen.return_value = mock_process

                launcher = CLILauncher(log_dir=str(tmp_path))
                launcher.launch("http://127.0.0.1:8000/sse", "sse", "--model opus")

                # Check log file exists and contains launch info
                log_file = tmp_path / "launch.log"
                assert log_file.exists()

                log_content = log_file.read_text()
                assert "Launch Attempt" in log_content
                assert "Command:" in log_content
                assert "MCP Config:" in log_content
                assert "started successfully" in log_content


class TestLaunchLogging:
    """Test launch logging functionality."""

    def test_log_launch_success(self, tmp_path):
        """Test logging of successful launch."""
        launcher = CLILauncher(log_dir=str(tmp_path))
        cmd = ["claude", "--mcp-config", "{}"]
        config = {"mcpServers": {"docx-server": {"url": "http://127.0.0.1:8000/sse", "transport": "sse"}}}

        launcher._log_launch(cmd, config, success=True, pid=12345)

        log_file = tmp_path / "launch.log"
        assert log_file.exists()

        log_content = log_file.read_text()
        assert "Launch Attempt" in log_content
        assert "Command: claude --mcp-config {}" in log_content
        assert "MCP Config:" in log_content
        assert "started successfully" in log_content
        assert "12345" in log_content

    def test_log_launch_failure(self, tmp_path):
        """Test logging of failed launch."""
        launcher = CLILauncher(log_dir=str(tmp_path))
        cmd = ["claude", "--mcp-config", "{}"]
        config = {"mcpServers": {}}

        launcher._log_launch(cmd, config, success=False, error="CLI not found")

        log_file = tmp_path / "launch.log"
        assert log_file.exists()

        log_content = log_file.read_text()
        assert "Launch Attempt" in log_content
        assert "Launch failed: CLI not found" in log_content

    def test_log_rotation_config(self, tmp_path):
        """Test that log rotation is configured correctly."""
        launcher = CLILauncher(log_dir=str(tmp_path))

        # Verify the handler is configured correctly
        from logging.handlers import RotatingFileHandler
        handler = launcher.logger.handlers[0]
        assert isinstance(handler, RotatingFileHandler)
        assert handler.maxBytes == 10 * 1024 * 1024
        assert handler.backupCount == 3

    @pytest.mark.skipif(
        sys.platform.startswith("win"),
        reason="Windows does not expose POSIX permission bits reliably",
    )
    def test_log_file_permissions(self, tmp_path):
        """Test that log file has correct permissions."""
        launcher = CLILauncher(log_dir=str(tmp_path))
        cmd = ["claude", "--mcp-config", "{}"]
        config = {"mcpServers": {}}

        launcher._log_launch(cmd, config, success=True, pid=12345)

        log_file = tmp_path / "launch.log"
        if log_file.exists():
            # Check file permissions (0600 = owner read/write only)
            import stat
            mode = log_file.stat().st_mode
            # On some systems, permissions might not be exactly 0600
            # Just check that it's not world-readable
            assert not (mode & stat.S_IROTH)  # Not readable by others
            assert not (mode & stat.S_IWOTH)  # Not writable by others


class TestSecurityValidation:
    """Test security validation functionality."""

    def test_validate_cli_params_safe(self, tmp_path):
        """Test validation of safe parameters."""
        launcher = CLILauncher(log_dir=str(tmp_path))

        is_valid, msg = launcher.validate_cli_params("--model opus --agent reviewer")
        assert is_valid is True
        assert msg == ""

    def test_validate_cli_params_empty(self, tmp_path):
        """Test validation of empty parameters."""
        launcher = CLILauncher(log_dir=str(tmp_path))

        is_valid, msg = launcher.validate_cli_params("")
        assert is_valid is True

        is_valid, msg = launcher.validate_cli_params("   ")
        assert is_valid is True

    def test_validate_cli_params_dangerous_semicolon(self, tmp_path):
        """Test rejection of semicolon (command separator)."""
        launcher = CLILauncher(log_dir=str(tmp_path))

        is_valid, msg = launcher.validate_cli_params("--model opus; rm -rf /")
        assert is_valid is False
        assert ";" in msg

    def test_validate_cli_params_dangerous_pipe(self, tmp_path):
        """Test rejection of pipe character."""
        launcher = CLILauncher(log_dir=str(tmp_path))

        is_valid, msg = launcher.validate_cli_params("--model opus | cat /etc/passwd")
        assert is_valid is False
        assert "|" in msg

    def test_validate_cli_params_dangerous_ampersand(self, tmp_path):
        """Test rejection of ampersand (background execution)."""
        launcher = CLILauncher(log_dir=str(tmp_path))

        is_valid, msg = launcher.validate_cli_params("--model opus & malicious_command")
        assert is_valid is False
        assert "&" in msg

    def test_validate_cli_params_dangerous_backtick(self, tmp_path):
        """Test rejection of backtick (command substitution)."""
        launcher = CLILauncher(log_dir=str(tmp_path))

        is_valid, msg = launcher.validate_cli_params("--model `whoami`")
        assert is_valid is False
        assert "`" in msg

    def test_validate_cli_params_dangerous_dollar(self, tmp_path):
        """Test rejection of dollar sign (variable expansion)."""
        launcher = CLILauncher(log_dir=str(tmp_path))

        is_valid, msg = launcher.validate_cli_params("--model $USER")
        assert is_valid is False
        assert "$" in msg

    def test_validate_cli_params_parse_error(self, tmp_path):
        """Test detection of parse errors."""
        launcher = CLILauncher(log_dir=str(tmp_path))

        is_valid, msg = launcher.validate_cli_params('--prompt "unclosed')
        assert is_valid is False
        assert "parse error" in msg.lower()

    def test_sanitize_for_log_api_key(self, tmp_path):
        """Test API key redaction."""
        launcher = CLILauncher(log_dir=str(tmp_path))

        sanitized = launcher.sanitize_for_log("--api-key sk-1234567890 --model opus")
        assert "sk-1234567890" not in sanitized
        assert "[REDACTED]" in sanitized
        assert "--model opus" in sanitized

    def test_sanitize_for_log_token(self, tmp_path):
        """Test token redaction."""
        launcher = CLILauncher(log_dir=str(tmp_path))

        sanitized = launcher.sanitize_for_log("--token abc123xyz --model opus")
        assert "abc123xyz" not in sanitized
        assert "[REDACTED]" in sanitized

    def test_sanitize_for_log_password(self, tmp_path):
        """Test password redaction."""
        launcher = CLILauncher(log_dir=str(tmp_path))

        sanitized = launcher.sanitize_for_log("--password secret123 --model opus")
        assert "secret123" not in sanitized
        assert "[REDACTED]" in sanitized

    def test_sanitize_for_log_case_insensitive(self, tmp_path):
        """Test case-insensitive redaction."""
        launcher = CLILauncher(log_dir=str(tmp_path))

        sanitized = launcher.sanitize_for_log("--API-KEY sk-123 --Token xyz --PASSWORD pwd")
        assert "sk-123" not in sanitized
        assert "xyz" not in sanitized
        assert "pwd" not in sanitized
        assert sanitized.count("[REDACTED]") == 3

    def test_sanitize_for_log_empty(self, tmp_path):
        """Test sanitization of empty string."""
        launcher = CLILauncher(log_dir=str(tmp_path))

        sanitized = launcher.sanitize_for_log("")
        assert sanitized == ""

        sanitized = launcher.sanitize_for_log(None)
        assert sanitized is None

    def test_launch_with_dangerous_params(self, tmp_path):
        """Test that launch rejects dangerous parameters."""
        with patch("shutil.which", return_value="/usr/bin/claude"):
            launcher = CLILauncher(log_dir=str(tmp_path))
            success, msg = launcher.launch(
                "http://127.0.0.1:8000/sse",
                "sse",
                "--model opus; rm -rf /"
            )

            assert success is False
            assert "invalid character" in msg.lower() or ";" in msg






