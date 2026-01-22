import pytest
import json
from docx_mcp_server.server import docx_create, session_manager
from docx_mcp_server.tools.paragraph_tools import docx_add_paragraph
from docx_mcp_server.tools.table_tools import docx_add_table

def _extract_id(response):
    data = json.loads(response)
    return data["data"]["element_id"]

def test_add_table_position_after():
    session_id = docx_create()

    # Create Anchor Paragraph
    p1_resp = docx_add_paragraph(session_id, "Anchor")
    p1_id = _extract_id(p1_resp)

    # Insert Table after Anchor
    t_resp = docx_add_table(session_id, rows=2, cols=2, position=f"after:{p1_id}")
    t_id = _extract_id(t_resp)

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
    session_id = docx_create()
    docx_add_paragraph(session_id, "Existing")

    # Insert Table at start
    docx_add_table(session_id, 1, 1, position="start:document_body")

    session = session_manager.get_session(session_id)
    children = list(session.document._body._element.iterchildren())
    # Expect: Tbl, P
    assert children[0].tag.endswith('tbl')
    assert children[1].tag.endswith('p')
