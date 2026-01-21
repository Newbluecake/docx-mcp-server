"""System management tools"""
import json
import os
import sys
import time
import platform
from mcp.server.fastmcp import FastMCP

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
        "active_sessions": len(session_manager.sessions)
    }
    return json.dumps(info, indent=2)
def register_tools(mcp: FastMCP):
    """Register system tools"""

    mcp.tool()(docx_server_status)