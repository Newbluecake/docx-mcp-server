import pytest
import json
from docx_mcp_server.tools.session_tools import docx_create
from docx_mcp_server.tools.paragraph_tools import docx_insert_paragraph
from docx_mcp_server.tools.table_tools import docx_insert_table, docx_get_cell, docx_insert_paragraph_to_cell
from docx_mcp_server.server import session_manager

def _extract(response):
    data = json.loads(response)
    if data["status"] == "error":
        raise ValueError(f"Tool failed: {data['message']}")
    return data["data"]

def test_cursor_workflow():
    # 1. Create session
    session_id = docx_create()

    # 2. Add initial content (Para 1, Para 2, Para 3)
    p1_resp = docx_insert_paragraph(session_id, "Paragraph 1", position="end:document_body")
    p1 = _extract(p1_resp)["element_id"]

    p2_resp = docx_insert_paragraph(session_id, "Paragraph 2", position="end:document_body")
    p2 = _extract(p2_resp)["element_id"]

    p3_resp = docx_insert_paragraph(session_id, "Paragraph 3", position="end:document_body")
    p3 = _extract(p3_resp)["element_id"]

    # 3. Insert "Paragraph 1.5" (Should be between 1 and 2)
    p1_5_resp = docx_insert_paragraph(session_id, "Paragraph 1.5", position=f"before:{p2}")
    p1_5 = _extract(p1_5_resp)["element_id"]

    # 4. Insert "Paragraph 2.5" (Should be between 2 and 3)
    p2_5_resp = docx_insert_paragraph(session_id, "Paragraph 2.5", position=f"after:{p2}")
    p2_5 = _extract(p2_5_resp)["element_id"]

    # 5. Insert Table AFTER Paragraph 2.5
    t1_resp = docx_insert_table(session_id, 2, 2, position=f"after:{p2_5}")
    t1 = _extract(t1_resp)["element_id"]

    # 8. Verify Order
    session = session_manager.get_session(session_id)
    doc = session.document

    # Expected: P1, P1.5, P2, P2.5, Table, P3
    body_elements = doc._body._element.getchildren()

    # Helper to get text or table
    def get_tag_info(el):
        if el.tag.endswith('p'):
            return "P: " + "".join([t.text for t in el.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t")])
        elif el.tag.endswith('tbl'):
            return "Table"
        return "Unknown"

    content_log = [get_tag_info(el) for el in body_elements if el.tag.endswith(('p', 'tbl'))]

    print("Content Log:", content_log)

    assert "P: Paragraph 1" in content_log[0]
    assert "P: Paragraph 1.5" in content_log[1]
    assert "P: Paragraph 2" in content_log[2]
    assert "P: Paragraph 2.5" in content_log[3]
    assert "Table" in content_log[4]
    assert "P: Paragraph 3" in content_log[5]

def test_cursor_inside_container():
    session_id = docx_create()

    # Create a table
    t1_resp = docx_insert_table(session_id, 1, 1, position="end:document_body")
    t1 = _extract(t1_resp)["element_id"]

    # Get the only cell (0,0)
    cell_resp = docx_get_cell(session_id, t1, 0, 0)
    cell_id = _extract(cell_resp)["element_id"]

    # Insert Paragraph "Start" at start of cell
    docx_insert_paragraph_to_cell(session_id, "Start", position=f"start:{cell_id}")

    # Insert Paragraph "End" at end of cell
    docx_insert_paragraph_to_cell(session_id, "End", position=f"end:{cell_id}")

    # Verify cell content
    session = session_manager.get_session(session_id)
    cell = session.get_object(cell_id)

    assert cell.paragraphs[0].text == "Start"
    assert cell.paragraphs[-1].text == "End"
