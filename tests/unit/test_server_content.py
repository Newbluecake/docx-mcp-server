import unittest
from docx_mcp_server.server import (
    docx_create,
    docx_add_paragraph,
    docx_add_heading,
    docx_add_run,
    session_manager
)

class TestServerContent(unittest.TestCase):
    def setUp(self):
        session_manager.sessions.clear()
        self.session_id = docx_create()

    def test_add_paragraph(self):
        para_id = docx_add_paragraph(self.session_id, "Hello World")
        self.assertTrue(para_id.startswith("para_"))

        session = session_manager.get_session(self.session_id)
        para = session.get_object(para_id)
        self.assertEqual(para.text, "Hello World")

    def test_add_heading(self):
        head_id = docx_add_heading(self.session_id, "My Title", level=0)
        self.assertTrue(head_id.startswith("para_"))

        session = session_manager.get_session(self.session_id)
        head = session.get_object(head_id)
        self.assertEqual(head.text, "My Title")
        self.assertEqual(head.style.name, "Title")

    def test_add_run(self):
        para_id = docx_add_paragraph(self.session_id, "Start: ")
        run_id = docx_add_run(self.session_id, para_id, "Appended Text")

        self.assertTrue(run_id.startswith("run_"))

        session = session_manager.get_session(self.session_id)
        para = session.get_object(para_id)
        self.assertEqual(para.text, "Start: Appended Text")

    def test_invalid_ids(self):
        with self.assertRaises(ValueError):
            docx_add_paragraph("bad_session", "text")

        with self.assertRaises(ValueError):
            docx_add_run(self.session_id, "bad_para_id", "text")

if __name__ == '__main__':
    unittest.main()
