"""Test context awareness integration with tools."""

import pytest
import json
import sys
import os

# Add parent directory to path for helpers import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from helpers import (
    extract_session_id,
    extract_element_id,
    extract_metadata_field,
    is_success,
    is_error
)
from docx_mcp_server.tools.paragraph_tools import docx_insert_paragraph, docx_insert_heading
from docx_mcp_server.tools.run_tools import docx_insert_run
from docx_mcp_server.tools.table_tools import docx_insert_table, docx_insert_paragraph_to_cell, docx_get_cell


def test_paragraph_context():
    """Test that add_paragraph returns context."""
    from docx_mcp_server.server import session_manager

    session_id = session_manager.create_session()

    # Add first paragraph
    result1 = docx_insert_paragraph(session_id, "First paragraph", position="end:document_body")
    assert is_success(result1)
    element_id1 = extract_element_id(result1)
    assert "para_" in element_id1
    assert extract_metadata_field(result1, "cursor") is not None

    # Add second paragraph
    result2 = docx_insert_paragraph(session_id, "Second paragraph", position="end:document_body")
    assert is_success(result2)
    assert extract_metadata_field(result2, "cursor") is not None


def test_heading_context():
    """Test that add_heading returns context."""
    from docx_mcp_server.server import session_manager

    session_id = session_manager.create_session()

    result = docx_insert_heading(session_id, "My Heading", position="end:document_body", level=1)
    assert is_success(result)
    element_id = extract_element_id(result)
    assert "para_" in element_id
    assert extract_metadata_field(result, "cursor") is not None


def test_run_context():
    """Test that add_run returns context."""
    from docx_mcp_server.server import session_manager

    session_id = session_manager.create_session()

    para_result = docx_insert_paragraph(session_id, "", position="end:document_body")
    para_id = extract_element_id(para_result)

    result = docx_insert_run(session_id, "Run text", position=f"inside:{para_id}")
    assert is_success(result)
    element_id = extract_element_id(result)
    assert "run_" in element_id
    assert extract_metadata_field(result, "cursor") is not None


def test_table_context():
    """Test that add_table returns context."""
    from docx_mcp_server.server import session_manager

    session_id = session_manager.create_session()

    # Add paragraph first
    docx_insert_paragraph(session_id, "Before table", position="end:document_body")

    # Add table
    result = docx_insert_table(session_id, rows=2, cols=2, position="end:document_body")
    assert is_success(result)
    element_id = extract_element_id(result)
    assert "table_" in element_id
    assert extract_metadata_field(result, "cursor") is not None


def test_table_cell_context():
    """Test context in table cells."""
    from docx_mcp_server.server import session_manager

    session_id = session_manager.create_session()

    table_result = docx_insert_table(session_id, rows=2, cols=2, position="end:document_body")
    table_id = extract_element_id(table_result)

    cell_result = docx_get_cell(session_id, table_id, 0, 0)
    cell_id = extract_element_id(cell_result)

    result = docx_insert_paragraph_to_cell(session_id, "Cell content", position=f"inside:{cell_id}")
    assert is_success(result)
    element_id = extract_element_id(result)
    assert "para_" in element_id


def test_cursor_tools_context():
    """Test context awareness in cursor tools."""
    from docx_mcp_server.server import session_manager
    from docx_mcp_server.tools.cursor_tools import (
        docx_cursor_move,
        docx_cursor_get
    )

    session_id = session_manager.create_session()
    para_result = docx_insert_paragraph(session_id, "Para 1", position="end:document_body")
    para_id = extract_element_id(para_result)

    # Move cursor
    move_result = docx_cursor_move(session_id, para_id, "after")
    assert is_success(move_result)
    assert extract_metadata_field(move_result, "cursor") is not None

    # Get cursor info
    get_result = docx_cursor_get(session_id)
    assert is_success(get_result)


def test_advanced_tools_context():
    """Test context in advanced tools."""
    from docx_mcp_server.server import session_manager
    from docx_mcp_server.tools.advanced_tools import docx_insert_image
    import tempfile
    import os

    session_id = session_manager.create_session()

    # Create a minimal valid PNG file
    minimal_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(minimal_png)
        img_path = f.name

    try:
        result = docx_insert_image(session_id, img_path, position="end:document_body")
        assert is_success(result)
        element_id = extract_element_id(result)
        assert "para_" in element_id or "run_" in element_id
        assert extract_metadata_field(result, "cursor") is not None
    finally:
        if os.path.exists(img_path):
            os.remove(img_path)
