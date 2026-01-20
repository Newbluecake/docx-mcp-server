"""E2E test for paragraph copying functionality."""

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
    docx_set_alignment,
    docx_copy_paragraph,
    docx_save,
    docx_close
)

def test_copy_paragraph_e2e():
    """Test copying paragraphs and verify in saved document."""
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        output_path = tmp.name

    try:
        # Create session
        session_id = docx_create()

        # Create original paragraph with formatting
        para1_id = docx_add_paragraph(session_id, "")
        run1_id = docx_add_run(session_id, para1_id, "This is ")
        run2_id = docx_add_run(session_id, para1_id, "formatted ")
        docx_set_font(session_id, run2_id, bold=True, color_hex="FF0000")
        run3_id = docx_add_run(session_id, para1_id, "text")
        docx_set_alignment(session_id, para1_id, "center")

        # Copy the paragraph
        para2_id = docx_copy_paragraph(session_id, para1_id)

        # Add another paragraph
        para3_id = docx_add_paragraph(session_id, "Normal paragraph")

        # Copy it too
        para4_id = docx_copy_paragraph(session_id, para3_id)

        # Save
        docx_save(session_id, output_path)
        docx_close(session_id)

        # Verify the saved document
        doc = Document(output_path)
        assert len(doc.paragraphs) == 4

        # Check first two paragraphs are identical
        assert doc.paragraphs[0].text == doc.paragraphs[1].text
        assert doc.paragraphs[0].text == "This is formatted text"
        assert doc.paragraphs[0].alignment == doc.paragraphs[1].alignment

        # Check last two paragraphs are identical
        assert doc.paragraphs[2].text == doc.paragraphs[3].text
        assert doc.paragraphs[2].text == "Normal paragraph"

        print(f"✓ E2E test passed! Document saved to {output_path}")

    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)

if __name__ == "__main__":
    test_copy_paragraph_e2e()
