"""Unit tests for refactored paragraph tools with JSON responses."""

import json
import pytest
from docx_mcp_server.tools.paragraph_tools import (
    docx_insert_paragraph,
    docx_insert_heading,
    docx_update_paragraph_text,
    docx_copy_paragraph,
    docx_delete,
    docx_insert_page_break
)
from docx_mcp_server.tools.session_tools import docx_create, docx_close


def test_add_paragraph_returns_json():
    """Test that docx_insert_paragraph returns valid JSON."""
    session_id = docx_create()
    result = docx_insert_paragraph(session_id, "Test paragraph", position="end:document_body")

    # Parse JSON
    data = json.loads(result)

    assert data["status"] == "success"
    assert data["message"] == "Paragraph created successfully"
    assert "element_id" in data["data"]
    assert data["data"]["element_id"].startswith("para_")
    assert "cursor" in data["data"]

    docx_close(session_id)


def test_add_paragraph_with_style():
    """Test adding paragraph with style returns proper JSON."""
    session_id = docx_create()
    result = docx_insert_paragraph(session_id, "Bullet item", position="end:document_body", style="List Bullet")

    data = json.loads(result)
    assert data["status"] == "success"
    assert "element_id" in data["data"]

    docx_close(session_id)


def test_add_paragraph_invalid_session():
    """Test that invalid session returns error JSON."""
    result = docx_insert_paragraph("invalid_session", "Test", position="end:document_body")

    data = json.loads(result)
    assert data["status"] == "error"
    assert "not found" in data["message"].lower()
    assert data["data"]["error_type"] == "SessionNotFound"


def test_add_heading_returns_json():
    """Test that docx_insert_heading returns valid JSON."""
    session_id = docx_create()
    result = docx_insert_heading(session_id, "Chapter 1", position="end:document_body", level=1)

    data = json.loads(result)
    assert data["status"] == "success"
    assert "Heading level 1" in data["message"]
    assert "element_id" in data["data"]
    assert data["data"]["element_id"].startswith("para_")

    docx_close(session_id)


def test_add_heading_with_different_levels():
    """Test adding headings with different levels."""
    session_id = docx_create()

    # Title (level 0)
    result = docx_insert_heading(session_id, "Title", position="end:document_body", level=0)
    data = json.loads(result)
    assert data["status"] == "success"

    # Heading 2
    result = docx_insert_heading(session_id, "Section", position="end:document_body", level=2)
    data = json.loads(result)
    assert data["status"] == "success"

    docx_close(session_id)


def test_update_paragraph_text_returns_json():
    """Test that docx_update_paragraph_text returns valid JSON."""
    session_id = docx_create()

    # Create paragraph
    result = docx_insert_paragraph(session_id, "Old text", position="end:document_body")
    data = json.loads(result)
    para_id = data["data"]["element_id"]

    # Update it
    result = docx_update_paragraph_text(session_id, para_id, "New text")
    data = json.loads(result)

    assert data["status"] == "success"
    assert "updated successfully" in data["message"]
    assert data["data"]["element_id"] == para_id
    assert "changed_fields" in data["data"]
    assert "text" in data["data"]["changed_fields"]

    docx_close(session_id)


def test_update_paragraph_invalid_id():
    """Test updating non-existent paragraph returns error."""
    session_id = docx_create()
    result = docx_update_paragraph_text(session_id, "para_invalid", "New text")

    data = json.loads(result)
    assert data["status"] == "error"
    assert data["data"]["error_type"] == "ElementNotFound"

    docx_close(session_id)


def test_copy_paragraph_returns_json():
    """Test that docx_copy_paragraph returns valid JSON."""
    session_id = docx_create()

    # Create original paragraph
    result = docx_insert_paragraph(session_id, "Original text", position="end:document_body")
    data = json.loads(result)
    original_id = data["data"]["element_id"]

    # Copy it
    result = docx_copy_paragraph(session_id, original_id, position="end:document_body")
    data = json.loads(result)

    assert data["status"] == "success"
    assert "copied successfully" in data["message"]
    assert "element_id" in data["data"]
    assert data["data"]["element_id"] != original_id
    assert data["data"]["source_id"] == original_id

    docx_close(session_id)


