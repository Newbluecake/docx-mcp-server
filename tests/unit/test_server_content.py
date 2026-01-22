import unittest
import json
from docx_mcp_server.server import (
    docx_create,
    docx_add_paragraph,
    docx_add_heading,
    docx_add_run,
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

class TestServerContent(unittest.TestCase):
    def setUp(self):
        session_manager.sessions.clear()
        self.session_id = docx_create()

    def test_add_paragraph(self):
        para_response = docx_add_paragraph(self.session_id, "Hello World")
        para_id = _extract_element_id(para_response)
        self.assertTrue(para_id.startswith("para_"))

        session = session_manager.get_session(self.session_id)
        para = session.get_object(para_id)
        self.assertEqual(para.text, "Hello World")

    def test_add_heading(self):
        head_response = docx_add_heading(self.session_id, "My Title", level=0)
        head_id = _extract_element_id(head_response)
        self.assertTrue(head_id.startswith("para_"))

        session = session_manager.get_session(self.session_id)
        head = session.get_object(head_id)
        self.assertEqual(head.text, "My Title")
        self.assertEqual(head.style.name, "Title")

    def test_add_run(self):
        para_response = docx_add_paragraph(self.session_id, "Start: ")
        para_id = _extract_element_id(para_response)
        run_response = docx_add_run(self.session_id, para_id, "Appended Text")
        run_id = _extract_element_id(run_response)

        self.assertTrue(run_id.startswith("run_"))

        session = session_manager.get_session(self.session_id)
        para = session.get_object(para_id)
        self.assertEqual(para.text, "Start: Appended Text")

    def test_invalid_ids(self):
        # Test invalid session - should return error JSON
        result = docx_add_paragraph("bad_session", "text")
        try:
            data = json.loads(result)
            self.assertEqual(data["status"], "error")
        except (json.JSONDecodeError, KeyError):
            self.assertIn("not found", result.lower())

        # Test invalid parent ID - should return error JSON
        result = docx_add_run(self.session_id, "bad_para_id", "text")
        try:
            data = json.loads(result)
            self.assertEqual(data["status"], "error")
        except (json.JSONDecodeError, KeyError):
            self.assertIn("not found", result.lower())

if __name__ == '__main__':
    unittest.main()
