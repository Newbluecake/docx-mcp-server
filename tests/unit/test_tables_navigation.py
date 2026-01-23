import pytest
import json
import sys
import os
from unittest.mock import MagicMock, patch, mock_open

# Add parent directory to path for helpers import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from docx_mcp_server.server import (
    docx_get_table,
    docx_find_table,
    docx_list_files,
    docx_copy_table,
    docx_insert_table_row,
    docx_insert_table_col,
    docx_fill_table,
    session_manager,
    docx_create,
    docx_insert_table
)
from helpers import extract_session_id, extract_element_id

def test_list_files():
    with patch("os.listdir", return_value=["template.docx", "ignore.txt", "~$temp.docx"]):
        with patch("os.path.exists", return_value=True):
            result = docx_list_files(".")
            files = json.loads(result)
            # Expect relative paths now
            assert "./template.docx" in files
            assert "./ignore.txt" not in files
            assert "./~$temp.docx" not in files

def test_table_operations_flow():
    # 1. Create session
    session_response = docx_create()
    sid = extract_session_id(session_response)

    # 2. Add table
    t_response = docx_insert_table(sid, rows=2, cols=2, position="end:document_body")
    t_id = extract_element_id(t_response)
    session = session_manager.get_session(sid)
    table = session.get_object(t_id)
    assert len(table.rows) == 2
    assert len(table.columns) == 2

    # 3. Add row
    docx_insert_table_row(sid, position=f"inside:{t_id}")
    assert len(table.rows) == 3

    # 4. Add column
    docx_insert_table_col(sid, position=f"inside:{t_id}")
    assert len(table.columns) == 3

def test_fill_table():
    session_response = docx_create()
    sid = extract_session_id(session_response)
    t_response = docx_insert_table(sid, rows=1, cols=2, position="end:document_body")
    t_id = extract_element_id(t_response)

    # Data for 2 rows (will need to add 1 row)
    data = [
        ["Header 1", "Header 2"],
        ["Value 1", "Value 2"]
    ]
    json_data = json.dumps(data)

    docx_fill_table(sid, json_data, t_id)

    session = session_manager.get_session(sid)
    table = session.get_object(t_id)

    assert len(table.rows) == 2
    assert table.rows[0].cells[0].text == "Header 1"
    assert table.rows[1].cells[1].text == "Value 2"

def test_copy_table():
    session_response = docx_create()
    sid = extract_session_id(session_response)
    t_response = docx_insert_table(sid, rows=2, cols=2, position="end:document_body")
    t_id = extract_element_id(t_response)

    # Copy it
    t_copy_response = docx_copy_table(sid, t_id, position="end:document_body")
    t_copy_id = extract_element_id(t_copy_response)

    assert t_copy_id != t_id
    assert t_copy_id.startswith("table_")

    session = session_manager.get_session(sid)
    assert len(session.document.tables) == 2 # Original + Copy

    # Verify copy has same dimensions
    t_copy = session.get_object(t_copy_id)
    assert len(t_copy.rows) == 2
    assert len(t_copy.columns) == 2

def test_find_table():
    session_response = docx_create()
    sid = extract_session_id(session_response)
    t_response = docx_insert_table(sid, rows=1, cols=1, position="end:document_body")
    t_id = extract_element_id(t_response)

    # Set text
    session = session_manager.get_session(sid)
    table = session.get_object(t_id)
    table.cell(0, 0).text = "UniqueRevenueData"

    # Find it
    found_response = docx_find_table(sid, "Revenue")
    found_id = extract_element_id(found_response)
    # Note: found_id might be different string if registered again, or same?
    # The register_object generates new ID every time unless we cache.
    # The current implementation generates new ID.

    found_table = session.get_object(found_id)
    assert "UniqueRevenueData" in found_table.cell(0, 0).text
