"""Standalone HTTP REST API Server for Launcher communication.

This is a lightweight FastAPI server that provides REST endpoints for
the Launcher GUI to manage file operations. It runs on a separate port
from the MCP server.

Architecture:
    - MCP Server (SSE): Port 8000 (for Claude Desktop)
    - HTTP API Server: Port 8001 (for Launcher GUI)

Endpoints:
    - GET  /health          - Health check
    - POST /api/file/switch - Switch active file
    - GET  /api/status      - Get server status
    - POST /api/session/close - Close current session
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging
import uvicorn

logger = logging.getLogger(__name__)

# Import global state and controllers
from docx_mcp_server.core.global_state import global_state
from docx_mcp_server.api.file_controller import (
    FileController,
    FileLockError,
    UnsavedChangesError
)

# Get version
from docx_mcp_server.server import VERSION

# ============================================================================
# Pydantic Models
# ============================================================================

class SwitchFileRequest(BaseModel):
    """Request model for file switch endpoint."""
    path: str
    force: bool = False


class CloseSessionRequest(BaseModel):
    """Request model for session close endpoint."""
    save: bool = False


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Docx MCP Server - HTTP API",
    description="REST API for Launcher file management",
    version=VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"HTTP API Server initialized (version {VERSION})")


# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint for Launcher to verify server is running.

    Returns:
        dict: Health status, version, and current file info
    """
    return {
        "status": "healthy",
        "version": VERSION,
        "transport": "http-api",
        "activeFile": global_state.active_file,
        "activeSessionId": global_state.active_session_id
    }


# ============================================================================
# File Management Endpoints
# ============================================================================

@app.post("/api/file/switch")
async def switch_file(request: SwitchFileRequest):
    """Switch to a different active file.

    Args:
        request: Contains path (file path) and force (bool)

    Returns:
        dict: Success response with current file info

    Raises:
        HTTPException 404: File not found
        HTTPException 403: Permission denied
        HTTPException 423: File is locked
        HTTPException 409: Unsaved changes (if force=False)
    """
    try:
        result = FileController.switch_file(request.path, force=request.force)
        logger.info(f"File switched to: {request.path}")
        return result

    except FileNotFoundError as e:
        logger.error(f"File not found: {request.path}")
        raise HTTPException(status_code=404, detail=str(e))

    except PermissionError as e:
        logger.error(f"Permission denied: {request.path}")
        raise HTTPException(status_code=403, detail=str(e))

    except FileLockError as e:
        logger.error(f"File locked: {request.path}")
        raise HTTPException(status_code=423, detail=str(e))

    except UnsavedChangesError as e:
        logger.warning(f"Unsaved changes: {request.path}")
        raise HTTPException(status_code=409, detail=str(e))

    except Exception as e:
        logger.exception(f"Error switching file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status")
async def get_status():
    """Get current server status and active file info.

    Returns:
        dict: Current file, session ID, and unsaved changes status
    """
    result = FileController.get_status()
    logger.debug(f"Status query: {result}")
    return result


@app.post("/api/session/close")
async def close_session(request: CloseSessionRequest):
    """Close the current session.

    Args:
        request: Contains save (bool) - whether to save before closing

    Returns:
        dict: Success message

    Raises:
        HTTPException 404: No active session
    """
    try:
        FileController.close_session(save=request.save)
        logger.info(f"Session closed (save={request.save})")
        return {"message": "Session closed successfully"}

    except ValueError as e:
        logger.error(f"No active session: {e}")
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        logger.exception(f"Error closing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    logger.info("=" * 70)
    logger.info("HTTP API Server Starting")
    logger.info("=" * 70)
    logger.info(f"  Version: {VERSION}")
    logger.info(f"  Endpoints:")
    logger.info(f"    - Health: /health")
    logger.info(f"    - File Switch: /api/file/switch")
    logger.info(f"    - Status: /api/status")
    logger.info(f"    - Close Session: /api/session/close")
    logger.info(f"    - Docs: /docs")
    logger.info("=" * 70)


@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown information."""
    logger.info("HTTP API Server shutting down")


# ============================================================================
# Main Function
# ============================================================================

def run_http_api_server(host: str = "0.0.0.0", port: int = 8001):
    """Run the HTTP API server.

    Args:
        host: Host to bind to (default: 0.0.0.0)
        port: Port to listen on (default: 8001)
    """
    logger.info(f"Starting HTTP API server on http://{host}:{port}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    # For testing and standalone mode
    import argparse

    parser = argparse.ArgumentParser(description="Docx MCP HTTP API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8001, help="Port to listen on")
    args = parser.parse_args()

    run_http_api_server(host=args.host, port=args.port)
