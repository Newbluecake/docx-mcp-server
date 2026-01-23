import pytest
import json
import re
from unittest.mock import MagicMock, patch
from docx_mcp_server.server import (
    docx_create,
    docx_insert_paragraph,
    docx_insert_run,
    docx_set_properties,
    session_manager
)


def _extract_element_id(response):
    """Extract element_id from Markdown response."""
    # Try to extract from Markdown format: **Element ID**: para_xxx
    match = re.search(r'\*\*Element ID\*\*:\s*(\w+)', response)
    if match:
        return match.group(1)
    # Fallback: try JSON format (legacy)
    try:
        data = json.loads(response)
        if isinstance(data, dict) and "data" in data and "element_id" in data["data"]:
            return data["data"]["element_id"]
        return response
    except (json.JSONDecodeError, KeyError):
        return response


def _extract_session_id(response):
    """Extract session_id from Markdown response."""
    # Try to extract from Markdown format: **Session Id**: xxx
    match = re.search(r'\*\*Session Id\*\*:\s*(\S+)', response)
    if match:
        return match.group(1)
    # Fallback: return as-is if it looks like a session ID (short alphanumeric string)
    if isinstance(response, str) and len(response) < 100 and '\n' not in response:
        return response.strip()
    return None


def test_create_with_autosave(tmp_path):
    test_file = str(tmp_path / "test.docx")
    with patch("docx_mcp_server.core.session.Document") as mock_doc:
        response = docx_create(file_path=test_file, auto_save=True)
        sid = _extract_session_id(response)
        session = session_manager.get_session(sid)
        assert session.auto_save is True
        assert session.file_path == test_file

def test_implicit_context_flow():
    # 1. Create session
    response = docx_create()
    sid = _extract_session_id(response)
    session = session_manager.get_session(sid)

    # 2. Add paragraph (should set last_created_id)
    p_response = docx_insert_paragraph(sid, "Hello", position="end:document_body")
    p_id = _extract_element_id(p_response)
    clean_id = p_id.strip().split()[0]
    assert session.last_created_id == clean_id

    # 3. Add run using explicit position
    r_response = docx_insert_run(sid, " World", position=f"inside:{p_id}")
    r_id = _extract_element_id(r_response)
    clean_rid = r_id.strip().split()[0]
    assert session.last_accessed_id == clean_rid

    # Verify run was added to paragraph
    para_obj = session.get_object(p_id)
    assert len(para_obj.runs) == 2 # "Hello" + " World" (first run created by add_paragraph)

def test_set_properties_flow():
    response = docx_create()
    sid = _extract_session_id(response)
    p_response = docx_insert_paragraph(sid, "Test Prop", position="end:document_body")
    p_id = _extract_element_id(p_response)

    # Set alignment via properties
    props = json.dumps({
        "paragraph_format": {"alignment": "center"}
    })
    docx_set_properties(sid, props, element_id=p_id)

    from docx.enum.text import WD_ALIGN_PARAGRAPH
    para_obj = session_manager.get_session(sid).get_object(p_id)
    assert para_obj.paragraph_format.alignment == WD_ALIGN_PARAGRAPH.CENTER

def test_set_properties_implicit_context():
    response = docx_create()
    sid = _extract_session_id(response)
    p_response = docx_insert_paragraph(sid, "Context Test", position="end:document_body")
    p_id = _extract_element_id(p_response)

    # Implicitly use p_id because it was last created/accessed
    props = json.dumps({"alignment": "right"}) # Shortcut property
    docx_set_properties(sid, props) # No element_id

    from docx.enum.text import WD_ALIGN_PARAGRAPH
    para_obj = session_manager.get_session(sid).get_object(p_id)
    assert para_obj.alignment == WD_ALIGN_PARAGRAPH.RIGHT
