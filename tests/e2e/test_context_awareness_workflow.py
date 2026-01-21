"""E2E test for Cursor Context Awareness workflow."""

import pytest
import re
from docx_mcp_server.tools.session_tools import docx_create
from docx_mcp_server.tools.paragraph_tools import docx_add_paragraph, docx_add_heading
from docx_mcp_server.tools.run_tools import docx_add_run, docx_set_font
from docx_mcp_server.tools.table_tools import docx_add_table, docx_add_paragraph_to_cell, docx_get_cell
from docx_mcp_server.tools.cursor_tools import docx_cursor_move, docx_insert_paragraph_at_cursor
from docx_mcp_server.server import session_manager

def extract_context(result_str):
    """Extract context part from tool result."""
    if "Context:" not in result_str:
        return None
    return result_str.split("Context:", 1)[1]

def test_context_awareness_workflow():
    # 1. Create a new document
    session_id = docx_create()

    # 2. Add Title (Heading)
    # Expectation: Context shows "at empty document start" before, but returns new ID + context
    h1_result = docx_add_heading(session_id, "Project Report", level=1)
    print(f"\nStep 2 (Heading): {h1_result}")
    assert "para_" in h1_result
    assert "Context:" in h1_result
    assert "Project Report" in h1_result

    # 3. Add Introduction (Paragraph)
    # Expectation: Context should show Heading as previous element
    p1_result = docx_add_paragraph(session_id, "This is the introduction.")
    print(f"\nStep 3 (Para 1): {p1_result}")
    assert "Project Report" in p1_result  # Previous element
    assert "This is the introduction" in p1_result # Current element

    # Extract ID for later use
    p1_id = p1_result.split('\n')[0]

    # 4. Add Table
    # Expectation: Context should show Para 1 as previous
    t1_result = docx_add_table(session_id, rows=2, cols=2)
    print(f"\nStep 4 (Table): {t1_result}")
    assert "This is the introduction" in t1_result
    assert "Table (2x2)" in t1_result

    t1_id = t1_result.split('\n')[0]

    # 5. Fill Table Cell
    # Expectation: Context inside cell, Parent should be Cell
    c1_id = docx_get_cell(session_id, t1_id, 0, 0)
    cell_p_result = docx_add_paragraph_to_cell(session_id, c1_id, "Header 1")
    print(f"\nStep 5 (Cell Para): {cell_p_result}")
    assert "Parent: _Cell" in cell_p_result or "Parent: Cell" in str(cell_p_result) # Type name might vary slightly
    assert "Header 1" in cell_p_result

    # 6. Move Cursor back to Introduction
    # Expectation: Context shows surrounding elements of Para 1
    move_result = docx_cursor_move(session_id, p1_id, "after")
    print(f"\nStep 6 (Move): {move_result}")
    assert "Project Report" in move_result # Before
    assert "Table" in move_result # After (since we are at p1)

    # 7. Insert Paragraph at Cursor (between Para 1 and Table)
    # Expectation: Context shows P1 before, Table after
    ins_result = docx_insert_paragraph_at_cursor(session_id, "Inserted Middle Paragraph")
    print(f"\nStep 7 (Insert): {ins_result}")
    assert "This is the introduction" in ins_result
    assert "Table" in ins_result
    assert "Inserted Middle Paragraph" in ins_result

    # 8. Add Run to the new paragraph
    # Expectation: Context shows Run level detail?
    # Session support for runs in siblings was added.
    ins_id = ins_result.split('\n')[0]
    run_result = docx_add_run(session_id, " [Bold Text]", paragraph_id=ins_id)
    print(f"\nStep 8 (Run): {run_result}")
    assert "run_" in run_result
    # Context should show the run we just added
    assert "[Bold Text]" in run_result

    # 9. Format the run
    run_id = run_result.split('\n')[0]
    fmt_result = docx_set_font(session_id, run_id, bold=True)
    print(f"\nStep 9 (Format): {fmt_result}")
    assert "Font updated" in fmt_result
    assert "Context:" in fmt_result

    print("\n✅ E2E Workflow Completed Successfully")
