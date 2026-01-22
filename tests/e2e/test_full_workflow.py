import pytest
import os
import json
from docx_mcp_server.server import (
    docx_create,
    docx_add_paragraph,
    docx_add_run,
    docx_set_properties,
    docx_add_table,
    docx_fill_table,
    docx_find_table,
    docx_copy_table,
    docx_replace_text,
    docx_save,
    docx_close,
    session_manager
)

def _extract(response):
    data = json.loads(response)
    if data["status"] == "error":
        raise ValueError(f"Tool failed: {data['message']}")
    return data["data"]

# E2E test simulating a user workflow
def test_full_workflow(tmp_path):
    output_file = tmp_path / "report.docx"
    output_path = str(output_file)

    # 1. Create Document
    sid = docx_create(auto_save=False)

    # 2. Add Title
    title_resp = docx_add_paragraph(sid, "Monthly Report", style="Heading 1")
    title_id = _extract(title_resp)["element_id"]
    docx_set_properties(sid, json.dumps({"paragraph_format": {"alignment": "center"}}), title_id)

    # 3. Add Intro text
    para_resp = docx_add_paragraph(sid, "This report covers the period: {{period}}.")
    para_id = _extract(para_resp)["element_id"]

    # 4. Create Data Table
    table_resp = docx_add_table(sid, rows=1, cols=3)
    table_id = _extract(table_resp)["element_id"]

    # 5. Fill Table Headers & Data
    data = [
        ["Metric", "Value", "Status"],
        ["Revenue", "$1M", "Green"],
        ["Users", "50k", "Yellow"]
    ]
    docx_fill_table(sid, json.dumps(data), table_id)

    # 6. Find Table (Simulation of navigation)
    found_resp = docx_find_table(sid, "Revenue")
    found_id = _extract(found_resp)["element_id"]
    # Verify it found the correct table (should be same underlying object as table_id)
    # IDs might differ if re-registered, but logic holds.

    # 7. Copy Table (Template usage)
    copy_resp = docx_copy_table(sid, found_id)
    copy_id = _extract(copy_resp)["element_id"]

    # 8. Modify Copy (Fill with different data)
    new_data = [
        ["Metric", "Value", "Status"],
        ["Cost", "$500k", "Red"]
    ]
    docx_fill_table(sid, json.dumps(new_data), copy_id)

    # 9. Replace Placeholders
    docx_replace_text(sid, "{{period}}", "January 2026")

    # 10. Save
    docx_save(sid, output_path)

    # 11. Close
    docx_close(sid)

    # Verification
    assert os.path.exists(output_path)

    # Verify content using python-docx directly
    from docx import Document
    doc = Document(output_path)

    # Check text replacement
    full_text = "\n".join([p.text for p in doc.paragraphs])
    assert "January 2026" in full_text
    assert "{{period}}" not in full_text

    # Check tables
    assert len(doc.tables) == 2

    t1 = doc.tables[0]
    assert t1.cell(1, 0).text == "Revenue"

    t2 = doc.tables[1]
    assert t2.cell(1, 0).text == "Cost"
