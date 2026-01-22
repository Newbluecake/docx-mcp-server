import pytest
import json
from unittest.mock import MagicMock, patch
from docx_mcp_server.server import (
    docx_create,
    docx_add_paragraph,
    docx_add_run,
    docx_set_properties,
    session_manager
)


def _extract_element_id(response):
    """Extract element_id from JSON response or return as-is if plain string."""
    try:
        data = json.loads(response)
        if isinstance(data, dict) and "data" in data and "element_id" in data["data"]:
            return data["data"]["element_id"]
        return response
    except (json.JSONDecodeError, KeyError):
        return response

def test_create_with_autosave(tmp_path):
    test_file = str(tmp_path / "test.docx")
    with patch("docx_mcp_server.core.session.Document") as mock_doc:
        sid = docx_create(file_path=test_file, auto_save=True)
        session = session_manager.get_session(sid)
        assert session.auto_save is True
        assert session.file_path == test_file

def test_implicit_context_flow():
    # 1. Create session
    sid = docx_create()
    session = session_manager.get_session(sid)

    # 2. Add paragraph (should set last_created_id)
    p_response = docx_add_paragraph(sid, "Hello")
    p_id = _extract_element_id(p_response)
    clean_id = p_id.strip().split()[0]
    assert session.last_created_id == clean_id

    # 3. Add run without parent (should use p_id)
    r_response = docx_add_run(sid, " World")
    r_id = _extract_element_id(r_response)
    clean_rid = r_id.strip().split()[0]
    assert session.last_accessed_id == clean_rid

    # Verify run was added to paragraph
    para_obj = session.get_object(p_id)
    assert len(para_obj.runs) == 2 # "Hello" + " World" (first run created by add_paragraph)

def test_set_properties_flow():
    sid = docx_create()
    p_response = docx_add_paragraph(sid, "Test Prop")
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
    sid = docx_create()
    p_response = docx_add_paragraph(sid, "Context Test")
    p_id = _extract_element_id(p_response)

    # Implicitly use p_id because it was last created/accessed
    props = json.dumps({"alignment": "right"}) # Shortcut property
    docx_set_properties(sid, props) # No element_id

    from docx.enum.text import WD_ALIGN_PARAGRAPH
    para_obj = session_manager.get_session(sid).get_object(p_id)
    assert para_obj.alignment == WD_ALIGN_PARAGRAPH.RIGHT
