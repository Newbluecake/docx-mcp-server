"""Unit tests for docx_copy_paragraph functionality."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from docx_mcp_server.server import (
    docx_create,
    docx_add_paragraph,
    docx_add_run,
    docx_set_font,
    docx_set_alignment,
    docx_copy_paragraph,
    docx_read_content,
    docx_close
)

def test_copy_simple_paragraph():
    """Test copying a simple paragraph."""
    session_id = docx_create()

    # Create original paragraph
    para_id = docx_add_paragraph(session_id, "Original text")

    # Copy it
    new_para_id = docx_copy_paragraph(session_id, para_id)

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
    para_id = docx_add_paragraph(session_id, "")
    run_id = docx_add_run(session_id, para_id, "Bold text")
    docx_set_font(session_id, run_id, bold=True, size=14, color_hex="FF0000")
    docx_set_alignment(session_id, para_id, "center")

    # Copy it
    new_para_id = docx_copy_paragraph(session_id, para_id)

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
    para_id = docx_add_paragraph(session_id, "")
    run1_id = docx_add_run(session_id, para_id, "Normal ")
    run2_id = docx_add_run(session_id, para_id, "Bold ")
    docx_set_font(session_id, run2_id, bold=True)
    run3_id = docx_add_run(session_id, para_id, "Italic")
    docx_set_font(session_id, run3_id, italic=True)

    # Copy it
    new_para_id = docx_copy_paragraph(session_id, para_id)

    # Verify content
    content = docx_read_content(session_id)
    assert content.count("Normal Bold Italic") == 2

    docx_close(session_id)

def test_copy_paragraph_invalid_session():
    """Test copying with invalid session ID."""
    try:
        docx_copy_paragraph("invalid_session", "para_123")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "not found" in str(e)

def test_copy_paragraph_invalid_id():
    """Test copying with invalid paragraph ID."""
    session_id = docx_create()

    try:
        docx_copy_paragraph(session_id, "para_invalid")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "not found" in str(e)

    docx_close(session_id)

if __name__ == "__main__":
    test_copy_simple_paragraph()
    test_copy_formatted_paragraph()
    test_copy_paragraph_with_multiple_runs()
    test_copy_paragraph_invalid_session()
    test_copy_paragraph_invalid_id()
    print("All tests passed!")
