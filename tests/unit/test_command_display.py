import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from docx_server_launcher.core.cli_launcher import CLILauncher

class TestCommandGeneration:
    def setup_method(self):
        self.launcher = CLILauncher(log_dir="/tmp/test_docx_launcher_logs")

    def test_build_command_default(self):
        """Test building claude mcp add command with default parameters."""
        url = "http://127.0.0.1:8000/sse"

        # Mock platform.system to ensure consistent testing across platforms
        with patch("platform.system", return_value="Linux"):
            cmd = self.launcher.build_command(url, "sse", "")

            assert cmd[0] == "claude"
            assert cmd[1] == "mcp"
            assert cmd[2] == "add"
            assert cmd[3] == "--transport"
            assert cmd[4] == "sse"
            assert cmd[5] == "docx"
            assert cmd[6] == url

    def test_build_command_windows(self):
        """Test building command on Windows (adds cmd.exe /c)."""
        url = "http://127.0.0.1:8000/sse"

        with patch("platform.system", return_value="Windows"):
            cmd = self.launcher.build_command(url, "sse", "")

            assert cmd[0] == "cmd.exe"
            assert cmd[1] == "/c"
            assert cmd[2] == "claude"
            assert cmd[3] == "mcp"
            assert cmd[4] == "add"

    def test_build_command_with_extra_params(self):
        """Test building command with extra parameters."""
        url = "http://192.168.1.100:8000/sse"
        params = "--dangerously-skip-permission --theme light"

        with patch("platform.system", return_value="Linux"):
            cmd = self.launcher.build_command(url, "sse", params)

            assert "--dangerously-skip-permission" in cmd
            assert "--theme" in cmd
            assert "light" in cmd

    def test_build_command_lan_ip(self):
        """Test building command with LAN IP."""
        url = "http://192.168.32.38:8000/sse"

        with patch("platform.system", return_value="Linux"):
            cmd = self.launcher.build_command(url, "sse", "")

            # Verify URL is preserved correctly
            assert "192.168.32.38" in cmd[6]

    def test_get_lan_ip(self):
        """Test LAN IP detection."""
        lan_ip = self.launcher.get_lan_ip()

        # Should return an IP address (either real LAN IP or fallback)
        assert isinstance(lan_ip, str)
        # Should be a valid IP format (basic check)
        parts = lan_ip.split(".")
        assert len(parts) == 4
        assert all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)

    def test_validate_cli_params_valid(self):
        """Test validation of valid parameters."""
        valid_params = [
            "--model opus",
            "--dangerously-skip-permission",
            "--timeout 30",
            ""
        ]

        for param in valid_params:
            is_valid, msg = self.launcher.validate_cli_params(param)
            assert is_valid, f"Failed for valid param: {param}"
            assert msg == ""

    def test_validate_cli_params_invalid(self):
        """Test validation of invalid parameters (shell injection)."""
        invalid_params = [
            "& rm -rf /",
            "| grep password",
            "; echo hack",
            "$(command)",
            "`command`"
        ]

        for param in invalid_params:
            is_valid, msg = self.launcher.validate_cli_params(param)
            assert not is_valid, f"Failed to detect invalid param: {param}"
            assert "Invalid character" in msg
