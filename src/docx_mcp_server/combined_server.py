"""Combined FastAPI + MCP Server.

This module provides a combined server that exposes both:
1. REST API endpoints (for Launcher HTTP communication)
2. MCP tools (mounted at /mcp for Claude Desktop)

Architecture:
    FastAPI (main app)
    ├─ /api/*       → REST endpoints (file management)
    ├─ /health      → Health check endpoint
    └─ /mcp         → Mounted MCP server (ASGI app)

Usage:
    # Start combined server
    python -m docx_mcp_server --transport combined --port 8080

    # Access REST API
    curl http://localhost:8080/api/status

    # Access MCP tools
    # (via Claude Desktop configured with http://localhost:8080/mcp)
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Import MCP server instance from main server module
from docx_mcp_server.server import mcp, VERSION
from docx_mcp_server.api.file_controller import (
    FileController,
    FileLockError,
    UnsavedChangesError
)

# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Docx MCP Server",
    description="Combined REST API and MCP server for Word document manipulation",
    version=VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

logger.info(f"FastAPI application initialized (version {VERSION})")

# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and Launcher.

    Returns:
        dict: Server status information including version and transport mode

    Example:
        >>> import requests
        >>> response = requests.get("http://localhost:8080/health")
        >>> print(response.json())
        {'status': 'healthy', 'version': '3.0.0', 'transport': 'combined'}
    """
    return {
        "status": "healthy",
        "version": VERSION,
        "transport": "combined",
        "endpoints": {
            "rest_api": "/api",
            "mcp": "/mcp",
            "health": "/health",
            "docs": "/docs"
        }
    }

logger.info("Health check endpoint registered at /health")

# ============================================================================
# Pydantic Models for REST API
# ============================================================================

class SwitchFileRequest(BaseModel):
    """Request model for file switching."""
    path: str
    force: bool = False

class CloseSessionRequest(BaseModel):
    """Request model for closing session."""
    save: bool = False

class StatusResponse(BaseModel):
    """Response model for status query."""
    currentFile: Optional[str]
    sessionId: Optional[str]
    hasUnsaved: bool
    serverVersion: str

# ============================================================================
# REST API Endpoints
# ============================================================================

@app.post("/api/file/switch")
async def switch_file(request: SwitchFileRequest):
    """Switch to a new active file.

    This endpoint allows the Launcher to change the currently active file.
    It performs validation checks and handles unsaved changes protection.

    Args:
        request: SwitchFileRequest with path and optional force flag

    Returns:
        dict: Status information with currentFile and sessionId

    Raises:
        HTTPException 404: File not found
        HTTPException 403: Permission denied
        HTTPException 423: File is locked
        HTTPException 409: Unsaved changes exist (use force=true to override)

    Example:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8080/api/file/switch",
        ...     json={"path": "/path/to/doc.docx", "force": false}
        ... )
        >>> print(response.json())
        {'currentFile': '/path/to/doc.docx', 'sessionId': None}
    """
    try:
        result = FileController.switch_file(request.path, request.force)
        logger.info(f"File switched successfully: {request.path}")
        return result
    except FileNotFoundError as e:
        logger.warning(f"File not found: {request.path}")
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        logger.warning(f"Permission denied: {request.path}")
        raise HTTPException(status_code=403, detail=str(e))
    except FileLockError as e:
        logger.warning(f"File locked: {request.path}")
        raise HTTPException(status_code=423, detail=str(e))
    except UnsavedChangesError as e:
        logger.warning(f"Unsaved changes: {str(e)}")
        current_status = FileController.get_status()
        raise HTTPException(
            status_code=409,
            detail={
                "error": "Unsaved changes exist",
                "currentFile": current_status.get("currentFile"),
                "message": "Call with force=true to discard changes"
            }
        )
    except ValueError as e:
        logger.error(f"Invalid request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error in switch_file: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Get current server status.

    Returns information about the currently active file, session,
    and whether there are unsaved changes.

    Returns:
        StatusResponse: Current status information

    Example:
        >>> import requests
        >>> response = requests.get("http://localhost:8080/api/status")
        >>> print(response.json())
        {
            'currentFile': '/path/to/doc.docx',
            'sessionId': 'abc-123',
            'hasUnsaved': true,
            'serverVersion': '3.0.0'
        }
    """
    try:
        status = FileController.get_status()
        return status
    except Exception as e:
        logger.exception(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@app.post("/api/session/close")
async def close_session(request: CloseSessionRequest):
    """Close the active session.

    Optionally saves the document before closing the session.

    Args:
        request: CloseSessionRequest with optional save flag

    Returns:
        dict: Result with success status and message

    Example:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8080/api/session/close",
        ...     json={"save": true}
        ... )
        >>> print(response.json())
        {'success': True, 'message': 'Session closed successfully'}
    """
    try:
        result = FileController.close_session(request.save)
        logger.info(f"Session closed (save={request.save})")
        return result
    except Exception as e:
        logger.exception(f"Error closing session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to close session: {str(e)}")

logger.info("REST API endpoints registered at /api/*")

# ============================================================================
# Mount MCP Server
# ============================================================================

# Mount MCP server at /mcp path
# This makes all MCP tools available through the /mcp endpoint
# Claude Desktop can connect to http://localhost:8080/mcp
try:
    app.mount("/mcp", mcp.get_asgi_app(path="/mcp"))
    logger.info("MCP server mounted at /mcp")
except Exception as e:
    logger.error(f"Failed to mount MCP server: {e}")
    raise

# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Called when the server starts."""
    logger.info("=" * 70)
    logger.info("Combined Server Starting")
    logger.info("=" * 70)
    logger.info(f"  Version: {VERSION}")
    logger.info(f"  REST API: /api/*")
    logger.info(f"  MCP Tools: /mcp")
    logger.info(f"  Health: /health")
    logger.info(f"  Docs: /docs")
    logger.info("=" * 70)

@app.on_event("shutdown")
async def shutdown_event():
    """Called when the server shuts down."""
    logger.info("Combined Server Shutting Down")

# ============================================================================
# Main Entry Point
# ============================================================================

def run_combined_server(host: str = "127.0.0.1", port: int = 8080):
    """Run the combined FastAPI + MCP server.

    This function starts a uvicorn server with the FastAPI app,
    which includes both REST API endpoints and the mounted MCP server.

    Args:
        host: Host address to bind to (default: 127.0.0.1)
        port: Port number to listen on (default: 8080)

    Example:
        >>> from docx_mcp_server.combined_server import run_combined_server
        >>> run_combined_server(host="0.0.0.0", port=8080)
    """
    import uvicorn

    logger.info("=" * 70)
    logger.info(f"Starting Combined Server at http://{host}:{port}")
    logger.info("=" * 70)
    logger.info(f"  - REST API: http://{host}:{port}/api/")
    logger.info(f"  - MCP endpoint: http://{host}:{port}/mcp")
    logger.info(f"  - Health check: http://{host}:{port}/health")
    logger.info(f"  - API docs: http://{host}:{port}/docs")
    logger.info("=" * 70)

    # Run uvicorn server
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    # Allow running this module directly for testing
    run_combined_server()
