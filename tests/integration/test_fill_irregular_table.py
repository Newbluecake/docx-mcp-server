"""
Integration tests for enhanced docx_fill_table with irregular table support.
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
from docx_mcp_server.tools.session_tools import docx_close
from tests.helpers.session_helpers import setup_active_session, teardown_active_session
from docx_mcp_server.tools.table_tools import (
    docx_insert_table,
    docx_fill_table
)


def test_fill_regular_table():
    """Test filling regular table."""
    session_id = setup_active_session()
    assert session_id is not None

    try:
        # Create table
        result = docx_insert_table(rows=3, cols=2, position="end:document_body")
        data = json.loads(result)
        table_id = data["data"]["element_id"]

        # Fill table
        fill_data = json.dumps([
            ["A1", "B1"],
            ["A2", "B2"],
            ["A3", "B3"]
        ])
        result = docx_fill_table(fill_data, table_id=table_id)
        assert is_success(result)
        fill_meta = extract_all_metadata(result)
        assert fill_meta.get("rows_filled") == 3
        assert "filled_range" in fill_meta
        assert "skipped_regions" in fill_meta
        assert len(fill_meta.get("skipped_regions", [])) == 0

    finally:
        teardown_active_session()
