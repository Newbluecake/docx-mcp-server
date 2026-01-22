"""MCP tool registration center"""
from mcp.server.fastmcp import FastMCP


def register_all_tools(mcp: FastMCP):
    """Register all MCP tools to the server instance"""
    from . import session_tools
    from . import content_tools
    from . import paragraph_tools
    from . import run_tools
    from . import table_tools
    from . import format_tools
    from . import advanced_tools
    from . import system_tools
    from . import cursor_tools
    from . import copy_tools
    from . import composite_tools

    # Register composite tools first (high-level, commonly used)
    composite_tools.register_tools(mcp)

    # Register each module's tools
    session_tools.register_tools(mcp)
    content_tools.register_tools(mcp)
    paragraph_tools.register_tools(mcp)
    run_tools.register_tools(mcp)
    table_tools.register_tools(mcp)
    format_tools.register_tools(mcp)
    advanced_tools.register_tools(mcp)
    system_tools.register_tools(mcp)
    cursor_tools.register_tools(mcp)
    copy_tools.register_tools(mcp)
