import pytest
import json
from docx_mcp_server.server import docx_create, docx_insert_paragraph, docx_copy_elements_range


def _extract_element_id(response):
    """Extract element_id from JSON response or return as-is if plain string."""
    try:
        data = json.loads(response)
        if isinstance(data, dict) and "data" in data and "element_id" in data["data"]:
            return data["data"]["element_id"]
        return response
    except (json.JSONDecodeError, KeyError):
        return response

def test_docx_copy_elements_range_tool():
    """Test the range copy tool."""
    session_id = docx_create()

    # Create content: P1, P2, P3
    p1_response = docx_insert_paragraph(session_id, "P1", position="end:document_body")
    p1_id = _extract_element_id(p1_response)
    p2_response = docx_insert_paragraph(session_id, "P2", position="end:document_body")
    p2_id = _extract_element_id(p2_response)
    p3_response = docx_insert_paragraph(session_id, "P3", position="end:document_body")
    p3_id = _extract_element_id(p3_response)

    # Copy P1-P2 range
    result_json = docx_copy_elements_range(session_id, p1_id, p2_id, position="end:document_body")
    result = json.loads(result_json)

    assert len(result) == 2
    assert result[0]["type"] == "para"
    assert result[1]["type"] == "para"

    # Verify document structure: P1, P2, P3, P1(Copy), P2(Copy)
    # We need to inspect document directly or use read_content (which loses structure)
    # Using finder or just count
    from docx_mcp_server.server import session_manager
    doc = session_manager.get_session(session_id).document
    assert len(doc.paragraphs) == 5
    assert doc.paragraphs[3].text == "P1"
    assert doc.paragraphs[4].text == "P2"
