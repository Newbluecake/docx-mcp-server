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

def test_create_with_autosave():
    with patch("docx_mcp_server.core.session.Document") as mock_doc:
        sid = docx_create(file_path="/tmp/test.docx", auto_save=True)
        session = session_manager.get_session(sid)
        assert session.auto_save is True
        assert session.file_path == "/tmp/test.docx"

def test_implicit_context_flow():
    # 1. Create session
    sid = docx_create()
    session = session_manager.get_session(sid)

    # 2. Add paragraph (should set last_created_id)
    p_id = docx_add_paragraph(sid, "Hello")
    assert session.last_created_id == p_id

    # 3. Add run without parent (should use p_id)
    r_id = docx_add_run(sid, " World")
    assert session.last_accessed_id == r_id

    # Verify run was added to paragraph
    para_obj = session.get_object(p_id)
    assert len(para_obj.runs) == 2 # "Hello" + " World" (first run created by add_paragraph)

def test_set_properties_flow():
    sid = docx_create()
    p_id = docx_add_paragraph(sid, "Test Prop")

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
    p_id = docx_add_paragraph(sid, "Context Test")

    # Implicitly use p_id because it was last created/accessed
    props = json.dumps({"alignment": "right"}) # Shortcut property
    docx_set_properties(sid, props) # No element_id

    from docx.enum.text import WD_ALIGN_PARAGRAPH
    para_obj = session_manager.get_session(sid).get_object(p_id)
    assert para_obj.alignment == WD_ALIGN_PARAGRAPH.RIGHT
