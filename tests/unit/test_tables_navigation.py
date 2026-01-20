import pytest
import json
from unittest.mock import MagicMock, patch, mock_open
from docx_mcp_server.server import (
    docx_get_table,
    docx_find_table,
    docx_list_files,
    docx_copy_table,
    docx_add_table_row,
    docx_add_table_col,
    docx_fill_table,
    session_manager,
    docx_create,
    docx_add_table
)

def test_list_files():
    with patch("os.listdir", return_value=["template.docx", "ignore.txt", "~$temp.docx"]):
        with patch("os.path.exists", return_value=True):
            result = docx_list_files(".")
            files = json.loads(result)
            assert "template.docx" in files
            assert "ignore.txt" not in files
            assert "~$temp.docx" not in files

def test_table_operations_flow():
    # 1. Create session
    sid = docx_create()

    # 2. Add table
    t_id = docx_add_table(sid, rows=2, cols=2)
    session = session_manager.get_session(sid)
    table = session.get_object(t_id)
    assert len(table.rows) == 2
    assert len(table.columns) == 2

    # 3. Add row
    docx_add_table_row(sid, t_id)
    assert len(table.rows) == 3

    # 4. Add column
    docx_add_table_col(sid, t_id)
    assert len(table.columns) == 3

def test_fill_table():
    sid = docx_create()
    t_id = docx_add_table(sid, rows=1, cols=2)

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
    sid = docx_create()
    t_id = docx_add_table(sid, rows=2, cols=2)

    # Copy it
    t_copy_id = docx_copy_table(sid, t_id)

    assert t_copy_id != t_id
    assert t_copy_id.startswith("table_")

    session = session_manager.get_session(sid)
    assert len(session.document.tables) == 2 # Original + Copy

    # Verify copy has same dimensions
    t_copy = session.get_object(t_copy_id)
    assert len(t_copy.rows) == 2
    assert len(t_copy.columns) == 2

def test_find_table():
    sid = docx_create()
    t_id = docx_add_table(sid, rows=1, cols=1)

    # Set text
    session = session_manager.get_session(sid)
    table = session.get_object(t_id)
    table.cell(0, 0).text = "UniqueRevenueData"

    # Find it
    found_id = docx_find_table(sid, "Revenue")
    # Note: found_id might be different string if registered again, or same?
    # The register_object generates new ID every time unless we cache.
    # The current implementation generates new ID.

    found_table = session.get_object(found_id)
    assert "UniqueRevenueData" in found_table.cell(0, 0).text
