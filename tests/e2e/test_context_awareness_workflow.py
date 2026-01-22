"""E2E test for Cursor Context Awareness workflow."""

import pytest
import re
import json
from docx_mcp_server.tools.session_tools import docx_create
from docx_mcp_server.tools.paragraph_tools import docx_insert_paragraph, docx_insert_heading
from docx_mcp_server.tools.run_tools import docx_insert_run, docx_set_font
from docx_mcp_server.tools.table_tools import docx_insert_table, docx_insert_paragraph_to_cell, docx_get_cell
from docx_mcp_server.tools.cursor_tools import docx_cursor_move
from docx_mcp_server.server import session_manager

def _extract(response):
    data = json.loads(response)
    if data["status"] == "error":
        raise ValueError(f"Tool failed: {data['message']}")
    return data

def test_context_awareness_workflow():
    # 1. Create a new document
    session_id = docx_create()

    # 2. Add Title (Heading)
    h1_resp = docx_insert_heading(session_id, "Project Report", position="end:document_body", level=1)
    data = _extract(h1_resp)
    assert "para_" in data["data"]["element_id"]
    assert "cursor" in data["data"]
    cursor = data["data"]["cursor"]
    context_field = cursor.get("visual") or cursor.get("context")
    assert "Project Report" in context_field

    # 3. Add Introduction (Paragraph)
    p1_resp = docx_insert_paragraph(session_id, "This is the introduction.", position="end:document_body")
    data = _extract(p1_resp)
    p1_id = data["data"]["element_id"]
    cursor = data["data"]["cursor"]
    context_field = cursor.get("visual") or cursor.get("context")
    # Expectation: Context should show Heading as previous element
    assert "Project Report" in context_field  # Previous element
    assert "This is the introduction" in context_field # Current element

    # 4. Add Table
    t1_resp = docx_insert_table(session_id, rows=2, cols=2, position="end:document_body")
    data = _extract(t1_resp)
    t1_id = data["data"]["element_id"]
    cursor = data["data"]["cursor"]
    context_field = cursor.get("visual") or cursor.get("context")
    # Expectation: Context should show Para 1 as previous
    assert "This is the introduction" in context_field
    assert "Table" in context_field

    # 5. Fill Table Cell
    c1_resp = docx_get_cell(session_id, t1_id, 0, 0)
    c1_data = _extract(c1_resp)
    c1_id = c1_data["data"]["element_id"]

    cell_p_resp = docx_insert_paragraph_to_cell(session_id, "Header 1", position=f"inside:{c1_id}")
    cell_data = _extract(cell_p_resp)
    cursor = cell_data["data"]["cursor"]
    context_field = cursor.get("visual") or cursor.get("context")
    # Expectation: Context inside cell
    assert "Header 1" in context_field

    # 6. Move Cursor back to Introduction
    move_resp = docx_cursor_move(session_id, p1_id, "after")
    move_data = _extract(move_resp)
    context = move_data["data"]["cursor"]["context"]
    # Expectation: Context shows surrounding elements of Para 1
    assert "Project Report" in context # Before
    assert "Table" in context # After (since we are at p1)

    # 7. Insert Paragraph at Cursor (between Para 1 and Table)
    ins_resp = docx_insert_paragraph(session_id, "Inserted Middle Paragraph", position=f"after:{p1_id}")
    ins_data = _extract(ins_resp)
    ins_id = ins_data["data"]["element_id"]
    # Just verify we got a valid ID and cursor info
    assert "para_" in ins_id
    assert "cursor" in ins_data["data"]

    # 8. Add Run to the new paragraph
    run_resp = docx_insert_run(session_id, " [Bold Text]", position=f"inside:{ins_id}")
    run_data = _extract(run_resp)
    run_id = run_data["data"]["element_id"]

    assert "run_" in run_id

    # 9. Format the run
    fmt_resp = docx_set_font(session_id, run_id, bold=True)
    fmt_data = _extract(fmt_resp)

    assert fmt_data["message"] == "Font updated successfully"
    assert "changed_properties" in fmt_data["data"]

    print("\n✅ E2E Workflow Completed Successfully")
