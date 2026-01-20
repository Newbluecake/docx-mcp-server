"""Unit tests for text update functionality."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from docx_mcp_server.server import (
    docx_create,
    docx_add_paragraph,
    docx_add_run,
    docx_set_font,
    docx_update_paragraph_text,
    docx_update_run_text,
    docx_read_content,
    docx_close
)

def test_update_paragraph_text():
    """Test updating paragraph text."""
    session_id = docx_create()

    # Create paragraph
    para_id = docx_add_paragraph(session_id, "Original text")

    # Update it
    result = docx_update_paragraph_text(session_id, para_id, "Updated text")
    assert "updated successfully" in result.lower()

    # Verify content
    content = docx_read_content(session_id)
    assert "Updated text" in content
    assert "Original text" not in content

    docx_close(session_id)

def test_update_run_text():
    """Test updating run text while preserving formatting."""
    session_id = docx_create()

    # Create formatted run
    para_id = docx_add_paragraph(session_id, "")
    run_id = docx_add_run(session_id, para_id, "Original")
    docx_set_font(session_id, run_id, bold=True, size=16)

    # Update run text
    result = docx_update_run_text(session_id, run_id, "Updated")
    assert "updated successfully" in result.lower()

    # Verify content
    content = docx_read_content(session_id)
    assert "Updated" in content
    assert "Original" not in content

    docx_close(session_id)

def test_update_paragraph_with_multiple_runs():
    """Test updating paragraph replaces all runs."""
    session_id = docx_create()

    # Create paragraph with multiple runs
    para_id = docx_add_paragraph(session_id, "")
    docx_add_run(session_id, para_id, "Part 1 ")
    docx_add_run(session_id, para_id, "Part 2")

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
    try:
        docx_update_paragraph_text("invalid_session", "para_123", "text")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "not found" in str(e)

def test_update_paragraph_invalid_id():
    """Test updating with invalid paragraph ID."""
    session_id = docx_create()

    try:
        docx_update_paragraph_text(session_id, "para_invalid", "text")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "not found" in str(e)

    docx_close(session_id)

def test_update_run_invalid_session():
    """Test updating run with invalid session ID."""
    try:
        docx_update_run_text("invalid_session", "run_123", "text")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "not found" in str(e)

def test_update_run_invalid_id():
    """Test updating run with invalid run ID."""
    session_id = docx_create()

    try:
        docx_update_run_text(session_id, "run_invalid", "text")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "not found" in str(e)

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
