"""
Unit tests for log_formatter module.
"""

import json
import pytest
from docx_server_launcher.core.log_formatter import (
    format_mcp_command,
    format_cli_command,
    format_log_message,
    filter_sensitive_info
)


class TestFilterSensitiveInfo:
    """Test sensitive information filtering."""

    def test_filter_file_paths(self):
        """Test that full file paths are redacted."""
        text = "/home/user/secret/file.txt"
        result = filter_sensitive_info(text)
        assert "[PATH]" in result
        assert "/home/user/secret" not in result
        assert "file.txt" in result

    def test_filter_api_keys(self):
        """Test that API keys are redacted."""
        text = "api_key=sk-1234567890abcdef"
        result = filter_sensitive_info(text)
        assert "[REDACTED]" in result
        assert "sk-1234567890abcdef" not in result

    def test_filter_tokens(self):
        """Test that tokens are redacted."""
        text = "token: abc123xyz"
        result = filter_sensitive_info(text)
        assert "[REDACTED]" in result
        assert "abc123xyz" not in result

    def test_filter_passwords(self):
        """Test that passwords are redacted."""
        text = "password=mysecret123"
        result = filter_sensitive_info(text)
        assert "[REDACTED]" in result
        assert "mysecret123" not in result


class TestFormatMcpCommand:
    """Test MCP command formatting."""

    def test_basic_format(self):
        """Test basic MCP command formatting."""
        command = "uv"
        args = ["run", "mcp-server-docx", "--transport", "sse"]
        result = format_mcp_command(command, args)

        assert result["level"] == "INFO"
        assert result["message"] == "Starting MCP server with command"
        assert result["data"]["command"] == "uv"
        assert result["data"]["args"] == args
        assert "timestamp" in result

    def test_filters_sensitive_args(self):
        """Test that sensitive info in args is filtered."""
        command = "uv"
        # Args as a single string (as they would appear in a command)
        args = ["run", "--api-key secret123"]
        result = format_mcp_command(command, args)

        assert "[REDACTED]" in result["data"]["args"][1]
        assert "secret123" not in str(result)


class TestFormatCliCommand:
    """Test CLI command formatting."""

    def test_basic_format(self):
        """Test basic CLI command formatting."""
        command = "claude --mcp-config {...}"
        mcp_config = {"mcpServers": {"docx-server": {"url": "http://localhost:8000"}}}
        extra_params = ["--model", "opus"]

        result = format_cli_command(command, mcp_config, extra_params)

        assert result["level"] == "INFO"
        assert result["message"] == "Launching Claude CLI"
        assert result["data"]["command"] == command
        assert result["data"]["mcp_config"] == mcp_config
        assert result["data"]["extra_params"] == extra_params
        assert "timestamp" in result

    def test_filters_sensitive_command(self):
        """Test that sensitive info in command is filtered."""
        command = "claude --api-key secret123"
        mcp_config = {}
        result = format_cli_command(command, mcp_config)

        assert "[REDACTED]" in result["data"]["command"]
        assert "secret123" not in result["data"]["command"]

    def test_handles_no_extra_params(self):
        """Test handling of no extra params."""
        command = "claude"
        mcp_config = {}
        result = format_cli_command(command, mcp_config)

        assert result["data"]["extra_params"] == []


class TestFormatLogMessage:
    """Test log message formatting."""

    def test_mcp_format(self):
        """Test MCP log message formatting."""
        log_data = {
            "timestamp": "2026-01-25T10:00:00Z",
            "level": "INFO",
            "message": "Starting MCP server",
            "data": {
                "command": "uv",
                "args": ["run", "mcp-server-docx"]
            }
        }

        result = format_log_message(log_data)

        assert "[2026-01-25T10:00:00Z] INFO: Starting MCP server" in result
        assert "Command:" in result
        assert "uv" in result

    def test_cli_format(self):
        """Test CLI log message formatting."""
        log_data = {
            "timestamp": "2026-01-25T10:00:00Z",
            "level": "INFO",
            "message": "Launching Claude CLI",
            "data": {
                "command": "claude --model opus",
                "mcp_config": {"mcpServers": {}},
                "extra_params": ["--model", "opus"]
            }
        }

        result = format_log_message(log_data)

        assert "[2026-01-25T10:00:00Z] INFO: Launching Claude CLI" in result
        assert "Command: claude --model opus" in result
        assert "MCP Config:" in result
        assert "Extra Params: --model opus" in result
