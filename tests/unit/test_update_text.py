"""Unit tests for text update functionality."""

import sys
import os
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from docx_mcp_server.server import (
    docx_create,
    docx_insert_paragraph,
    docx_insert_run,
    docx_set_font,
    docx_update_paragraph_text,
    docx_update_run_text,
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

def test_update_paragraph_text():
    """Test updating paragraph text."""
    session_id = docx_create()

    # Create paragraph
    para_response = docx_insert_paragraph(session_id, "Original text", position="end:document_body")
    para_id = _extract_element_id(para_response)

    # Update it
    result = docx_update_paragraph_text(session_id, para_id, "Updated text")
    # Result can be JSON or plain string
    result_str = result if isinstance(result, str) else str(result)
    assert "updated" in result_str.lower() or "success" in result_str.lower()

    # Verify content
    content = docx_read_content(session_id)
    assert "Updated text" in content
    assert "Original text" not in content

    docx_close(session_id)

def test_update_run_text():
    """Test updating run text while preserving formatting."""
    session_id = docx_create()

    # Create formatted run
    para_response = docx_insert_paragraph(session_id, "", position="end:document_body")
    para_id = _extract_element_id(para_response)
    run_response = docx_insert_run(session_id, "Original", position=f"inside:{para_id}")
    run_id = _extract_element_id(run_response)
    docx_set_font(session_id, run_id, bold=True, size=16)

    # Update run text
    result = docx_update_run_text(session_id, run_id, "Updated")
    result_str = result if isinstance(result, str) else str(result)
    assert "updated" in result_str.lower() or "success" in result_str.lower()

    # Verify content
    content = docx_read_content(session_id)
    assert "Updated" in content
    assert "Original" not in content

    docx_close(session_id)

def test_update_paragraph_with_multiple_runs():
    """Test updating paragraph replaces all runs."""
    session_id = docx_create()

    # Create paragraph with multiple runs
    para_response = docx_insert_paragraph(session_id, "", position="end:document_body")
    para_id = _extract_element_id(para_response)
    docx_insert_run(session_id, "Part 1 ", position=f"inside:{para_id}")
    docx_insert_run(session_id, "Part 2", position=f"inside:{para_id}")

    # Update paragraph (should replace all runs)
    docx_update_paragraph_text(session_id, para_id, "New single text")

    # Verify content
    content = docx_read_content(session_id)
    assert "New single text" in content
    assert "Part 1" not in content
    assert "Part 2" not in content

    docx_close(session_id)

def test_update_paragraph_invalid_session():
    """Test updating with invalid session ID."""
    result = docx_update_paragraph_text("invalid_session", "para_123", "text")
    # Should return error JSON response
    try:
        data = json.loads(result)
        assert data["status"] == "error"
        assert "not found" in data["message"].lower()
    except (json.JSONDecodeError, KeyError):
        # Fallback: check if it's an error string
        assert "not found" in result.lower()

def test_update_paragraph_invalid_id():
    """Test updating with invalid paragraph ID."""
    session_id = docx_create()

    result = docx_update_paragraph_text(session_id, "para_invalid", "text")
    # Should return error JSON response
    try:
        data = json.loads(result)
        assert data["status"] == "error"
        assert "not found" in data["message"].lower()
    except (json.JSONDecodeError, KeyError):
        assert "not found" in result.lower()

    docx_close(session_id)

def test_update_run_invalid_session():
    """Test updating run with invalid session ID."""
    result = docx_update_run_text("invalid_session", "run_123", "text")
    # Should return error JSON response
    try:
        data = json.loads(result)
        assert data["status"] == "error"
        assert "not found" in data["message"].lower()
    except (json.JSONDecodeError, KeyError):
        assert "not found" in result.lower()

def test_update_run_invalid_id():
    """Test updating run with invalid run ID."""
    session_id = docx_create()

    result = docx_update_run_text(session_id, "run_invalid", "text")
    # Should return error JSON response
    try:
        data = json.loads(result)
        assert data["status"] == "error"
        assert "not found" in data["message"].lower()
    except (json.JSONDecodeError, KeyError):
        assert "not found" in result.lower()

    docx_close(session_id)

if __name__ == "__main__":
    test_update_paragraph_text()
    test_update_run_text()
    test_update_paragraph_with_multiple_runs()
    test_update_paragraph_invalid_session()
    test_update_paragraph_invalid_id()
    test_update_run_invalid_session()
    test_update_run_invalid_id()
    print("All tests passed!")
