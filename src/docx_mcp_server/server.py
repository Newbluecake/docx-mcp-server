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
from docx_mcp_server.tools.system_tools import docx_server_status
from docx_mcp_server.tools.cursor_tools import (
    docx_cursor_move, docx_cursor_get,
    docx_insert_paragraph_at_cursor, docx_insert_table_at_cursor
)

# Configure logging
logging.basicConfig()
logger = logging.getLogger("docx-mcp-server")
logger.setLevel(logging.INFO)

# Initialize SessionManager
session_manager = SessionManager()

# Create MCP Server
mcp = FastMCP("docx-mcp-server")

# Register all tools
register_all_tools(mcp, session_manager)

def main():
    """Main entry point for the server"""
    mcp.run()

if __name__ == "__main__":
    main()
