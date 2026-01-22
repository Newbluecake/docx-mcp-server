"""Unit tests for docx_copy_paragraph functionality."""

import sys
import os
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from docx_mcp_server.server import (
    docx_create,
    docx_insert_paragraph,
    docx_insert_run,
    docx_set_font,
    docx_set_alignment,
    docx_copy_paragraph,
    docx_read_content,
    docx_close
)


def _extract_element_id(response):
    """Extract element_id from JSON response or return as-is if plain string."""
    try:
        data = json.loads(response)
        if isinstance(data, dict) and "data" in data and "element_id" in data["data"]:
            return data["data"]["element_id"]
        return response
    except (json.JSONDecodeError, KeyError):
        return response

def test_copy_simple_paragraph():
    """Test copying a simple paragraph."""
    session_id = docx_create()

    # Create original paragraph
    para_response = docx_insert_paragraph(session_id, "Original text", position="end:document_body")
    para_id = _extract_element_id(para_response)

    # Copy it
    new_para_response = docx_copy_paragraph(session_id, para_id, position="end:document_body")
    new_para_id = _extract_element_id(new_para_response)

    # Verify it's a different ID
    assert new_para_id != para_id
    assert new_para_id.startswith("para_")

    # Verify content
    content = docx_read_content(session_id)
    assert content.count("Original text") == 2

    docx_close(session_id)

def test_copy_formatted_paragraph():
    """Test copying a paragraph with formatting."""
    session_id = docx_create()

    # Create formatted paragraph
    para_response = docx_insert_paragraph(session_id, "", position="end:document_body")
    para_id = _extract_element_id(para_response)
    run_response = docx_insert_run(session_id, "Bold text", position=f"inside:{para_id}")
    run_id = _extract_element_id(run_response)
    docx_set_font(session_id, run_id, bold=True, size=14, color_hex="FF0000")
    docx_set_alignment(session_id, para_id, "center")

    # Copy it
    new_para_response = docx_copy_paragraph(session_id, para_id, position="end:document_body")
    new_para_id = _extract_element_id(new_para_response)

    # Verify different IDs
    assert new_para_id != para_id

    # Verify content duplicated
    content = docx_read_content(session_id)
    assert content.count("Bold text") == 2

    docx_close(session_id)

def test_copy_paragraph_with_multiple_runs():
    """Test copying a paragraph with multiple runs."""
    session_id = docx_create()

    # Create paragraph with multiple runs
    para_response = docx_insert_paragraph(session_id, "", position="end:document_body")
    para_id = _extract_element_id(para_response)
    run1_response = docx_insert_run(session_id, "Normal ", position=f"inside:{para_id}")
    run1_id = _extract_element_id(run1_response)
    run2_response = docx_insert_run(session_id, "Bold ", position=f"inside:{para_id}")
    run2_id = _extract_element_id(run2_response)
    docx_set_font(session_id, run2_id, bold=True)
    run3_response = docx_insert_run(session_id, "Italic", position=f"inside:{para_id}")
    run3_id = _extract_element_id(run3_response)
    docx_set_font(session_id, run3_id, italic=True)

    # Copy it
    new_para_response = docx_copy_paragraph(session_id, para_id, position="end:document_body")
    new_para_id = _extract_element_id(new_para_response)

    # Verify content
    content = docx_read_content(session_id)
    assert content.count("Normal Bold Italic") == 2

    docx_close(session_id)

def test_copy_paragraph_invalid_session():
    """Test copying with invalid session ID."""
    result = docx_copy_paragraph("invalid_session", "para_123", position="end:document_body")
    try:
        data = json.loads(result)
        assert data["status"] == "error"
        assert "not found" in data["message"].lower()
    except (json.JSONDecodeError, KeyError):
        assert "not found" in result.lower()

def test_copy_paragraph_invalid_id():
    """Test copying with invalid paragraph ID."""
    session_id = docx_create()

    result = docx_copy_paragraph(session_id, "para_invalid", position="end:document_body")
    try:
        data = json.loads(result)
        assert data["status"] == "error"
        assert "not found" in data["message"].lower()
    except (json.JSONDecodeError, KeyError):
        assert "not found" in result.lower()

    docx_close(session_id)

if __name__ == "__main__":
    test_copy_simple_paragraph()
    test_copy_formatted_paragraph()
    test_copy_paragraph_with_multiple_runs()
    test_copy_paragraph_invalid_session()
    test_copy_paragraph_invalid_id()
    print("All tests passed!")
