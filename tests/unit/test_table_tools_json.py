import json
import pytest
import sys
import os

# Add parent directory to path for helpers import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from docx_mcp_server.tools.table_tools import (
    docx_insert_table,
    docx_get_table,
    docx_find_table,
    docx_get_cell,
    docx_insert_paragraph_to_cell,
    docx_insert_table_row,
    docx_insert_table_col,
    docx_fill_table,
    docx_copy_table
)
from docx_mcp_server.tools.session_tools import docx_create, docx_close
from helpers import (
    extract_session_id,
    extract_element_id,
    extract_metadata_field,
    is_success,
    is_error,
    extract_error_message
)


def test_add_table_returns_json():
    """Test that docx_insert_table returns valid JSON."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)
    result = docx_insert_table(session_id, rows=2, cols=3, position="end:document_body")
    assert is_success(result)
    element_id = extract_element_id(result)
    assert element_id is not None
    assert element_id.startswith("table_")
    assert extract_metadata_field(result, "rows") == 2
    assert extract_metadata_field(result, "cols") == 3
    assert extract_metadata_field(result, "cursor") is not None

    docx_close(session_id)


def test_get_table_returns_json():
    """Test that docx_get_table returns valid JSON."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)
    docx_insert_table(session_id, 2, 2, position="end:document_body")

    result = docx_get_table(session_id, 0)

    assert is_success(result)
    element_id = extract_element_id(result)
    assert element_id is not None
    assert extract_metadata_field(result, "index") == 0

    docx_close(session_id)


def test_find_table_returns_json():
    """Test that docx_find_table returns valid JSON."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)

    # Create table with specific text
    table_id = extract_element_id(docx_insert_table(session_id, 2, 2, position="end:document_body"))
    cell_id = extract_element_id(docx_get_cell(session_id, table_id, 0, 0))
    docx_insert_paragraph_to_cell(session_id, "UniqueHeader", position=f"inside:{cell_id}")

    # Find it
    result = docx_find_table(session_id, "UniqueHeader")

    assert is_success(result)
    assert extract_element_id(result) == table_id
    assert extract_metadata_field(result, "search_text") == "UniqueHeader"

    docx_close(session_id)


def test_get_cell_returns_json():
    """Test that docx_get_cell returns valid JSON."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)
    table_id = extract_element_id(docx_insert_table(session_id, 2, 2, position="end:document_body"))

    result = docx_get_cell(session_id, table_id, 0, 1)

    assert is_success(result)
    element_id = extract_element_id(result)
    assert element_id is not None
    assert element_id.startswith("cell_")
    assert extract_metadata_field(result, "row") == 0
    assert extract_metadata_field(result, "col") == 1

    docx_close(session_id)


def test_add_paragraph_to_cell_returns_json():
    """Test that docx_insert_paragraph_to_cell returns valid JSON."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)
    table_id = extract_element_id(docx_insert_table(session_id, 2, 2, position="end:document_body"))
    cell_id = extract_element_id(docx_get_cell(session_id, table_id, 0, 0))

    result = docx_insert_paragraph_to_cell(session_id, "Cell Text", position=f"inside:{cell_id}")

    assert is_success(result)
    element_id = extract_element_id(result)
    assert element_id is not None
    assert extract_metadata_field(result, "cursor") is not None

    docx_close(session_id)


def test_add_table_row_returns_json():
    """Test that docx_insert_table_row returns valid JSON."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)
    table_id = extract_element_id(docx_insert_table(session_id, 2, 2, position="end:document_body"))

    result = docx_insert_table_row(session_id, position=f"inside:{table_id}")

    assert is_success(result)
    assert extract_metadata_field(result, "new_row_count") == 3

    docx_close(session_id)


def test_add_table_col_returns_json():
    """Test that docx_insert_table_col returns valid JSON."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)
    table_id = extract_element_id(docx_insert_table(session_id, 2, 2, position="end:document_body"))

    result = docx_insert_table_col(session_id, position=f"inside:{table_id}")

    assert is_success(result)
    assert extract_metadata_field(result, "new_col_count") == 3

    docx_close(session_id)


def test_fill_table_returns_json():
    """Test that docx_fill_table returns valid JSON."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)
    table_id = extract_element_id(docx_insert_table(session_id, 2, 2, position="end:document_body"))

    data_json = json.dumps([["A1", "B1"], ["A2", "B2"]])
    result = docx_fill_table(session_id, data_json, table_id)

    assert is_success(result)
    assert extract_metadata_field(result, "rows_filled") == 2
    assert extract_metadata_field(result, "cursor") is not None

    docx_close(session_id)


def test_fill_table_preserves_run_formatting_when_enabled():
    """docx_fill_table preserves existing run formatting when preserve_formatting=True."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)
    table_id = extract_element_id(docx_insert_table(session_id, 1, 1, position="end:document_body"))

    # Seed formatting in the first cell (bold run)
    cell_id = extract_element_id(docx_get_cell(session_id, table_id, 0, 0))
    from docx_mcp_server.server import session_manager
    session = session_manager.get_session(session_id)
    cell = session.get_object(cell_id)
    para = cell.paragraphs[0]
    run = para.add_run("Seed")
    run.font.bold = True

    # Fill table with preserve_formatting=True
    data_json = json.dumps([["New Value"]])
    result = docx_fill_table(session_id, data_json, table_id, preserve_formatting=True)

    assert is_success(result)
    assert extract_metadata_field(result, "preserve_formatting") is True

    # Verify formatting is retained on the new run
    updated_cell = session.get_object(table_id).rows[0].cells[0]
    updated_run = updated_cell.paragraphs[0].runs[0]
    assert updated_run.text == "New Value"
    assert updated_run.font.bold is True

    docx_close(session_id)


def test_copy_table_returns_json():
    """Test that docx_copy_table returns valid JSON."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)
    table_id = extract_element_id(docx_insert_table(session_id, 2, 2, position="end:document_body"))

    result = docx_copy_table(session_id, table_id, position="end:document_body")

    assert is_success(result)
    element_id = extract_element_id(result)
    assert element_id is not None
    assert element_id != table_id
    assert extract_metadata_field(result, "source_id") == table_id

    docx_close(session_id)


def test_table_error_handling():
    """Test error handling in table tools."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)

    # Invalid table ID
    result = docx_get_table("invalid_id", 0)
    assert is_error(result)
    assert extract_metadata_field(result, "error_type") == "SessionNotFound"

    # Index out of bounds
    result = docx_get_table(session_id, 99)
    assert is_error(result)

    # Invalid JSON for fill_table
    table_id = extract_element_id(docx_insert_table(session_id, 2, 2, position="end:document_body"))
    result = docx_fill_table(session_id, "invalid_json", table_id)
    assert is_error(result)
    assert extract_metadata_field(result, "error_type") == "JSONDecodeError"

    docx_close(session_id)
