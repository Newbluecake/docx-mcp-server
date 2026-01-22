import pytest
import json
from docx_mcp_server.server import docx_create, docx_insert_paragraph, docx_insert_run, docx_set_font, docx_copy_paragraph, docx_get_element_source, docx_insert_heading


def _extract_element_id(response):
    """Extract element_id from JSON response or return as-is if plain string."""
    try:
        data = json.loads(response)
        if isinstance(data, dict) and "data" in data and "element_id" in data["data"]:
            return data["data"]["element_id"]
        return response
    except (json.JSONDecodeError, KeyError):
        return response

def test_docx_copy_paragraph_tool():
    """Test the atomic paragraph copy tool via server API."""
    session_id = docx_create()

    # Create source paragraph with complex formatting
    para_response = docx_insert_paragraph(session_id, "Source Paragraph", position="end:document_body")
    para_id = _extract_element_id(para_response)
    run_response = docx_insert_run(session_id, " Bold Part", position=f"inside:{para_id}")
    run_id = _extract_element_id(run_response)
    docx_set_font(session_id, run_id, bold=True, size=14, color_hex="FF0000")

    # Copy it
    new_para_response = docx_copy_paragraph(session_id, para_id, position="end:document_body")
    new_para_id = _extract_element_id(new_para_response)

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
    h_response = docx_insert_heading(session_id, "My Heading", position="end:document_body", level=1)
    h_id = _extract_element_id(h_response)

    # Copy it
    new_h_response = docx_copy_paragraph(session_id, h_id, position="end:document_body")
    new_h_id = _extract_element_id(new_h_response)

    # Verify metadata
    source_json = docx_get_element_source(session_id, new_h_id)
    source_data = json.loads(source_json)
    assert source_data["source_id"] == h_id

def test_docx_copy_invalid_input():
    session_id = docx_create()
    result = docx_copy_paragraph(session_id, "invalid_id", position="end:document_body")
    # Check if it's a JSON error response
    try:
        data = json.loads(result)
        assert data["status"] == "error"
        assert "not found" in data["message"].lower() or "invalid" in data["message"].lower()
    except (json.JSONDecodeError, KeyError):
        # If not JSON, should raise ValueError
        pytest.fail("Expected JSON error response or ValueError")