def test_delete_paragraph_returns_json():
    """Test that docx_delete returns valid JSON."""
    session_id = docx_create()

    # Create paragraph
    result = docx_insert_paragraph(session_id, "To be deleted", position="end:document_body")
    data = json.loads(result)
    para_id = data["data"]["element_id"]

    # Delete it
    result = docx_delete(session_id, para_id)
    data = json.loads(result)

    assert data["status"] == "success"
    assert "Deleted" in data["message"]
    assert data["data"]["deleted_id"] == para_id

    docx_close(session_id)


def test_delete_without_element_id_uses_context():
    """Test that delete without element_id uses context."""
    session_id = docx_create()

    # Create paragraph (sets context)
    result = docx_insert_paragraph(session_id, "Context paragraph", position="end:document_body")
    data = json.loads(result)
    para_id = data["data"]["element_id"]

    # Delete using context
    result = docx_delete(session_id)
    data = json.loads(result)

    assert data["status"] == "success"
    assert data["data"]["deleted_id"] == para_id

    docx_close(session_id)


def test_delete_no_context_returns_error():
    """Test that delete without context returns error."""
    session_id = docx_create()

    # Try to delete without any context
    result = docx_delete(session_id)
    data = json.loads(result)

    assert data["status"] == "error"
    assert data["data"]["error_type"] == "NoContext"

    docx_close(session_id)


def test_add_page_break_returns_json():
    """Test that docx_insert_page_break returns valid JSON."""
    session_id = docx_create()
    result = docx_insert_page_break(session_id, position="end:document_body")

    data = json.loads(result)
    assert data["status"] == "success"
    assert "Page break" in data["message"]

    docx_close(session_id)


def test_cursor_context_in_response():
    """Test that cursor context is included in responses."""
    session_id = docx_create()

    # Add first paragraph
    docx_insert_paragraph(session_id, "First", position="end:document_body")

    # Add second paragraph
    result = docx_insert_paragraph(session_id, "Second", position="end:document_body")
    data = json.loads(result)

    # Check cursor information
    assert "cursor" in data["data"]
    cursor = data["data"]["cursor"]
    assert "element_id" in cursor
    assert cursor["position"] == "after"
    assert "context" in cursor

    docx_close(session_id)


def test_json_response_structure():
    """Test that all responses follow the standard structure."""
    session_id = docx_create()

    # Test various operations
    operations = [
        docx_insert_paragraph(session_id, "Test", position="end:document_body"),
        docx_insert_heading(session_id, "Heading", position="end:document_body", level=1),
        docx_insert_page_break(session_id, position="end:document_body")
    ]

    for result in operations:
        data = json.loads(result)

        # All responses must have these fields
        assert "status" in data
        assert "message" in data
        assert "data" in data
        assert isinstance(data["data"], dict)

    docx_close(session_id)


def test_error_response_structure():
    """Test that error responses follow the standard structure."""
    # Test with invalid session
    result = docx_insert_paragraph("invalid", "Test", position="end:document_body")
    data = json.loads(result)

    assert data["status"] == "error"
    assert "message" in data
    assert "data" in data
    assert "error_type" in data["data"]


def test_add_paragraph_to_parent():
    """Test adding paragraph to a parent container (cell)."""
    from docx_mcp_server.tools.table_tools import docx_insert_table, docx_get_cell

    session_id = docx_create()

    # Create table
    table_result = docx_insert_table(session_id, 2, 2, position="end:document_body")
    table_data = json.loads(table_result)
    table_id = table_data["data"]["element_id"]

    # Get cell
    cell_result = docx_get_cell(session_id, table_id, 0, 0)
    cell_data = json.loads(cell_result)
    cell_id = cell_data["data"]["element_id"]

    # Add paragraph to cell
    result = docx_insert_paragraph(session_id, "Cell content", position=f"inside:{cell_id}")
    data = json.loads(result)

    assert data["status"] == "success"
    assert "element_id" in data["data"]

    docx_close(session_id)
