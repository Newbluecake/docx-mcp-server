import pytest
import json
from docx_mcp_server.server import docx_create, session_manager
from docx_mcp_server.tools.paragraph_tools import docx_add_paragraph

def _extract_id(response):
    data = json.loads(response)
    return data["data"]["element_id"]

def test_add_paragraph_position_after():
    session_id = docx_create()

    # Create P1
    p1_resp = docx_add_paragraph(session_id, "P1")
    p1_id = _extract_id(p1_resp)

    # Create P3 (appended)
    p3_resp = docx_add_paragraph(session_id, "P3")

    # Insert P2 after P1 using position
    p2_resp = docx_add_paragraph(session_id, "P2", position=f"after:{p1_id}")
    p2_id = _extract_id(p2_resp)

    # Verify Order
    session = session_manager.get_session(session_id)
    paras = session.document.paragraphs
    assert paras[0].text == "P1"
    assert paras[1].text == "P2"
    assert paras[2].text == "P3"

    # Verify Context Response
    data = json.loads(p2_resp)["data"]
    assert "cursor" in data
    assert "visual" in data["cursor"]
    print(data["cursor"]["visual"])
    assert "P2" in data["cursor"]["visual"]
    assert "P1" in data["cursor"]["visual"]

def test_add_paragraph_position_before():
    session_id = docx_create()

    # Create P2
    p2_resp = docx_add_paragraph(session_id, "P2")
    p2_id = _extract_id(p2_resp)

    # Insert P1 before P2
    p1_resp = docx_add_paragraph(session_id, "P1", position=f"before:{p2_id}")

    # Verify Order
    session = session_manager.get_session(session_id)
    paras = session.document.paragraphs
    assert paras[0].text == "P1"
    assert paras[1].text == "P2"

def test_add_paragraph_position_start():
    session_id = docx_create()

    docx_add_paragraph(session_id, "Existing")

    # Insert at start of document
    docx_add_paragraph(session_id, "Start", position="start:document_body")

    session = session_manager.get_session(session_id)
    paras = session.document.paragraphs
    assert paras[0].text == "Start"
    assert paras[1].text == "Existing"
