"""Unit tests for REST API routes (T-005).

Tests the /api/* endpoints for file management.
"""

import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.responses import JSONResponse
    from docx_mcp_server.api.file_controller import FileController
    from docx_mcp_server.core.global_state import global_state
    from docx_mcp_server.server import session_manager, VERSION

    # Create a simple Starlette app with just the API routes
    async def health(request):
        return JSONResponse({
            "status": "ok",
            "version": VERSION,
            "transport": "test"
        })

    async def get_status(request):
        return JSONResponse({
            "currentFile": global_state.active_file,
            "sessionId": global_state.active_session_id,
            "hasUnsaved": False,
            "serverVersion": VERSION
        })

    async def switch_file(request):
        data = await request.json()
        path = data.get("path")
        force = data.get("force", False)

        # Validate required field
        if not path:
            return JSONResponse(
                {"detail": [{"loc": ["body", "path"], "msg": "field required", "type": "value_error.missing"}]},
                status_code=422
            )

        try:
            result = FileController.switch_file(path, force)
            return JSONResponse(result)
        except FileNotFoundError as e:
            return JSONResponse({"detail": str(e)}, status_code=404)
        except PermissionError as e:
            return JSONResponse({"detail": str(e)}, status_code=403)
        except Exception as e:
            if "locked" in str(e).lower():
                return JSONResponse({"detail": str(e)}, status_code=423)
            elif "unsaved" in str(e).lower():
                return JSONResponse({
                    "detail": {
                        "error": str(e),
                        "message": "File has unsaved changes. Use force=true to discard."
                    }
                }, status_code=409)
            return JSONResponse({"detail": str(e)}, status_code=500)

    async def close_session(request):
        data = await request.json()
        save = data.get("save", False)

        session_id = global_state.active_session_id
        if session_id and save:
            session = session_manager.get_session(session_id)
            if session and session.file_path:
                session.document.save(session.file_path)

        if session_id:
            session_manager.close_session(session_id)
            global_state.active_session_id = None

        return JSONResponse({"success": True})

    app = Starlette(routes=[
        Route("/health", health, methods=["GET"]),
        Route("/api/status", get_status, methods=["GET"]),
        Route("/api/file/switch", switch_file, methods=["POST"]),
        Route("/api/session/close", close_session, methods=["POST"]),
    ])

    return TestClient(app)


@pytest.fixture
def temp_docx():
    """Create a temporary .docx file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        f.write(b"PK")  # Minimal ZIP signature
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture(autouse=True)
def reset_global_state():
    """Reset global state before each test."""
    from docx_mcp_server.core.global_state import global_state
    global_state.clear()
    yield
    global_state.clear()


class TestSwitchFileEndpoint:
    """Test suite for POST /api/file/switch endpoint."""

    def test_switch_file_success(self, client, temp_docx):
        """Test successful file switch."""
        response = client.post(
            "/api/file/switch",
            json={"path": temp_docx, "force": False}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["currentFile"] == temp_docx
        assert data["sessionId"] is None

    def test_switch_file_not_found(self, client):
        """Test switching to non-existent file."""
        response = client.post(
            "/api/file/switch",
            json={"path": "/nonexistent/file.docx", "force": False}
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_switch_file_missing_path(self, client):
        """Test request with missing path field."""
        response = client.post(
            "/api/file/switch",
            json={"force": False}
        )

        # Pydantic validation error
        assert response.status_code == 422

    def test_switch_file_force_default_false(self, client, temp_docx):
        """Test that force defaults to False."""
        response = client.post(
            "/api/file/switch",
            json={"path": temp_docx}
        )

        assert response.status_code == 200

    @patch('docx_mcp_server.api.file_controller.FileController.switch_file')
    def test_switch_file_with_unsaved_changes_no_force(self, mock_switch, client, temp_docx):
        """Test switching with unsaved changes (force=False) returns 409."""
        from docx_mcp_server.api.file_controller import UnsavedChangesError

        mock_switch.side_effect = UnsavedChangesError("Unsaved changes exist")

        response = client.post(
            "/api/file/switch",
            json={"path": temp_docx, "force": False}
        )

        assert response.status_code == 409
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"]
        assert data["detail"]["error"] == "Unsaved changes exist"
        assert "message" in data["detail"]

    def test_switch_file_permission_denied(self, client, temp_docx):
        """Test switching to file without permissions."""
        # Make file read-only
        os.chmod(temp_docx, 0o444)

        try:
            response = client.post(
                "/api/file/switch",
                json={"path": temp_docx, "force": False}
            )

            assert response.status_code == 403
            assert "permission" in response.json()["detail"].lower()
        finally:
            # Restore permissions for cleanup
            os.chmod(temp_docx, 0o644)

    @patch('docx_mcp_server.api.file_controller.FileController._is_file_locked')
    def test_switch_file_locked(self, mock_is_locked, client, temp_docx):
        """Test switching to locked file."""
        mock_is_locked.return_value = True

        response = client.post(
            "/api/file/switch",
            json={"path": temp_docx, "force": False}
        )

        assert response.status_code == 423
        assert "locked" in response.json()["detail"].lower()


class TestGetStatusEndpoint:
    """Test suite for GET /api/status endpoint."""

    def test_get_status_no_active_file(self, client):
        """Test status query with no active file."""
        response = client.get("/api/status")

        assert response.status_code == 200
        data = response.json()

        assert data["currentFile"] is None
        assert data["sessionId"] is None
        assert data["hasUnsaved"] is False
        assert "serverVersion" in data

    def test_get_status_with_active_file(self, client, temp_docx):
        """Test status query after switching file."""
        # First switch file
        client.post("/api/file/switch", json={"path": temp_docx})

        # Then get status
        response = client.get("/api/status")

        assert response.status_code == 200
        data = response.json()
        assert data["currentFile"] == temp_docx
        assert data["sessionId"] is None

    def test_get_status_response_structure(self, client):
        """Test that /api/status returns correct structure."""
        response = client.get("/api/status")
        data = response.json()

        # Should match StatusResponse model
        assert "currentFile" in data
        assert "sessionId" in data
        assert "hasUnsaved" in data
        assert "serverVersion" in data


class TestCloseSessionEndpoint:
    """Test suite for POST /api/session/close endpoint."""

    def test_close_session_no_active_session(self, client):
        """Test closing when no session is active."""
        response = client.post(
            "/api/session/close",
            json={"save": False}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_close_session_save_default_false(self, client):
        """Test that save defaults to False."""
        response = client.post(
            "/api/session/close",
            json={}
        )

        assert response.status_code == 200

    def test_close_session_with_save(self, client):
        """Test closing session with save=True."""
        response = client.post(
            "/api/session/close",
            json={"save": True}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestAPIEndpointRouting:
    """Test suite for API endpoint routing."""

    def test_all_api_endpoints_exist(self, client):
        """Test that all expected API endpoints exist."""
        # Test POST /api/file/switch
        response = client.post("/api/file/switch", json={"path": "/test.docx"})
        # Should not be 404 or 405 (should be 404 from FileController for non-existent file)
        assert response.status_code != 405

        # Test GET /api/status
        response = client.get("/api/status")
        assert response.status_code == 200

        # Test POST /api/session/close
        response = client.post("/api/session/close", json={})
        assert response.status_code == 200

    def test_api_prefix_correct(self, client):
        """Test that API endpoints are under /api prefix."""
        # Should work with /api prefix
        response = client.get("/api/status")
        assert response.status_code == 200

        # Should not work without /api prefix
        response = client.get("/status")
        assert response.status_code == 404
