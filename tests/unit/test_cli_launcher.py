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
        server_url = "http://127.0.0.1:8000/sse"

        cmd = launcher.build_command(server_url, "sse", "")

        assert cmd == ["claude", "mcp", "add", "--transport", "sse", "docx", server_url]

    def test_build_command_with_params(self, tmp_path):
        """Test command building with extra parameters."""
        launcher = CLILauncher(log_dir=str(tmp_path))
        server_url = "http://127.0.0.1:8000/sse"

        cmd = launcher.build_command(server_url, "sse", "--model opus --agent reviewer")

        assert cmd == [
            "claude",
            "mcp",
            "add",
            "--transport",
            "sse",
            "docx",
            server_url,
            "--model",
            "opus",
            "--agent",
            "reviewer"
        ]

    def test_build_command_quoted_params(self, tmp_path):
        """Test command building with quoted parameters."""
        launcher = CLILauncher(log_dir=str(tmp_path))
        server_url = "http://127.0.0.1:8000/sse"

        cmd = launcher.build_command(server_url, "sse", '--prompt "Hello World"')

        assert cmd == [
            "claude",
            "mcp",
            "add",
            "--transport",
            "sse",
            "docx",
            server_url,
            "--prompt",
            "Hello World"
        ]

    def test_build_command_whitespace_only(self, tmp_path):
        """Test command building with whitespace-only extra params."""
        launcher = CLILauncher(log_dir=str(tmp_path))
        server_url = "http://127.0.0.1:8000/sse"

        cmd = launcher.build_command(server_url, "sse", "   ")

        assert cmd == ["claude", "mcp", "add", "--transport", "sse", "docx", server_url]

    def test_build_command_parse_error(self, tmp_path):
        """Test command building with unparseable parameters."""
        launcher = CLILauncher(log_dir=str(tmp_path))
        server_url = "http://127.0.0.1:8000/sse"

        # Unclosed quote
        with pytest.raises(ValueError, match="Failed to parse"):
            launcher.build_command(server_url, "sse", '--prompt "Hello')


