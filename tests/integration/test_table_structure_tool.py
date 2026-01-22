"""
Integration tests for docx_get_table_structure tool.
"""

import pytest
import json
from docx_mcp_server.tools.session_tools import docx_create, docx_close
from docx_mcp_server.tools.table_tools import (
    docx_insert_table,
    docx_get_table_structure
)


def test_get_table_structure():
    """Test getting table structure."""
    session_id = docx_create()

    try:
        # Create a table
        result = docx_insert_table(session_id, rows=3, cols=3, position="end:document_body")
        data = json.loads(result)
        table_id = data["data"]["element_id"]

        # Get structure
        result = docx_get_table_structure(session_id, table_id)
        data = json.loads(result)

        assert data["status"] == "success"
        assert "ascii_visualization" in data["data"]
        assert "structure_info" in data["data"]
        assert data["data"]["rows"] == 3
        assert data["data"]["cols"] == 3
        assert "Table: 3 rows x 3 cols" in data["data"]["ascii_visualization"]

    finally:
        docx_close(session_id)
