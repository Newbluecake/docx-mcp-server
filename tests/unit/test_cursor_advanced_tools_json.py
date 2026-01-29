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
from tests.helpers.session_helpers import setup_active_session, teardown_active_session


def test_cursor_get_returns_json():
    """Test that docx_cursor_get returns valid JSON."""
    setup_active_session()
    result = docx_cursor_get()

    assert is_success(result)
    assert extract_metadata_field(result, "parent_id") is not None
    # element_id can be None for empty document
    assert extract_metadata_field(result, "position") is not None
    assert extract_metadata_field(result, "description") is not None
    assert extract_metadata_field(result, "context") is not None

    teardown_active_session()


def test_cursor_move_returns_json():
    """Test that docx_cursor_move returns valid JSON."""
    setup_active_session()
    para_id = extract_element_id(docx_insert_paragraph("Test", position="end:document_body"))

    result = docx_cursor_move(para_id, "after")

    assert is_success(result)
    assert extract_metadata_field(result, "element_id") is not None
    assert extract_metadata_field(result, "element_id") == para_id

    teardown_active_session()


def test_cursor_move_invalid_position():
    """Test that docx_cursor_move returns error for invalid position."""
    setup_active_session()
    para_id = extract_element_id(docx_insert_paragraph("Test", position="end:document_body"))

    result = docx_cursor_move(para_id, "invalid")

    assert is_error(result)
    assert extract_metadata_field(result, "error_type") == "ValidationError"

    teardown_active_session()


def test_replace_text_returns_json():
    """Test that docx_replace_text returns valid JSON."""
    setup_active_session()
    docx_insert_paragraph("Hello {{NAME}}, welcome!", position="end:document_body")

    result = docx_replace_text("{{NAME}}", "John")

    assert is_success(result)
    assert extract_metadata_field(result, "replacements") is not None
    assert extract_metadata_field(result, "replacements") == 1
    assert "{{NAME}}" in result  # Check for text in diff/content
    assert extract_metadata_field(result, "new_text") == "John"

    teardown_active_session()


def test_replace_text_no_matches():
    """Test that docx_replace_text returns 0 replacements when no matches."""
    setup_active_session()
    docx_insert_paragraph("Hello World", position="end:document_body")

    result = docx_replace_text("{{NAME}}", "John")

    assert is_success(result)
    assert extract_metadata_field(result, "replacements") == 0

    teardown_active_session()


def test_batch_replace_text_returns_json():
    """Test that docx_batch_replace_text returns valid JSON."""
    setup_active_session()
    docx_insert_paragraph("Hello {{NAME}}, today is {{DATE}}", position="end:document_body")

    replacements = json.dumps({"{{NAME}}": "Alice", "{{DATE}}": "2023-01-01"})
    result = docx_batch_replace_text(replacements)

    assert is_success(result)
    assert extract_metadata_field(result, "replacements") is not None
    assert extract_metadata_field(result, "replacements") >= 2
    assert extract_metadata_field(result, "patterns") == 2

    teardown_active_session()


def test_batch_replace_text_invalid_json():
    """Test that docx_batch_replace_text returns error for invalid JSON."""
    setup_active_session()
    result = docx_batch_replace_text("not valid json")

    assert is_error(result)
    assert extract_metadata_field(result, "error_type") == "ValidationError"

    teardown_active_session()


def test_insert_image_returns_json():
    """Test that docx_insert_image returns valid JSON."""
    setup_active_session()
    # Create a temporary test image
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        # Write minimal PNG header
        tmp.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')
        tmp_path = tmp.name

    try:
        result = docx_insert_image(tmp_path, width=2.0, position="end:document_body")

        assert is_success(result)
        assert extract_metadata_field(result, "element_id") is not None
        assert extract_metadata_field(result, "image_path") == tmp_path
    finally:
        os.unlink(tmp_path)
        teardown_active_session()


def test_insert_image_file_not_found():
    """Test that docx_insert_image returns error for missing file."""
    setup_active_session()
    result = docx_insert_image("/nonexistent/image.png", position="end:document_body")

    assert is_error(result)
    assert extract_metadata_field(result, "error_type") == "FileNotFound"

    teardown_active_session()


def test_cursor_move_to_document_body():
    """Test moving cursor to document body."""
    setup_active_session()
    result = docx_cursor_move("document_body", "inside_end")

    assert is_success(result)
    assert extract_metadata_field(result, "element_id") == "document_body"

    teardown_active_session()


def test_cursor_move_invalid_element():
    """Test that docx_cursor_move returns error for invalid element."""
    setup_active_session()
    result = docx_cursor_move("para_nonexistent", "after")

    assert is_error(result)
    assert extract_metadata_field(result, "error_type") == "ElementNotFound"

    teardown_active_session()
