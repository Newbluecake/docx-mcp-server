"""
Integration tests for enhanced docx_smart_fill_table.
"""

import pytest
import json
from docx_mcp_server.tools.session_tools import docx_create, docx_close
from docx_mcp_server.tools.table_tools import docx_insert_table
from docx_mcp_server.tools.composite_tools import docx_smart_fill_table


def test_smart_fill_with_auto_resize():
    """Test smart fill with auto resize."""
    session_id = docx_create()

    try:
        # Create small table
        result = docx_insert_table(session_id, rows=2, cols=2, position="end:document_body")
        data = json.loads(result)
        table_id = data["data"]["element_id"]

        # Fill with more data
        fill_data = json.dumps([
            ["Header1", "Header2"],
            ["Data1", "Data2"],
            ["Data3", "Data4"],
            ["Data5", "Data6"]
        ])

        result = docx_smart_fill_table(
            session_id,
            table_id,
            fill_data,
            has_header=True,
            auto_resize=True
        )
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["rows_filled"] == 4
        assert data["rows_added"] == 2  # Added 2 rows
        assert "filled_range" in data
        assert "skipped_regions" in data

    finally:
        docx_close(session_id)
