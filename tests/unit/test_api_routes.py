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
    # Import server and create a test instance with custom routes
    from docx_mcp_server.server import mcp
    from mcp.server.fastmcp import FastMCP

    # Create a test FastMCP instance
    test_mcp = FastMCP("docx-mcp-server-test", host="127.0.0.1", port=8000)

    # Register custom routes
    from docx_mcp_server.server import register_custom_routes
    register_custom_routes(test_mcp)

    # Get the underlying FastAPI app
    return TestClient(test_mcp.app)


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
