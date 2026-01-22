import unittest
import json
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx_mcp_server.server import (
    docx_create,
    docx_add_paragraph,
    docx_add_run,
    docx_set_font,
    docx_set_alignment,
    docx_add_page_break,
    docx_set_margins,
    session_manager
)


def _extract_element_id(response):
    """Extract element_id from JSON response or return as-is if plain string."""
    try:
        data = json.loads(response)
        if isinstance(data, dict) and "data" in data and "element_id" in data["data"]:
            return data["data"]["element_id"]
        return response
    except (json.JSONDecodeError, KeyError):
        return response

class TestServerFormatting(unittest.TestCase):
    def setUp(self):
        session_manager.sessions.clear()
        self.session_id = docx_create()

    def test_set_font(self):
        para_response = docx_add_paragraph(self.session_id, "Test Paragraph")
        para_id = _extract_element_id(para_response)
        run_response = docx_add_run(self.session_id, para_id, " Styled Text")
        run_id = _extract_element_id(run_response)

        docx_set_font(self.session_id, run_id, size=14, bold=True, color_hex="FF0000")

        session = session_manager.get_session(self.session_id)
        run = session.get_object(run_id)

        self.assertEqual(run.font.size, Pt(14))
        self.assertTrue(run.font.bold)
        self.assertEqual(run.font.color.rgb, RGBColor(255, 0, 0))

    def test_set_alignment(self):
        para_response = docx_add_paragraph(self.session_id, "Center Me")
        para_id = _extract_element_id(para_response)
        docx_set_alignment(self.session_id, para_id, "center")

        session = session_manager.get_session(self.session_id)
        para = session.get_object(para_id)
        self.assertEqual(para.alignment, WD_ALIGN_PARAGRAPH.CENTER)

    def test_page_break(self):
        # Just ensure it doesn't crash
        result = docx_add_page_break(self.session_id)
        # Check if it's JSON response or plain string
        try:
            data = json.loads(result)
            self.assertEqual(data["status"], "success")
            self.assertIn("page break", data["message"].lower())
        except (json.JSONDecodeError, KeyError):
            self.assertEqual(result, "Page break added")

        session = session_manager.get_session(self.session_id)
        # Verify a paragraph was added (page break is technically a paragraph with a run containing a break?)
        # Actually docx.add_page_break() adds a paragraph with a page break.
        self.assertTrue(len(session.document.paragraphs) > 0)

    def test_set_margins(self):
        docx_set_margins(self.session_id, top=1.5, left=2.0)

        session = session_manager.get_session(self.session_id)
        section = session.document.sections[-1]

        self.assertEqual(section.top_margin, Inches(1.5))
        self.assertEqual(section.left_margin, Inches(2.0))

if __name__ == '__main__':
    unittest.main()
