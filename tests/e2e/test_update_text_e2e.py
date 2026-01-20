"""E2E test for text update functionality."""

import sys
import os
import tempfile
from docx import Document

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from docx_mcp_server.server import (
    docx_create,
    docx_add_paragraph,
    docx_add_run,
    docx_set_font,
    docx_update_paragraph_text,
    docx_update_run_text,
    docx_save,
    docx_close
)

def test_update_text_e2e():
    """Test text updates and verify in saved document."""
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        output_path = tmp.name

    try:
        # Create session
        session_id = docx_create()

        # Create original content
        para1_id = docx_add_paragraph(session_id, "Original paragraph 1")

        para2_id = docx_add_paragraph(session_id, "")
        run1_id = docx_add_run(session_id, para2_id, "Original run")
        docx_set_font(session_id, run1_id, bold=True, size=14)

        # Update paragraph text
        docx_update_paragraph_text(session_id, para1_id, "Updated paragraph 1")

        # Update run text (should preserve formatting)
        docx_update_run_text(session_id, run1_id, "Updated run")

        # Save
        docx_save(session_id, output_path)
        docx_close(session_id)

        # Verify the saved document
        doc = Document(output_path)
        assert len(doc.paragraphs) == 2

        # Check updated paragraph
        assert doc.paragraphs[0].text == "Updated paragraph 1"
        assert "Original paragraph 1" not in doc.paragraphs[0].text

        # Check updated run
        assert doc.paragraphs[1].text == "Updated run"
        assert "Original run" not in doc.paragraphs[1].text

        # Verify formatting is preserved
        assert doc.paragraphs[1].runs[0].font.bold == True
        assert doc.paragraphs[1].runs[0].font.size.pt == 14

        print(f"✓ E2E test passed! Document saved to {output_path}")

    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)

if __name__ == "__main__":
    test_update_text_e2e()
