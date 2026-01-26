import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from docx_server_launcher.core.cli_launcher import CLILauncher

class TestCommandGeneration:
    def setup_method(self):
        self.launcher = CLILauncher(log_dir="/tmp/test_docx_launcher_logs")

    def test_generate_mcp_config(self):
        """Test MCP config generation."""
        url = "http://127.0.0.1:8000/sse"
        config = self.launcher.generate_mcp_config(url, "sse")

        assert "mcpServers" in config
        assert "docx-server" in config["mcpServers"]
        assert config["mcpServers"]["docx-server"]["url"] == url
        assert config["mcpServers"]["docx-server"]["transport"] == "sse"

    def test_build_command_default(self):
        """Test building command with default parameters."""
        url = "http://127.0.0.1:8000/sse"
        config = self.launcher.generate_mcp_config(url, "sse")

        # Mock platform.system to ensure consistent testing across platforms
        with patch("platform.system", return_value="Linux"):
            cmd = self.launcher.build_command(config, "")

            assert cmd[0] == "claude"
            assert cmd[1] == "--mcp-config"
            assert "127.0.0.1" in cmd[2]

    def test_build_command_windows(self):
        """Test building command on Windows (adds cmd.exe /c)."""
        url = "http://127.0.0.1:8000/sse"
        config = self.launcher.generate_mcp_config(url, "sse")

        with patch("platform.system", return_value="Windows"):
            cmd = self.launcher.build_command(config, "")

            assert cmd[0] == "cmd.exe"
            assert cmd[1] == "/c"
            assert cmd[2] == "claude"

    def test_build_command_with_extra_params(self):
        """Test building command with extra parameters."""
        url = "http://127.0.0.1:8000/sse"
        config = self.launcher.generate_mcp_config(url, "sse")
        params = "--dangerously-skip-permission --theme light"

        with patch("platform.system", return_value="Linux"):
            cmd = self.launcher.build_command(config, params)

            assert "--dangerously-skip-permission" in cmd
            assert "--theme" in cmd
            assert "light" in cmd

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
