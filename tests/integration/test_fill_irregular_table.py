"""
Integration tests for enhanced docx_fill_table with irregular table support.
"""

import pytest
import json
from docx_mcp_server.tools.session_tools import docx_create, docx_close
from docx_mcp_server.tools.table_tools import (
    docx_insert_table,
    docx_fill_table
)


def test_fill_regular_table():
    """Test filling regular table."""
    session_id = docx_create()

    try:
        # Create table
        result = docx_insert_table(session_id, rows=3, cols=2, position="end:document_body")
        data = json.loads(result)
        table_id = data["data"]["element_id"]

        # Fill table
        fill_data = json.dumps([
            ["A1", "B1"],
            ["A2", "B2"],
            ["A3", "B3"]
        ])
        result = docx_fill_table(session_id, fill_data, table_id=table_id)
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["data"]["rows_filled"] == 3
        assert "filled_range" in data["data"]
        assert "skipped_regions" in data["data"]
        assert len(data["data"]["skipped_regions"]) == 0

    finally:
        docx_close(session_id)
