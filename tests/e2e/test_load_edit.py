import pytest
import os
import json
from docx import Document
from docx_mcp_server.server import (
    docx_create,
    docx_save,
    docx_read_content,
    docx_find_paragraphs,
    docx_add_run,
    docx_set_font
)

class TestLoadEditE2E:
    def test_full_workflow(self, tmp_path):
        # 1. Prepare initial document
        initial_doc_path = tmp_path / "initial.docx"
        doc = Document()
        doc.add_paragraph("Title Paragraph")
        doc.add_paragraph("Target: This needs editing.")
        doc.add_paragraph("Footer Paragraph")
        doc.save(str(initial_doc_path))

        # 2. Load the document
        session_id = docx_create(file_path=str(initial_doc_path))
        assert session_id is not None

        # 3. Read content to confirm
        content = docx_read_content(session_id)
        assert "Target: This needs editing." in content

        # 4. Find specific paragraph
        results_json = docx_find_paragraphs(session_id, "Target:")
        results = json.loads(results_json)
        assert len(results) == 1
        para_id = results[0]["id"]

        # 5. Edit (Append text)
        run_id = docx_add_run(session_id, para_id, " [EDITED]")

        # 6. Style the new run
        docx_set_font(session_id, run_id, bold=True, color_hex="FF0000")

        # 7. Save to new file
        final_doc_path = tmp_path / "final.docx"
        docx_save(session_id, str(final_doc_path))

        # 8. Verification
        doc_final = Document(str(final_doc_path))
        full_text = "\n".join([p.text for p in doc_final.paragraphs])

        assert "Target: This needs editing. [EDITED]" in full_text

        # Verify formatting
        # Find the paragraph again in the loaded doc object
        target_para = None
        for p in doc_final.paragraphs:
            if "Target:" in p.text:
                target_para = p
                break

        assert target_para is not None
        # Check the last run for bold/color
        last_run = target_para.runs[-1]
        assert last_run.text == " [EDITED]"
        assert last_run.bold is True
        # Color check might be complex depending on how python-docx stores it,
        # but we know we called the tool.
        assert str(last_run.font.color.rgb) == "FF0000"
