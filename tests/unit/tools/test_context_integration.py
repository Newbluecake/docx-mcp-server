"""Test context awareness integration with tools."""

import pytest
from docx_mcp_server.tools.paragraph_tools import docx_add_paragraph, docx_add_heading
from docx_mcp_server.tools.run_tools import docx_add_run
from docx_mcp_server.tools.table_tools import docx_add_table, docx_add_paragraph_to_cell, docx_get_cell


def test_paragraph_context():
    """Test that add_paragraph returns context."""
    from docx_mcp_server.server import session_manager

    session_id = session_manager.create_session()

    # Add first paragraph
    result1 = docx_add_paragraph(session_id, "First paragraph")
    assert "para_" in result1
    assert "Context:" in result1  # Should include context

    # Add second paragraph
    result2 = docx_add_paragraph(session_id, "Second paragraph")
    assert "Context:" in result2
    assert "First paragraph" in result2  # Should show previous element


def test_heading_context():
    """Test that add_heading returns context."""
    from docx_mcp_server.server import session_manager

    session_id = session_manager.create_session()

    result = docx_add_heading(session_id, "My Heading", level=1)
    assert "para_" in result
    assert "Context:" in result


def test_run_context():
    """Test that add_run returns context."""
    from docx_mcp_server.server import session_manager

    session_id = session_manager.create_session()

    para_result = docx_add_paragraph(session_id, "")
    para_id = para_result.split('\n')[0]

    result = docx_add_run(session_id, "Run text", paragraph_id=para_id)
    assert "run_" in result
    assert "Context:" in result


def test_table_context():
    """Test that add_table returns context."""
    from docx_mcp_server.server import session_manager

    session_id = session_manager.create_session()

    # Add paragraph first
    docx_add_paragraph(session_id, "Before table")

    # Add table
    result = docx_add_table(session_id, rows=2, cols=2)
    assert "table_" in result
    assert "Context:" in result
    assert "Before table" in result


def test_table_cell_context():
    """Test context in table cells."""
    from docx_mcp_server.server import session_manager

    session_id = session_manager.create_session()

    table_result = docx_add_table(session_id, rows=2, cols=2)
    table_id = table_result.split('\n')[0]

    cell_id = docx_get_cell(session_id, table_id, 0, 0)

    result = docx_add_paragraph_to_cell(session_id, cell_id, "Cell content")
    assert "para_" in result
    assert "Context:" in result
    assert "Parent:" in result  # Should show parent cell


def test_cursor_tools_context():
    """Test context awareness in cursor tools."""
    from docx_mcp_server.server import session_manager
    from docx_mcp_server.tools.cursor_tools import (
        docx_cursor_move,
        docx_insert_paragraph_at_cursor,
        docx_cursor_get
    )

    session_id = session_manager.create_session()
    para_result = docx_add_paragraph(session_id, "Para 1")
    para_id = para_result.split('\n')[0]

    # Move cursor
    move_result = docx_cursor_move(session_id, para_id, "after")
    assert "Cursor moved" in move_result
    assert "Context:" in move_result

    # Insert at cursor
    insert_result = docx_insert_paragraph_at_cursor(session_id, "Inserted Para")
    assert "para_" in insert_result
    assert "Context:" in insert_result

    # Get cursor info
    get_result = docx_cursor_get(session_id)
    assert isinstance(get_result, dict)
    assert "context" in get_result
    assert "Context:" in get_result["context"]


def test_advanced_tools_context():
    """Test context in advanced tools."""
    from docx_mcp_server.server import session_manager
    from docx_mcp_server.tools.advanced_tools import docx_insert_image

    session_id = session_manager.create_session()

    # Create a dummy image file for testing
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(b"fake image data")
        img_path = f.name

    try:
        # Insert image
        # Note: We expect this to fail actual image insertion because content is fake,
        # but python-docx might check header.
        # If python-docx validates image, we might need a real minimal png.
        # Let's try mocking or just checking if we can catch the error if it fails validation,
        # but the tool usually validates file existence first.
        # For simplicity, let's skip actual image insertion logic validation and just check if we can reach the context part
        # if we had a valid image.
        # Actually, let's use a real minimal PNG signature.
        minimal_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        with open(img_path, 'wb') as f:
            f.write(minimal_png)

        result = docx_insert_image(session_id, img_path)
        assert "para_" in result or "run_" in result
        assert "Context:" in result

    finally:
        if os.path.exists(img_path):
            os.remove(img_path)
