"""
Log formatting utilities for the docx-server-launcher.

This module provides standardized log formatting functions for MCP server
and Claude CLI startup commands.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def filter_sensitive_info(text: str) -> str:
    """
    Filter sensitive information from log text.

    Args:
        text: Text to filter

    Returns:
        Filtered text with sensitive info redacted
    """
    # Redact full file paths (keep only filename)
    text = re.sub(
        r'(/[^/\s]+)+/([^/\s]+)',
        r'[PATH]/\2',
        text
    )

    # Redact API keys
    text = re.sub(
        r'(api[_-]?key["\']?\s*[:=]\s*["\']?)([^\s"\']+)',
        r'\1[REDACTED]',
        text,
        flags=re.IGNORECASE
    )

    # Redact tokens
    text = re.sub(
        r'(token["\']?\s*[:=]\s*["\']?)([^\s"\']+)',
        r'\1[REDACTED]',
        text,
        flags=re.IGNORECASE
    )

    # Redact passwords
    text = re.sub(
        r'(password["\']?\s*[:=]\s*["\']?)([^\s"\']+)',
        r'\1[REDACTED]',
        text,
        flags=re.IGNORECASE
    )

    return text


def format_mcp_command(command: str, args: List[str]) -> Dict[str, Any]:
    """
    Format MCP server startup command as structured JSON.

    Args:
        command: The base command (e.g., "uv")
        args: List of command arguments

    Returns:
        Dict containing structured log data with timestamp, level, message, and data
    """
    # Filter sensitive info from args
    filtered_args = [filter_sensitive_info(arg) for arg in args]

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": "INFO",
        "message": "Starting MCP server with command",
        "data": {
            "command": command,
            "args": filtered_args
        }
    }


def format_cli_command(
    command: str,
    mcp_config: Dict[str, Any],
    extra_params: List[str] = None
) -> Dict[str, Any]:
    """
    Format Claude CLI startup command as structured JSON.

    Args:
        command: The complete CLI command string
        mcp_config: MCP configuration dictionary
        extra_params: Optional list of extra parameters

    Returns:
        Dict containing structured log data
    """
    # Filter sensitive info
    filtered_command = filter_sensitive_info(command)
    filtered_params = [filter_sensitive_info(p) for p in (extra_params or [])]

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": "INFO",
        "message": "Launching Claude CLI",
        "data": {
            "command": filtered_command,
            "mcp_config": mcp_config,
            "extra_params": filtered_params
        }
    }


def format_log_message(log_data: Dict[str, Any]) -> str:
    """
    Format structured log data as a human-readable string.

    Args:
        log_data: Structured log data dictionary

    Returns:
        Formatted log message string
    """
    timestamp = log_data.get("timestamp", "")
    level = log_data.get("level", "INFO")
    message = log_data.get("message", "")
    data = log_data.get("data", {})

    lines = [
        f"[{timestamp}] {level}: {message}"
    ]

    if "command" in data and "args" in data:
        # MCP server format
        cmd_json = json.dumps({"command": data["command"], "args": data["args"]})
        lines.append(f"Command: {cmd_json}")
    elif "command" in data:
        # Claude CLI format
        lines.append(f"Command: {data['command']}")
        if "mcp_config" in data:
            lines.append(f"MCP Config: {json.dumps(data['mcp_config'])}")
        if "extra_params" in data and data["extra_params"]:
            lines.append(f"Extra Params: {' '.join(data['extra_params'])}")

    return "\n".join(lines)
