import pytest
import json
from docx_mcp_server.server import docx_create, docx_add_paragraph, docx_add_run, docx_set_font, docx_copy_paragraph, docx_get_element_source, docx_add_heading

def test_docx_copy_paragraph_tool():
    """Test the atomic paragraph copy tool via server API."""
    session_id = docx_create()

    # Create source paragraph with complex formatting
    para_id = docx_add_paragraph(session_id, "Source Paragraph")
    run_id = docx_add_run(session_id, " Bold Part", paragraph_id=para_id)
    docx_set_font(session_id, run_id, bold=True, size=14, color_hex="FF0000")

    # Copy it
    new_para_id = docx_copy_paragraph(session_id, para_id)

    # Verify IDs are different
    assert new_para_id != para_id
    assert new_para_id.startswith("para_")

    # Verify metadata (Lineage tracking)
    source_json = docx_get_element_source(session_id, new_para_id)
    source_data = json.loads(source_json)

    assert source_data["source_id"] == para_id
    assert source_data["source_type"] == "paragraph"
    assert "copied_at" in source_data

def test_docx_copy_heading_tool():
    """Test that headings can be copied as they are paragraphs."""
    session_id = docx_create()

    # Create heading
    h_id = docx_add_heading(session_id, "My Heading", level=1)

    # Copy it
    new_h_id = docx_copy_paragraph(session_id, h_id)

    # Verify metadata
    source_json = docx_get_element_source(session_id, new_h_id)
    source_data = json.loads(source_json)
    assert source_data["source_id"] == h_id

def test_docx_copy_invalid_input():
    session_id = docx_create()
    with pytest.raises(ValueError):
        docx_copy_paragraph(session_id, "invalid_id")
