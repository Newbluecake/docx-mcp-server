import pytest
import json
from docx_mcp_server.server import docx_create, docx_add_paragraph, docx_copy_elements_range

def test_docx_copy_elements_range_tool():
    """Test the range copy tool."""
    session_id = docx_create()

    # Create content: P1, P2, P3
    p1_id = docx_add_paragraph(session_id, "P1")
    p2_id = docx_add_paragraph(session_id, "P2")
    p3_id = docx_add_paragraph(session_id, "P3")

    # Copy P1-P2 range
    result_json = docx_copy_elements_range(session_id, p1_id, p2_id)
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
