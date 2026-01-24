import pytest
import json
from docx_mcp_server.server import docx_create, session_manager
from docx_mcp_server.tools.paragraph_tools import docx_insert_paragraph

# Add parent directory to path for helpers import
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from helpers import (
    extract_session_id,
    extract_element_id,
    extract_metadata_field,
    is_success,
    is_error,
    extract_error_message
)

def test_add_paragraph_position_after():
    session_response = docx_create()

    session_id = extract_session_id(session_response)

    # Create P1
    p1_resp = docx_insert_paragraph(session_id, "P1", position="end:document_body")
    p1_id = extract_element_id(p1_resp)

    # Create P3 (appended)
    p3_resp = docx_insert_paragraph(session_id, "P3", position="end:document_body")

    # Insert P2 after P1 using position
    p2_resp = docx_insert_paragraph(session_id, "P2", position=f"after:{p1_id}")
    p2_id = extract_element_id(p2_resp)

    # Verify Order
    session = session_manager.get_session(session_id)
    paras = session.document.paragraphs
    assert paras[0].text == "P1"
    assert paras[1].text == "P2"
    assert paras[2].text == "P3"

    # Verify Context Response
    assert "Document Context" in p2_resp
    assert "P2" in p2_resp
    assert "P1" in p2_resp

def test_add_paragraph_position_before():
    session_response = docx_create()

    session_id = extract_session_id(session_response)

    # Create P2
    p2_resp = docx_insert_paragraph(session_id, "P2", position="end:document_body")
    p2_id = extract_element_id(p2_resp)

    # Insert P1 before P2
    p1_resp = docx_insert_paragraph(session_id, "P1", position=f"before:{p2_id}")

    # Verify Order
    session = session_manager.get_session(session_id)
    paras = session.document.paragraphs
    assert paras[0].text == "P1"
    assert paras[1].text == "P2"

def test_add_paragraph_position_start():
    session_response = docx_create()

    session_id = extract_session_id(session_response)

    docx_insert_paragraph(session_id, "Existing", position="end:document_body")

    # Insert at start of document
    docx_insert_paragraph(session_id, "Start", position="start:document_body")

    session = session_manager.get_session(session_id)
    paras = session.document.paragraphs
    assert paras[0].text == "Start"
    assert paras[1].text == "Existing"
