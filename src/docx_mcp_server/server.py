"""DOCX MCP Server - Main entry point"""
import logging
import argparse
import os
import json
import types
from functools import wraps
from mcp.server.fastmcp import FastMCP
from docx_mcp_server.core.session import SessionManager
from docx_mcp_server.tools import register_all_tools
from docx_mcp_server.utils.logger import (
    LEVEL_NAMES,
    set_global_log_level,
)

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
    docx_insert_paragraph, docx_insert_heading, docx_update_paragraph_text,
    docx_copy_paragraph, docx_delete, docx_insert_page_break
)
from docx_mcp_server.tools.run_tools import (
    docx_insert_run, docx_update_run_text, docx_set_font
)
from docx_mcp_server.tools.table_tools import (
    docx_insert_table, docx_get_table, docx_find_table, docx_get_cell,
    docx_insert_paragraph_to_cell, docx_insert_table_row, docx_insert_table_col,
    docx_fill_table, docx_copy_table
)
from docx_mcp_server.tools.cursor_tools import (
    docx_cursor_move, docx_cursor_get
)
from docx_mcp_server.tools.advanced_tools import (
    docx_replace_text, docx_insert_image, docx_batch_replace_text
)
from docx_mcp_server.tools.format_tools import (
    docx_set_alignment, docx_set_properties, docx_set_margins,
    docx_format_copy, docx_extract_format_template, docx_apply_format_template
)
from docx_mcp_server.tools.system_tools import docx_server_status
from docx_mcp_server.tools.copy_tools import (
    docx_get_element_source, docx_copy_elements_range
)

# Configure logging (default level can be overridden by env/CLI)
DEFAULT_LOG_LEVEL = os.environ.get("DOCX_MCP_LOG_LEVEL", "INFO").upper()

logging.basicConfig()
logger = logging.getLogger("docx-mcp-server")
try:
    set_global_log_level(DEFAULT_LOG_LEVEL)
except ValueError:
    set_global_log_level(logging.INFO)


def _patch_tool_logging(mcp_instance: FastMCP, log: logging.Logger):
    """Wrap mcp.tool decorator to log tool outputs, pretty-printing JSON if possible."""
    original_tool = mcp_instance.tool

    def tool_with_logging(self, *targs, **tkwargs):
        decorator = original_tool(*targs, **tkwargs)

        def registrar(func):
            @wraps(func)
            def wrapped(*fargs, **fkwargs):
                result = func(*fargs, **fkwargs)
                try:
                    parsed = json.loads(result)
                    pretty = json.dumps(parsed, ensure_ascii=False, indent=2)
                    log.info("Tool %s result:\n%s", func.__name__, pretty)
                except Exception:
                    log.info("Tool %s result: %s", func.__name__, result)
                return result

            return decorator(wrapped)

        return registrar

    mcp_instance.tool = types.MethodType(tool_with_logging, mcp_instance)

# Initialize SessionManager
session_manager = SessionManager()

# Create MCP Server (without host/port to avoid network init during import)
mcp = FastMCP("docx-mcp-server")
_patch_tool_logging(mcp, logger)

# Register all tools
register_all_tools(mcp)

def main():
    """Main entry point for the server with configurable transport"""
    parser = argparse.ArgumentParser(
        description="DOCX MCP Server - Microsoft Word document manipulation via MCP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard I/O mode (default, for Claude Desktop)
  mcp-server-docx
  mcp-server-docx --transport stdio

  # SSE mode (HTTP Server-Sent Events)
  mcp-server-docx --transport sse --host 127.0.0.1 --port 3000

  # Streamable HTTP mode
  mcp-server-docx --transport streamable-http --host 0.0.0.0 --port 8080 --mount-path /mcp

Environment Variables:
  DOCX_MCP_TRANSPORT    : Override transport mode (stdio|sse|streamable-http)
  DOCX_MCP_HOST         : Override host address (default: 127.0.0.1)
  DOCX_MCP_PORT         : Override port number (default: 8000)
  DOCX_MCP_MOUNT_PATH   : Override mount path for HTTP transports
        """
    )

    parser.add_argument(
        "--transport", "-t",
        choices=["stdio", "sse", "streamable-http"],
        default=os.environ.get("DOCX_MCP_TRANSPORT", "stdio"),
        help="Transport protocol to use (default: stdio)"
    )

    parser.add_argument(
        "--host",
        type=str,
        default=os.environ.get("DOCX_MCP_HOST", "127.0.0.1"),
        help="Host address to bind to (default: 127.0.0.1)"
    )

    parser.add_argument(
        "--port", "-p",
        type=int,
        default=int(os.environ.get("DOCX_MCP_PORT", "8000")),
        help="Port number for SSE/HTTP transport (default: 8000)"
    )

    parser.add_argument(
        "--log-level",
        type=lambda s: s.upper(),
        choices=list(LEVEL_NAMES.keys()),
        default=DEFAULT_LOG_LEVEL,
        help="Logging level (default: INFO, override with DOCX_MCP_LOG_LEVEL)"
    )

    parser.add_argument(
        "--mount-path", "-m",
        type=str,
        default=os.environ.get("DOCX_MCP_MOUNT_PATH", None),
        help="Mount path for HTTP transports (e.g., /mcp)"
    )

    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"docx-mcp-server {VERSION}"
    )

    args = parser.parse_args()

    try:
        set_global_log_level(args.log_level)
    except ValueError:
        logger.warning(f"Invalid log level '{args.log_level}', falling back to INFO")
        set_global_log_level(logging.INFO)

    # Print startup information
    logger.info(f"Starting docx-mcp-server v{VERSION}")
    logger.info(f"Transport: {args.transport}")
    logger.info(f"Log level: {logging.getLevelName(logging.getLogger().getEffectiveLevel())}")

    if args.transport in ["sse", "streamable-http"]:
        logger.info(f"Host: {args.host}")
        logger.info(f"Port: {args.port}")
        if args.mount_path:
            logger.info(f"Mount path: {args.mount_path}")
            logger.info(f"Server URL: http://{args.host}:{args.port}{args.mount_path}")
        else:
            logger.info(f"Server URL: http://{args.host}:{args.port}")

    # For non-stdio transports, we need to create a new FastMCP instance with custom host/port
    if args.transport in ["sse", "streamable-http"]:
        # Create a new FastMCP instance with custom configuration
        custom_mcp = FastMCP(
            "docx-mcp-server",
            host=args.host,
            port=args.port
        )
        _patch_tool_logging(custom_mcp, logger)
        # Re-register all tools to the new instance
        register_all_tools(custom_mcp)
        server_instance = custom_mcp
    else:
        # Use the default module-level instance for stdio
        server_instance = mcp

    # Run the server with specified transport
    try:
        if args.transport == "stdio":
            server_instance.run(transport="stdio")
        elif args.transport == "sse":
            server_instance.run(transport="sse", mount_path=args.mount_path)
        elif args.transport == "streamable-http":
            server_instance.run(transport="streamable-http", mount_path=args.mount_path)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.exception(f"Server error: {e}")
        raise

if __name__ == "__main__":
    main()
