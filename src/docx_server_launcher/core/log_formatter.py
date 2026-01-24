"""
Log formatting utilities for the docx-server-launcher.

This module provides standardized log formatting functions for MCP server
and Claude CLI startup commands.
"""

import json
from datetime import datetime
from typing import Any, Dict, List


def format_mcp_command(command: str, args: List[str]) -> Dict[str, Any]:
    """
    Format MCP server startup command as structured JSON.

    Args:
        command: The base command (e.g., "uv")
        args: List of command arguments

    Returns:
        Dict containing structured log data with timestamp, level, message, and data
    """
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": "INFO",
        "message": "Starting MCP server with command",
        "data": {
            "command": command,
            "args": args
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
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": "INFO",
        "message": "Launching Claude CLI",
        "data": {
            "command": command,
            "mcp_config": mcp_config,
            "extra_params": extra_params or []
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
