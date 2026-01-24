import sys
import os
import unittest
from unittest.mock import MagicMock, patch

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

# Add src to path
sys.path.insert(0, os.path.abspath("src"))

# We need to mock pywin32 modules BEFORE importing Win32PreviewController
# because it tries to import them at module level
sys.modules["win32com"] = MagicMock()
sys.modules["win32com.client"] = MagicMock()
sys.modules["pywintypes"] = MagicMock()

# Now we can safely import, but we need to ensure HAS_PYWIN32 is True
# We can do this by patching the module after import or controlling the import
# But since the module checks imports on load, and we mocked them, it should set HAS_PYWIN32 = True

from docx_mcp_server.preview.win32 import Win32PreviewController

class TestWin32PreviewController(unittest.TestCase):

    def setUp(self):
        # Reset mocks
        sys.modules["win32com.client"].reset_mock()
        self.controller = Win32PreviewController()

    @patch("docx_mcp_server.preview.win32.win32com.client.GetActiveObject")
    def test_prepare_for_save_found(self, mock_get_active):
        """Test closing a document when it is found open."""
        # Setup Mock App and Document
        mock_app = MagicMock()
        mock_doc = MagicMock()

        # Determine paths
        file_path = os.path.abspath("test.docx")

        # Setup doc properties
        mock_doc.FullName = file_path

        # Setup app.Documents
        mock_app.Documents = [mock_doc]

        # Setup GetActiveObject to return our app
        mock_get_active.return_value = mock_app

        # Run
        result = self.controller.prepare_for_save(file_path)

        # Verify
        self.assertTrue(result)
        mock_doc.Close.assert_called_once_with(SaveChanges=False)
        self.assertIn(file_path, self.controller._was_open_cache)

    @patch("docx_mcp_server.preview.win32.win32com.client.GetActiveObject")
    def test_prepare_for_save_not_found(self, mock_get_active):
        """Test doing nothing when document is not open."""
        mock_app = MagicMock()
        mock_app.Documents = [] # No docs
        mock_get_active.return_value = mock_app

        file_path = os.path.abspath("test.docx")
        result = self.controller.prepare_for_save(file_path)

        self.assertFalse(result)
        self.assertNotIn(file_path, self.controller._was_open_cache)

    @patch("docx_mcp_server.preview.win32.win32com.client.GetActiveObject")
    def test_refresh_success(self, mock_get_active):
        """Test re-opening a document that was cached."""
        file_path = os.path.abspath("test.docx")
        mock_app = MagicMock()
        mock_app.Visible = True

        # Manually populate cache
        self.controller._was_open_cache[file_path] = (mock_app, True)

        # Run
        result = self.controller.refresh(file_path)

        # Verify
        self.assertTrue(result)
        mock_app.Documents.Open.assert_called_once_with(file_path, ReadOnly=True)
        self.assertNotIn(file_path, self.controller._was_open_cache)

if __name__ == "__main__":
    unittest.main()
