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
