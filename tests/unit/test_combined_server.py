"""Unit tests for combined_server.py (T-004).

Tests FastAPI app initialization, health endpoint, and MCP mounting.
"""

import pytest
from fastapi.testclient import TestClient
from docx_mcp_server.combined_server import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestHealthEndpoint:
    """Test suite for /health endpoint."""

    def test_health_endpoint_exists(self, client):
        """Test that /health endpoint exists."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_response_structure(self, client):
        """Test that /health returns correct structure."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "transport" in data
        assert "endpoints" in data

    def test_health_endpoint_status_healthy(self, client):
        """Test that /health returns healthy status."""
        response = client.get("/health")
        data = response.json()

        assert data["status"] == "healthy"

    def test_health_endpoint_transport_combined(self, client):
        """Test that /health returns transport=combined."""
        response = client.get("/health")
        data = response.json()

        assert data["transport"] == "combined"

    def test_health_endpoint_includes_endpoints(self, client):
        """Test that /health includes endpoints information."""
        response = client.get("/health")
        data = response.json()

        endpoints = data["endpoints"]
        assert "rest_api" in endpoints
        assert "mcp" in endpoints
        assert "health" in endpoints
        assert "docs" in endpoints


class TestMCPMount:
    """Test suite for MCP mounting."""

    def test_mcp_endpoint_exists(self, client):
        """Test that /mcp endpoint exists (not 404)."""
        response = client.get("/mcp")
        # MCP might return various responses, but should not be 404
        assert response.status_code != 404

    def test_mcp_mounted_at_correct_path(self, client):
        """Test that MCP is mounted at /mcp path."""
        # Try to access /mcp - should not return 404
        response = client.get("/mcp")
        assert response.status_code != 404

        # Try to access /mcp/ with trailing slash
        response = client.get("/mcp/")
        assert response.status_code != 404


class TestFastAPIApp:
    """Test suite for FastAPI app configuration."""

    def test_app_title(self):
        """Test that app has correct title."""
        assert app.title == "Docx MCP Server"

    def test_app_has_docs_url(self):
        """Test that app has docs URL configured."""
        assert app.docs_url == "/docs"

    def test_app_has_redoc_url(self):
        """Test that app has redoc URL configured."""
        assert app.redoc_url == "/redoc"

    def test_docs_endpoint_accessible(self, client):
        """Test that /docs endpoint is accessible."""
        response = client.get("/docs")
        # Should return HTML documentation
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")


class TestServerConfiguration:
    """Test suite for server configuration."""

    def test_app_instance_exists(self):
        """Test that FastAPI app instance exists."""
        assert app is not None

    def test_app_has_routes(self):
        """Test that app has routes configured."""
        routes = [route.path for route in app.routes]

        # Should have at least health and mcp routes
        assert any("/health" in path for path in routes)
        # MCP mount creates a route
        assert any("/mcp" in path for path in routes)
