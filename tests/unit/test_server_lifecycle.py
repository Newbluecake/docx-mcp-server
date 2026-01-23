import unittest
import os
import tempfile
from docx_mcp_server.server import docx_create, docx_save, docx_close, session_manager

# Add parent directory to path for helpers import
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from helpers import (
    extract_session_id,
    extract_element_id,
    extract_metadata_field,
    is_success,
    is_error
)

class TestServerLifecycle(unittest.TestCase):
    def setUp(self):
        # Clear sessions before each test
        session_manager.sessions.clear()

    def test_create_session(self):
        session_response = docx_create()

        session_id = extract_session_id(session_response)
        self.assertIsNotNone(session_id)
        self.assertIn(session_id, session_manager.sessions)

    def test_save_document(self):
        session_response = docx_create()

        session_id = extract_session_id(session_response)

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            result = docx_save(session_id, tmp_path)
            self.assertTrue(is_success(result))
            self.assertTrue(os.path.exists(tmp_path))
            # Basic check if it's a zip file (docx format)
            with open(tmp_path, 'rb') as f:
                header = f.read(4)
                self.assertEqual(header, b'PK\x03\x04')
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_close_session(self):
        session_response = docx_create()

        session_id = extract_session_id(session_response)
        result = docx_close(session_id)
        self.assertTrue(is_success(result))
        self.assertNotIn(session_id, session_manager.sessions)

    def test_save_invalid_session(self):
        result = docx_save("invalid_id", "test.docx")
        self.assertTrue(is_error(result))

if __name__ == '__main__':
    unittest.main()
