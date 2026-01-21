import pytest
from docx_mcp_server.tools.session_tools import docx_create
from docx_mcp_server.tools.paragraph_tools import docx_add_paragraph
from docx_mcp_server.tools.cursor_tools import (
    docx_cursor_move,
    docx_insert_paragraph_at_cursor,
    docx_insert_table_at_cursor
)
from docx_mcp_server.tools.table_tools import docx_add_table
from docx_mcp_server.server import session_manager

def test_cursor_workflow():
    # 1. Create session
    session_id = docx_create()

    # 2. Add initial content (Para 1, Para 2, Para 3)
    p1 = docx_add_paragraph(session_id, "Paragraph 1")
    p2 = docx_add_paragraph(session_id, "Paragraph 2")
    p3 = docx_add_paragraph(session_id, "Paragraph 3")

    # 3. Move cursor BEFORE Paragraph 2
    docx_cursor_move(session_id, p2, "before")

    # 4. Insert "Paragraph 1.5" (Should be between 1 and 2)
    p1_5 = docx_insert_paragraph_at_cursor(session_id, "Paragraph 1.5")

    # 5. Move cursor AFTER Paragraph 2
    docx_cursor_move(session_id, p2, "after")

    # 6. Insert "Paragraph 2.5" (Should be between 2 and 3)
    p2_5 = docx_insert_paragraph_at_cursor(session_id, "Paragraph 2.5")

    # 7. Insert Table AFTER Paragraph 2.5 (implicitly, as cursor stays after inserted element?
    # Wait, tool impl doesn't auto-update cursor unless we want it to.
    # Let's check impl: The tool just returns ID. It doesn't update cursor position implicitly
    # BUT the session.last_created_id updates.
    # Users usually expect cursor to move to end of inserted content.
    # For now, let's explicit move or assume cursor stays where it was?
    # The current implementation of `docx_insert_paragraph_at_cursor` does NOT update `session.cursor`.
    # So cursor is still "after p2".

    # Let's move cursor explicitly to be safe for this test
    docx_cursor_move(session_id, p2_5, "after")
    t1 = docx_insert_table_at_cursor(session_id, 2, 2)

    # 8. Verify Order
    session = session_manager.get_session(session_id)
    doc = session.document

    # Expected: P1, P1.5, P2, P2.5, Table, P3
    # Note: P3 was added at the end initially.
    # Inserting P2.5 "after P2" means it is before P3.
    # Inserting Table "after P2.5" means it is before P3.

    elements = doc.paragraphs
    # Note: doc.paragraphs only contains paragraphs, not tables.
    # We need to check body elements to see interleaved tables.

    body_elements = doc._body._element.getchildren()
    # This includes w:p and w:tbl

    # Helper to get text or table
    def get_tag_info(el):
        if el.tag.endswith('p'):
            # It's a paragraph, find text
            # This is low-level xml access, a bit brittle but accurate for order
            # Namespace map might be needed
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
    t1 = docx_add_table(session_id, 1, 1)
    # Get the only cell (0,0) - we don't have a direct tool to get cell ID easily without `docx_get_cell`
    # Let's use `docx_get_cell` from table_tools
    from docx_mcp_server.tools.table_tools import docx_get_cell

    cell_id = docx_get_cell(session_id, t1, 0, 0)

    # Move cursor inside start of cell
    docx_cursor_move(session_id, cell_id, "inside_start")

    # Insert Paragraph "Start"
    docx_insert_paragraph_at_cursor(session_id, "Start")

    # Move cursor inside end of cell
    docx_cursor_move(session_id, cell_id, "inside_end")

    # Insert Paragraph "End"
    docx_insert_paragraph_at_cursor(session_id, "End")

    # Verify cell content
    session = session_manager.get_session(session_id)
    cell = session.get_object(cell_id)

    assert cell.paragraphs[0].text == "Start"
    assert cell.paragraphs[-1].text == "End"
