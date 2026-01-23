"""Unit tests for refactored cursor and advanced tools with JSON responses."""

import json
import pytest
import tempfile
import os
import sys

# Add parent directory to path for helpers import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from helpers import (
    extract_session_id,
    extract_element_id,
    extract_metadata_field,
    is_success,
    is_error,
    extract_error_message
)
from docx_mcp_server.tools.cursor_tools import (
    docx_cursor_get,
    docx_cursor_move
)
from docx_mcp_server.tools.advanced_tools import (
    docx_replace_text,
    docx_batch_replace_text,
    docx_insert_image
)
from docx_mcp_server.tools.paragraph_tools import docx_insert_paragraph
from docx_mcp_server.tools.session_tools import docx_create, docx_close


def test_cursor_get_returns_json():
    """Test that docx_cursor_get returns valid JSON."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)

    result = docx_cursor_get(session_id)

    assert is_success(result)
    assert extract_metadata_field(result, "parent_id") is not None
    # element_id can be None for empty document
    assert extract_metadata_field(result, "position") is not None
    assert extract_metadata_field(result, "description") is not None
    assert extract_metadata_field(result, "context") is not None

    docx_close(session_id)


def test_cursor_move_returns_json():
    """Test that docx_cursor_move returns valid JSON."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)
    para_id = extract_element_id(docx_insert_paragraph(session_id, "Test", position="end:document_body"))

    result = docx_cursor_move(session_id, para_id, "after")

    assert is_success(result)
    assert extract_metadata_field(result, "element_id") is not None
    assert extract_metadata_field(result, "element_id") == para_id

    docx_close(session_id)


def test_cursor_move_invalid_position():
    """Test that docx_cursor_move returns error for invalid position."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)
    para_id = extract_element_id(docx_insert_paragraph(session_id, "Test", position="end:document_body"))

    result = docx_cursor_move(session_id, para_id, "invalid")

    assert is_error(result)
    assert extract_metadata_field(result, "error_type") == "ValidationError"

    docx_close(session_id)


def test_replace_text_returns_json():
    """Test that docx_replace_text returns valid JSON."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)
    docx_insert_paragraph(session_id, "Hello {{NAME}}, welcome!", position="end:document_body")

    result = docx_replace_text(session_id, "{{NAME}}", "John")

    assert is_success(result)
    assert extract_metadata_field(result, "replacements") is not None
    assert extract_metadata_field(result, "replacements") == 1
    assert "{{NAME}}" in result  # Check for text in diff/content
    assert extract_metadata_field(result, "new_text") == "John"

    docx_close(session_id)


def test_replace_text_no_matches():
    """Test that docx_replace_text returns 0 replacements when no matches."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)
    docx_insert_paragraph(session_id, "Hello World", position="end:document_body")

    result = docx_replace_text(session_id, "{{NAME}}", "John")

    assert is_success(result)
    assert extract_metadata_field(result, "replacements") == 0

    docx_close(session_id)


def test_batch_replace_text_returns_json():
    """Test that docx_batch_replace_text returns valid JSON."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)
    docx_insert_paragraph(session_id, "Hello {{NAME}}, today is {{DATE}}", position="end:document_body")

    replacements = json.dumps({"{{NAME}}": "Alice", "{{DATE}}": "2023-01-01"})
    result = docx_batch_replace_text(session_id, replacements)

    assert is_success(result)
    assert extract_metadata_field(result, "replacements") is not None
    assert extract_metadata_field(result, "replacements") >= 2
    assert extract_metadata_field(result, "patterns") == 2

    docx_close(session_id)


def test_batch_replace_text_invalid_json():
    """Test that docx_batch_replace_text returns error for invalid JSON."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)

    result = docx_batch_replace_text(session_id, "not valid json")

    assert is_error(result)
    assert extract_metadata_field(result, "error_type") == "ValidationError"

    docx_close(session_id)


def test_insert_image_returns_json():
    """Test that docx_insert_image returns valid JSON."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)

    # Create a temporary test image
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        # Write minimal PNG header
        tmp.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')
        tmp_path = tmp.name

    try:
        result = docx_insert_image(session_id, tmp_path, width=2.0, position="end:document_body")

        assert is_success(result)
        assert extract_metadata_field(result, "element_id") is not None
        assert extract_metadata_field(result, "image_path") == tmp_path
    finally:
        os.unlink(tmp_path)
        docx_close(session_id)


def test_insert_image_file_not_found():
    """Test that docx_insert_image returns error for missing file."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)

    result = docx_insert_image(session_id, "/nonexistent/image.png", position="end:document_body")

    assert is_error(result)
    assert extract_metadata_field(result, "error_type") == "FileNotFound"

    docx_close(session_id)


def test_cursor_move_to_document_body():
    """Test moving cursor to document body."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)

    result = docx_cursor_move(session_id, "document_body", "inside_end")

    assert is_success(result)
    assert extract_metadata_field(result, "element_id") == "document_body"

    docx_close(session_id)


def test_cursor_move_invalid_element():
    """Test that docx_cursor_move returns error for invalid element."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)

    result = docx_cursor_move(session_id, "para_nonexistent", "after")

    assert is_error(result)
    assert extract_metadata_field(result, "error_type") == "ElementNotFound"

    docx_close(session_id)
