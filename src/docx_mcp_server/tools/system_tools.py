"""System management tools"""
import json
import os
import sys
import time
import platform
import logging
from mcp.server.fastmcp import FastMCP
from docx_mcp_server.core.response import create_success_response, create_error_response
from docx_mcp_server.utils.logger import LEVEL_NAMES, get_global_log_level, set_global_log_level

SERVER_START_TIME = time.time()
VERSION = "0.1.3"


def docx_server_status() -> str:
    """
    Get the current status and environment information of the server.
    Useful for clients to understand the server's running environment (OS, paths).

    Returns:
        str: JSON string containing server status info.
    """
    from docx_mcp_server.server import session_manager

    info = {
        "status": "running",
        "version": VERSION,
        "cwd": os.getcwd(),
        "os_name": os.name,
        "os_system": platform.system(),
        "path_sep": os.sep,
        "python_version": sys.version,
        "start_time": SERVER_START_TIME,
        "uptime_seconds": time.time() - SERVER_START_TIME,
        "active_sessions": len(session_manager.sessions),
        "log_level": get_global_log_level(),
    }
    return json.dumps(info, indent=2)


def docx_get_log_level() -> str:
    """
    Get current server log level.
    """
    level = get_global_log_level()
    return create_success_response(
        message="Retrieved current log level",
        level=level,
    )


def docx_set_log_level(level: str) -> str:
    """
    Set server log level at runtime.
    Args:
        level: One of DEBUG, INFO, WARNING, ERROR, CRITICAL
    """
    try:
        set_global_log_level(level)
    except ValueError:
        return create_error_response(
            message=f"Invalid log level: {level}. Choose from {list(LEVEL_NAMES.keys())}",
            error_type="ValidationError",
        )

    normalized = get_global_log_level()
    logging.getLogger(__name__).info(f"Log level changed to {normalized}")
    return create_success_response(
        message="Log level updated",
        level=normalized,
    )


def register_tools(mcp: FastMCP):
    """Register system tools"""

    mcp.tool()(docx_server_status)
    mcp.tool()(docx_get_log_level)
    mcp.tool()(docx_set_log_level)
