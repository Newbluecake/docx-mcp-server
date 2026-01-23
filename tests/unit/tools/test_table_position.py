import pytest
import json
from docx_mcp_server.server import docx_create, session_manager
from docx_mcp_server.tools.paragraph_tools import docx_insert_paragraph
from docx_mcp_server.tools.table_tools import docx_insert_table

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

def test_add_table_position_after():
    session_response = docx_create()

    session_id = extract_session_id(session_response)

    # Create Anchor Paragraph
    p1_resp = docx_insert_paragraph(session_id, "Anchor", position="end:document_body")
    p1_id = extract_element_id(p1_resp)

    # Insert Table after Anchor
    t_resp = docx_insert_table(session_id, rows=2, cols=2, position=f"after:{p1_id}")
    t_id = extract_element_id(t_resp)

    # Verify Order
    session = session_manager.get_session(session_id)
    # Document elements are stored in body._element
    # We can iterate block items to check order
    # Or just check if table is after paragraph
    doc_body = session.document._body
    # python-docx doesn't expose a unified list of paragraphs and tables easily in .elements
    # But we can check xml path or child order
    children = list(doc_body._element.iterchildren())
    assert len(children) >= 2
    # Expect: P (Anchor), Tbl
    assert children[0].tag.endswith('p')
    assert children[1].tag.endswith('tbl')

    # Verify Context Visual
    data = json.loads(t_resp)["data"]
    visual = data["cursor"]["visual"]
    print(visual)
    assert "Table: 2x2" in visual
    assert "Anchor" in visual

def test_add_table_position_start():
    session_response = docx_create()

    session_id = extract_session_id(session_response)
    docx_insert_paragraph(session_id, "Existing", position="end:document_body")

    # Insert Table at start
    docx_insert_table(session_id, 1, 1, position="start:document_body")

    session = session_manager.get_session(session_id)
    children = list(session.document._body._element.iterchildren())
    # Expect: Tbl, P
    assert children[0].tag.endswith('tbl')
    assert children[1].tag.endswith('p')
