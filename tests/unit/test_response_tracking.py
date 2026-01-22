"""
Unit tests for Response formatting with change tracking.
"""

import pytest
import json
from docx import Document
from docx_mcp_server.core.session import Session
from docx_mcp_server.core.response import (
    create_change_tracked_response,
    create_success_response
)


def test_create_change_tracked_response():
    """Test creating response with change tracking."""
    session = Session(session_id="test", document=Document())

    changes = {
        "before": {"text": "old text"},
        "after": {"text": "new text"},
        "context": {"parent_id": "document_body"}
    }

    response = create_change_tracked_response(
        session=session,
        message="Updated successfully",
        element_id="para_123",
        changes=changes,
        commit_id="commit-456",
        include_cursor=False
    )

    data = json.loads(response)

    assert data["status"] == "success"
    assert data["message"] == "Updated successfully"
    assert data["data"]["element_id"] == "para_123"
    assert "changes" in data["data"]
    assert data["data"]["changes"]["before"]["text"] == "old text"
    assert data["data"]["commit_id"] == "commit-456"


def test_change_tracked_response_with_extra_data():
    """Test change tracked response with additional data fields."""
    session = Session(session_id="test", document=Document())

    response = create_change_tracked_response(
        session=session,
        message="Operation completed",
        element_id="elem_789",
        changes={"before": {}, "after": {}},
        commit_id="commit-abc",
        include_cursor=False,
        custom_field="custom_value",
        another_field=123
    )

    data = json.loads(response)

    assert data["status"] == "success"
    assert data["data"]["custom_field"] == "custom_value"
    assert data["data"]["another_field"] == 123


def test_backward_compatibility():
    """Test that existing create_success_response still works."""
    response = create_success_response(
        message="Success",
        element_id="elem_123",
        custom_data="value"
    )

    data = json.loads(response)

    assert data["status"] == "success"
    assert data["data"]["element_id"] == "elem_123"
    assert data["data"]["custom_data"] == "value"
