import unittest
import os
import time
from docx import Document
from docx_mcp_server.core.session import SessionManager, Session

class TestSessionManager(unittest.TestCase):
    def setUp(self):
        self.manager = SessionManager(ttl_seconds=1)

    def test_create_session(self):
        session_id = self.manager.create_session()
        self.assertIsNotNone(session_id)
        self.assertIn(session_id, self.manager.sessions)

        session = self.manager.get_session(session_id)
        self.assertIsInstance(session, Session)
        self.assertIsNotNone(session.document)

    def test_session_expiry(self):
        session_id = self.manager.create_session()
        # Wait for TTL to expire
        time.sleep(1.1)

        session = self.manager.get_session(session_id)
        self.assertIsNone(session)
        self.assertNotIn(session_id, self.manager.sessions)

    def test_object_registry(self):
        session_id = self.manager.create_session()
        session = self.manager.get_session(session_id)

        # Test registering a dummy object
        dummy_obj = {"type": "paragraph", "text": "hello"}
        obj_id = session.register_object(dummy_obj, "para")

        self.assertTrue(obj_id.startswith("para_"))
        self.assertEqual(session.get_object(obj_id), dummy_obj)
        self.assertIsNone(session.get_object("non_existent"))

    def test_close_session(self):
        session_id = self.manager.create_session()
        result = self.manager.close_session(session_id)
        self.assertTrue(result)
        self.assertIsNone(self.manager.get_session(session_id))

if __name__ == '__main__':
    unittest.main()
