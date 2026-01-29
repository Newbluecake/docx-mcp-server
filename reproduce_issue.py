
import sys
import os
from unittest.mock import MagicMock

# Mock modules to avoid dependencies issues
sys.modules['docx'] = MagicMock()
sys.modules['docx.text.paragraph'] = MagicMock()
sys.modules['docx.table'] = MagicMock()
sys.modules['mcp.server.fastmcp'] = MagicMock()

# Setup paths
sys.path.insert(0, os.path.abspath("src"))

# Mock session helpers
from docx_mcp_server.utils import session_helpers
session_helpers.get_active_session = MagicMock()

# Mock session and document
mock_session = MagicMock()
mock_session.session_id = "test-session"
mock_doc = MagicMock()
mock_doc.element.body.iterchildren.return_value = []
mock_session.document = mock_doc

# Setup get_active_session return value
session_helpers.get_active_session.return_value = (mock_session, None)

# Import the function
from docx_mcp_server.tools.content_tools import docx_read_content

# Run it
print("--- Calling docx_read_content ---")
result = docx_read_content(return_json=False)
print(f"Type: {type(result)}")
print(f"Result: {result!r}")

print("\n--- Calling docx_read_content(return_json=True) ---")
result_json = docx_read_content(return_json=True)
print(f"Type: {type(result_json)}")
print(f"Result: {result_json!r}")
