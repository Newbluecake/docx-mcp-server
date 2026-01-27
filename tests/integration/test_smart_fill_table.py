"""
Integration tests for enhanced docx_smart_fill_table.
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
from docx_mcp_server.tools.table_tools import docx_insert_table
from docx_mcp_server.tools.composite_tools import docx_smart_fill_table


def test_smart_fill_with_auto_resize():
    """Test smart fill with auto resize."""
    setup_active_session()
    assert session_id is not None

    try:
        # Create small table
        result = docx_insert_table(rows=2, cols=2, position="end:document_body")
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
        assert is_success(result)
        fill_meta = extract_all_metadata(result)
        assert fill_meta.get("rows_filled") == 4
        assert fill_meta.get("rows_added") == 2  # Added 2 rows
        # skipped_regions may be empty; just ensure key exists when provided
        if "skipped_regions" in fill_meta:
            assert isinstance(fill_meta.get("skipped_regions"), (list, str))

    finally:
        teardown_active_session()
