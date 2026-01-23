
# Add parent directory to path for helpers import
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from helpers import (
    extract_session_id,
    extract_element_id,
    extract_metadata_field,
    extract_error_message,
    is_success,
    is_error
)
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
    session_response = docx_create()

    session_id = extract_session_id(session_response)
    result = docx_insert_paragraph(session_id, "Test paragraph", position="end:document_body")

    # Parse JSON
    assert is_success(result)
    # assert data["message"] == "Paragraph created successfully"
    assert extract_metadata_field(result, "element_id") is not None
    assert extract_metadata_field(result, "element_id").startswith("para_")

    docx_close(session_id)


def test_add_paragraph_with_style():
    """Test adding paragraph with style returns proper JSON."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)
    result = docx_insert_paragraph(session_id, "Bullet item", position="end:document_body", style="List Bullet")
    assert is_success(result)
    assert extract_metadata_field(result, "element_id") is not None

    docx_close(session_id)


def test_add_paragraph_invalid_session():
    """Test that invalid session returns error JSON."""
    result = docx_insert_paragraph("invalid_session", "Test", position="end:document_body")
    assert is_error(result)
    # assert "not found" in data["message"].lower()
    assert extract_metadata_field(result, "error_type") == "SessionNotFound"


def test_add_heading_returns_json():
    """Test that docx_insert_heading returns valid JSON."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)
    result = docx_insert_heading(session_id, "Chapter 1", position="end:document_body", level=1)
    assert is_success(result)
    # assert "Heading level 1" in data["message"]
    assert extract_metadata_field(result, "element_id") is not None
    assert extract_metadata_field(result, "element_id").startswith("para_")

    docx_close(session_id)


def test_add_heading_with_different_levels():
    """Test adding headings with different levels."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)

    # Title (level 0)
    result = docx_insert_heading(session_id, "Title", position="end:document_body", level=0)
    assert is_success(result)

    # Heading 2
    result = docx_insert_heading(session_id, "Section", position="end:document_body", level=2)
    assert is_success(result)

    docx_close(session_id)


def test_update_paragraph_text_returns_json():
    """Test that docx_update_paragraph_text returns valid JSON."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)

    # Create paragraph
    result = docx_insert_paragraph(session_id, "Old text", position="end:document_body")
    para_id = extract_element_id(result)

    # Update it
    result = docx_update_paragraph_text(session_id, para_id, "New text")

    assert is_success(result)
    assert extract_metadata_field(result, "element_id") == para_id
    assert extract_metadata_field(result, "changed_fields") is not None

    docx_close(session_id)


def test_update_paragraph_invalid_id():
    """Test updating non-existent paragraph returns error."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)
    result = docx_update_paragraph_text(session_id, "para_invalid", "New text")
    assert is_error(result)
    assert extract_metadata_field(result, "error_type") == "ElementNotFound"

    docx_close(session_id)


def test_copy_paragraph_returns_json():
    """Test that docx_copy_paragraph returns valid JSON."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)

    # Create original paragraph
    result = docx_insert_paragraph(session_id, "Original text", position="end:document_body")
    original_id = extract_element_id(result)

    # Copy it
    result = docx_copy_paragraph(session_id, original_id, position="end:document_body")

    assert is_success(result)
    # assert "copied successfully" in data["message"]
    assert extract_metadata_field(result, "element_id") is not None
    assert extract_element_id(result) != original_id
    # Source ID is tracked in metadata
    assert extract_element_id(result) != original_id

    docx_close(session_id)


def test_delete_paragraph_returns_json():
    """Test that docx_delete returns valid JSON."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)

    # Create paragraph
    result = docx_insert_paragraph(session_id, "To be deleted", position="end:document_body")
    para_id = extract_element_id(result)

    # Delete it
    result = docx_delete(session_id, para_id)

    assert is_success(result)
    # assert "Deleted" in data["message"]
    assert extract_metadata_field(result, "deleted_id") == para_id

    docx_close(session_id)


def test_delete_without_element_id_uses_context():
    """Test that delete without element_id uses context."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)

    # Create paragraph (sets context)
    result = docx_insert_paragraph(session_id, "Context paragraph", position="end:document_body")
    para_id = extract_element_id(result)

    # Delete using context
    result = docx_delete(session_id)

    assert is_success(result)
    assert extract_metadata_field(result, "deleted_id") == para_id

    docx_close(session_id)


def test_delete_no_context_returns_error():
    """Test that delete without context returns error."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)

    # Try to delete without any context
    result = docx_delete(session_id)

    assert is_error(result)
    assert extract_metadata_field(result, "error_type") == "NoContext"

    docx_close(session_id)


def test_add_page_break_returns_json():
    """Test that docx_insert_page_break returns valid JSON."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)
    result = docx_insert_page_break(session_id, position="end:document_body")
    assert is_success(result)
    # assert "Page break" in data["message"]

    docx_close(session_id)


def test_cursor_context_in_response():
    """Test that cursor context is included in responses."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)

    # Add first paragraph
    docx_insert_paragraph(session_id, "First", position="end:document_body")

    # Add second paragraph
    result = docx_insert_paragraph(session_id, "Second", position="end:document_body")

    # Check that response includes document context (cursor is shown in context)
    assert is_success(result)
    assert "Document Context" in result or "CURSOR" in result

    docx_close(session_id)


def test_json_response_structure():
    """Test that all responses follow the standard structure."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)

    # Test various operations
    operations = [
        docx_insert_paragraph(session_id, "Test", position="end:document_body"),
        docx_insert_heading(session_id, "Heading", position="end:document_body", level=1),
        docx_insert_page_break(session_id, position="end:document_body")
    ]

    for result in operations:
        # All responses must be successful and have element_id
        assert is_success(result)
        assert extract_element_id(result) is not None

    docx_close(session_id)


def test_error_response_structure():
    """Test that error responses follow the standard structure."""
    # Test with invalid session
    result = docx_insert_paragraph("invalid", "Test", position="end:document_body")

    assert is_error(result)
    assert extract_error_message(result) is not None
    assert extract_metadata_field(result, "error_type") is not None


def test_add_paragraph_to_parent():
    """Test adding paragraph to a parent container (cell)."""
    from docx_mcp_server.tools.table_tools import docx_insert_table, docx_get_cell

    session_response = docx_create()


    session_id = extract_session_id(session_response)

    # Create table
    table_result = docx_insert_table(session_id, 2, 2, position="end:document_body")
    table_id = extract_element_id(table_result)

    # Get cell
    cell_result = docx_get_cell(session_id, table_id, 0, 0)
    cell_id = extract_element_id(cell_result)

    # Add paragraph to cell
    result = docx_insert_paragraph(session_id, "Cell content", position=f"inside:{cell_id}")

    assert is_success(result)
    assert extract_metadata_field(result, "element_id") is not None

    docx_close(session_id)
