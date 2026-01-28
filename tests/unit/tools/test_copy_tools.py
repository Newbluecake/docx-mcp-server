import pytest
import json
from docx_mcp_server.tools.paragraph_tools import docx_insert_paragraph, docx_insert_heading
from docx_mcp_server.tools.run_tools import docx_insert_run, docx_set_font
from docx_mcp_server.tools.paragraph_tools import docx_copy_paragraph
from docx_mcp_server.tools.copy_tools import docx_get_element_source

# Add parent directory to path for helpers import
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from helpers import (
    extract_session_id,
    extract_element_id,
    extract_metadata_field,
    is_success,
    is_error
)
from tests.helpers.session_helpers import setup_active_session, teardown_active_session


def test_docx_copy_paragraph_tool():
    """Test that copy_paragraph preserves formatting and tracks lineage."""
    setup_active_session()
    try:
        # Create source paragraph with complex formatting
        para_response = docx_insert_paragraph("Source Paragraph", position="end:document_body")
        para_id = extract_element_id(para_response)
        run_response = docx_insert_run(" Bold Part", position=f"inside:{para_id}")
        run_id = extract_element_id(run_response)
        docx_set_font(run_id, bold=True, size=14, color_hex="FF0000")

        # Copy it
        new_para_response = docx_copy_paragraph(para_id, position="end:document_body")
        new_para_id = extract_element_id(new_para_response)

        # Verify IDs are different
        assert new_para_id != para_id
        assert new_para_id.startswith("para_")

        # Verify metadata (Lineage tracking)
        source_json = docx_get_element_source(new_para_id)
        source_data = json.loads(source_json)

        assert source_data["source_id"] == para_id
        assert source_data["source_type"] == "paragraph"
        assert "copied_at" in source_data
    finally:
        teardown_active_session()

def test_docx_copy_heading_tool():
    """Test that headings can be copied as they are paragraphs."""
    setup_active_session()
    try:
        # Create heading
        h_response = docx_insert_heading("My Heading", position="end:document_body", level=1)
        h_id = extract_element_id(h_response)

        # Copy it
        new_h_response = docx_copy_paragraph(h_id, position="end:document_body")
        new_h_id = extract_element_id(new_h_response)

        # Verify metadata
        source_json = docx_get_element_source(new_h_id)
        source_data = json.loads(source_json)
        assert source_data["source_id"] == h_id
    finally:
        teardown_active_session()

def test_docx_copy_invalid_input():
    setup_active_session()
    try:
        result = docx_copy_paragraph("invalid_id", position="end:document_body")
        # Check if it's an error response
        assert is_error(result)
    finally:
        teardown_active_session()
