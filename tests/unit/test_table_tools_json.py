"""Unit tests for refactored table tools with JSON responses."""

import json
import pytest
from docx_mcp_server.tools.table_tools import (
    docx_add_table,
    docx_get_table,
    docx_find_table,
    docx_get_cell,
    docx_add_paragraph_to_cell,
    docx_add_table_row,
    docx_add_table_col,
    docx_fill_table,
    docx_copy_table
)
from docx_mcp_server.tools.session_tools import docx_create, docx_close


def test_add_table_returns_json():
    """Test that docx_add_table returns valid JSON."""
    session_id = docx_create()
    result = docx_add_table(session_id, rows=2, cols=3)

    data = json.loads(result)
    assert data["status"] == "success"
    assert "element_id" in data["data"]
    assert data["data"]["element_id"].startswith("table_")
    assert data["data"]["rows"] == 2
    assert data["data"]["cols"] == 3
    assert "cursor" in data["data"]

    docx_close(session_id)


def test_get_table_returns_json():
    """Test that docx_get_table returns valid JSON."""
    session_id = docx_create()
    docx_add_table(session_id, 2, 2)

    result = docx_get_table(session_id, 0)
    data = json.loads(result)

    assert data["status"] == "success"
    assert "element_id" in data["data"]
    assert data["data"]["index"] == 0

    docx_close(session_id)


def test_find_table_returns_json():
    """Test that docx_find_table returns valid JSON."""
    session_id = docx_create()

    # Create table with specific text
    table_id = json.loads(docx_add_table(session_id, 2, 2))["data"]["element_id"]
    cell_id = json.loads(docx_get_cell(session_id, table_id, 0, 0))["data"]["element_id"]
    docx_add_paragraph_to_cell(session_id, cell_id, "UniqueHeader")

    # Find it
    result = docx_find_table(session_id, "UniqueHeader")
    data = json.loads(result)

    assert data["status"] == "success"
    assert data["data"]["element_id"] == table_id
    assert data["data"]["search_text"] == "UniqueHeader"

    docx_close(session_id)


def test_get_cell_returns_json():
    """Test that docx_get_cell returns valid JSON."""
    session_id = docx_create()
    table_id = json.loads(docx_add_table(session_id, 2, 2))["data"]["element_id"]

    result = docx_get_cell(session_id, table_id, 0, 1)
    data = json.loads(result)

    assert data["status"] == "success"
    assert "element_id" in data["data"]
    assert data["data"]["element_id"].startswith("cell_")
    assert data["data"]["row"] == 0
    assert data["data"]["col"] == 1

    docx_close(session_id)


def test_add_paragraph_to_cell_returns_json():
    """Test that docx_add_paragraph_to_cell returns valid JSON."""
    session_id = docx_create()
    table_id = json.loads(docx_add_table(session_id, 2, 2))["data"]["element_id"]
    cell_id = json.loads(docx_get_cell(session_id, table_id, 0, 0))["data"]["element_id"]

    result = docx_add_paragraph_to_cell(session_id, cell_id, "Cell Text")
    data = json.loads(result)

    assert data["status"] == "success"
    assert "element_id" in data["data"]
    assert "cursor" in data["data"]

    docx_close(session_id)


def test_add_table_row_returns_json():
    """Test that docx_add_table_row returns valid JSON."""
    session_id = docx_create()
    table_id = json.loads(docx_add_table(session_id, 2, 2))["data"]["element_id"]

    result = docx_add_table_row(session_id, table_id)
    data = json.loads(result)

    assert data["status"] == "success"
    assert "Row added" in data["message"]
    assert data["data"]["new_row_count"] == 3

    docx_close(session_id)


def test_add_table_col_returns_json():
    """Test that docx_add_table_col returns valid JSON."""
    session_id = docx_create()
    table_id = json.loads(docx_add_table(session_id, 2, 2))["data"]["element_id"]

    result = docx_add_table_col(session_id, table_id)
    data = json.loads(result)

    assert data["status"] == "success"
    assert "Column added" in data["message"]
    assert data["data"]["new_col_count"] == 3

    docx_close(session_id)


def test_fill_table_returns_json():
    """Test that docx_fill_table returns valid JSON."""
    session_id = docx_create()
    table_id = json.loads(docx_add_table(session_id, 2, 2))["data"]["element_id"]

    data_json = json.dumps([["A1", "B1"], ["A2", "B2"]])
    result = docx_fill_table(session_id, data_json, table_id)
    data = json.loads(result)

    assert data["status"] == "success"
    assert data["data"]["rows_filled"] == 2
    assert "cursor" in data["data"]

    docx_close(session_id)


def test_copy_table_returns_json():
    """Test that docx_copy_table returns valid JSON."""
    session_id = docx_create()
    table_id = json.loads(docx_add_table(session_id, 2, 2))["data"]["element_id"]

    result = docx_copy_table(session_id, table_id)
    data = json.loads(result)

    assert data["status"] == "success"
    assert "element_id" in data["data"]
    assert data["data"]["element_id"] != table_id
    assert data["data"]["source_id"] == table_id

    docx_close(session_id)


def test_table_error_handling():
    """Test error handling in table tools."""
    session_id = docx_create()

    # Invalid table ID
    result = docx_get_table("invalid_id", 0)
    data = json.loads(result)
    assert data["status"] == "error"
    assert data["data"]["error_type"] == "SessionNotFound"

    # Index out of bounds
    result = docx_get_table(session_id, 99)
    data = json.loads(result)
    assert data["status"] == "error"

    # Invalid JSON for fill_table
    table_id = json.loads(docx_add_table(session_id, 2, 2))["data"]["element_id"]
    result = docx_fill_table(session_id, "invalid_json", table_id)
    data = json.loads(result)
    assert data["status"] == "error"
    assert data["data"]["error_type"] == "JSONDecodeError"

    docx_close(session_id)
