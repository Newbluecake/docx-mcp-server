"""DOCX MCP Server - Main entry point"""
import logging
from mcp.server.fastmcp import FastMCP
from docx_mcp_server.core.session import SessionManager
from docx_mcp_server.tools import register_all_tools

# Version constant
VERSION = "0.1.3"

# Re-export all tool functions for backward compatibility
from docx_mcp_server.tools.session_tools import (
    docx_create, docx_close, docx_save, docx_get_context
)
from docx_mcp_server.tools.content_tools import (
    docx_read_content, docx_find_paragraphs, docx_list_files, docx_extract_template_structure
)
from docx_mcp_server.tools.paragraph_tools import (
    docx_add_paragraph, docx_add_heading, docx_update_paragraph_text,
    docx_copy_paragraph, docx_delete, docx_add_page_break
)
from docx_mcp_server.tools.run_tools import (
    docx_add_run, docx_update_run_text, docx_set_font
)
from docx_mcp_server.tools.table_tools import (
    docx_add_table, docx_get_table, docx_find_table, docx_get_cell,
    docx_add_paragraph_to_cell, docx_add_table_row, docx_add_table_col,
    docx_fill_table, docx_copy_table
)
from docx_mcp_server.tools.format_tools import (
    docx_set_alignment, docx_set_properties, docx_format_copy, docx_set_margins
)
from docx_mcp_server.tools.advanced_tools import (
    docx_replace_text, docx_insert_image
)
from docx_mcp_server.tools.system_tools import (
    docx_server_status
)

logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("docx-mcp-server")

# Global session manager
session_manager = SessionManager()

# Register all tools
register_all_tools(mcp)


def main():
    """Server startup entry point"""
    import argparse
    parser = argparse.ArgumentParser(description="DOCX MCP Server")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "sse"], help="Transport protocol")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (SSE only)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (SSE only)")

    # Parse known args to avoid conflict if FastMCP parses its own
    args, unknown = parser.parse_known_args()

    if args.transport == "sse":
        print(f"Starting SSE server on {args.host}:{args.port}...", flush=True)

        # FastMCP.run() doesn't accept host/port args, we must update settings directly
        mcp.settings.host = args.host
        mcp.settings.port = args.port

        # Disable DNS rebinding protection for non-localhost addresses (LAN access)
        if args.host not in ("127.0.0.1", "localhost"):
            mcp.settings.transport_security = None

        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
