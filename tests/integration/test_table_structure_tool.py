"""
Integration tests for docx_get_table_structure tool.
"""

import pytest
from tests.helpers import (
    extract_session_id,
    extract_element_id,
    extract_metadata_field,
    extract_all_metadata,
    is_success,
    is_error
)
import json
from docx_mcp_server.tools.session_tools import docx_create, docx_close
from docx_mcp_server.tools.table_tools import (
    docx_insert_table,
    docx_get_table_structure
)


def test_get_table_structure():
    """Test getting table structure."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)
    assert session_id is not None

    try:
        # Create a table
        result = docx_insert_table(session_id, rows=3, cols=3, position="end:document_body")
        data = json.loads(result)
        table_id = data["data"]["element_id"]

        # Get structure
        result = docx_get_table_structure(session_id, table_id)
        assert is_success(result)
        struct_meta = extract_all_metadata(result)
        assert "ascii_visualization" in struct_meta
        assert "structure_info" in struct_meta
        assert struct_meta.get("rows") == 3
        assert struct_meta.get("cols") == 3
        ascii_vis = struct_meta.get("ascii_visualization", "")
        assert "Table: 3 rows x 3 cols" in ascii_vis

    finally:
        docx_close(session_id)
