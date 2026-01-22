"""Test context awareness integration with tools."""

import pytest
import json
from docx_mcp_server.tools.paragraph_tools import docx_add_paragraph, docx_add_heading
from docx_mcp_server.tools.run_tools import docx_add_run
from docx_mcp_server.tools.table_tools import docx_add_table, docx_add_paragraph_to_cell, docx_get_cell


def _extract_element_id(response):
    """Extract element_id from JSON response or return as-is if plain string."""
    try:
        data = json.loads(response)
        if isinstance(data, dict) and "data" in data and "element_id" in data["data"]:
            return data["data"]["element_id"]
        return response
    except (json.JSONDecodeError, KeyError):
        return response


def test_paragraph_context():
    """Test that add_paragraph returns context."""
    from docx_mcp_server.server import session_manager

    session_id = session_manager.create_session()

    # Add first paragraph
    result1 = docx_add_paragraph(session_id, "First paragraph")
    data1 = json.loads(result1)
    assert "para_" in data1["data"]["element_id"]
    assert "cursor" in data1["data"]  # Should include cursor with context
    assert "context" in data1["data"]["cursor"]

    # Add second paragraph
    result2 = docx_add_paragraph(session_id, "Second paragraph")
    data2 = json.loads(result2)
    assert "cursor" in data2["data"]
    assert "First paragraph" in data2["data"]["cursor"]["context"]  # Should show previous element


def test_heading_context():
    """Test that add_heading returns context."""
    from docx_mcp_server.server import session_manager

    session_id = session_manager.create_session()

    result = docx_add_heading(session_id, "My Heading", level=1)
    data = json.loads(result)
    assert "para_" in data["data"]["element_id"]
    assert "cursor" in data["data"]
    assert "context" in data["data"]["cursor"]


def test_run_context():
    """Test that add_run returns context."""
    from docx_mcp_server.server import session_manager

    session_id = session_manager.create_session()

    para_result = docx_add_paragraph(session_id, "")
    para_id = _extract_element_id(para_result)

    result = docx_add_run(session_id, "Run text", paragraph_id=para_id)
    data = json.loads(result)
    assert "run_" in data["data"]["element_id"]
    assert "cursor" in data["data"]
    assert "context" in data["data"]["cursor"]


def test_table_context():
    """Test that add_table returns context."""
    from docx_mcp_server.server import session_manager

    session_id = session_manager.create_session()

    # Add paragraph first
    docx_add_paragraph(session_id, "Before table")

    # Add table
    result = docx_add_table(session_id, rows=2, cols=2)
    data = json.loads(result)
    assert "table_" in data["data"]["element_id"]
    assert "cursor" in data["data"]
    assert "Before table" in data["data"]["cursor"]["context"]


def test_table_cell_context():
    """Test context in table cells."""
    from docx_mcp_server.server import session_manager

    session_id = session_manager.create_session()

    table_result = docx_add_table(session_id, rows=2, cols=2)
    table_id = _extract_element_id(table_result)

    cell_result = docx_get_cell(session_id, table_id, 0, 0)
    cell_id = _extract_element_id(cell_result)

    result = docx_add_paragraph_to_cell(session_id, cell_id, "Cell content")
    # docx_add_paragraph_to_cell might return plain string ID, not JSON
    # Let's check if it's JSON or plain string
    try:
        data = json.loads(result)
        if "data" in data and "element_id" in data["data"]:
            element_id = data["data"]["element_id"]
            assert "cursor" in data["data"]
            assert "context" in data["data"]["cursor"]
        else:
            # Old format or different structure
            element_id = _extract_element_id(result)
            assert "para_" in element_id
    except (json.JSONDecodeError, KeyError):
        # Plain string ID
        element_id = result
        assert "para_" in element_id


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
    para_id = _extract_element_id(para_result)

    # Move cursor
    move_result = docx_cursor_move(session_id, para_id, "after")
    move_data = json.loads(move_result)
    assert "Cursor moved" in move_data["message"]
    assert "cursor" in move_data["data"]
    assert "context" in move_data["data"]["cursor"]

    # Insert at cursor
    insert_result = docx_insert_paragraph_at_cursor(session_id, "Inserted Para")
    insert_data = json.loads(insert_result)
    assert "para_" in insert_data["data"]["element_id"]
    assert "cursor" in insert_data["data"]
    assert "context" in insert_data["data"]["cursor"]

    # Get cursor info
    get_result = docx_cursor_get(session_id)
    get_data = json.loads(get_result) if isinstance(get_result, str) else get_result
    # docx_cursor_get returns context directly in data, not in data["cursor"]
    assert "context" in get_data["data"]


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
        data = json.loads(result)
        element_id = data["data"]["element_id"]
        assert "para_" in element_id or "run_" in element_id
        assert "cursor" in data["data"]
        assert "context" in data["data"]["cursor"]

    finally:
        if os.path.exists(img_path):
            os.remove(img_path)
