import pytest
import json
from docx_mcp_server.server import docx_create, docx_insert_paragraph, docx_batch_replace_text

# Add parent directory to path for helpers import
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from helpers import (
    extract_session_id,
    extract_element_id,
    extract_metadata_field,
    is_success,
    is_error,
    extract_error_message
)

def test_docx_batch_replace_tool():
    """Test the batch replace tool via server API."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)

    # Create content
    docx_insert_paragraph(session_id, "Hello {NAME}, today is {DAY}.", position="end:document_body")
    docx_insert_paragraph(session_id, "Another {NAME} instance.", position="end:document_body")

    # Prepare replacements
    replacements = {
        "{NAME}": "Claude",
        "{DAY}": "Monday"
    }
    replacements_json = json.dumps(replacements)

    # Execute batch replace
    result = docx_batch_replace_text(session_id, replacements_json)

    assert "Replaced 3 occurrences" in result

    # Verify content (using read_content for simplicity, though it loses structure)
    from docx_mcp_server.server import docx_read_content
    content = docx_read_content(session_id)

    assert "Hello Claude, today is Monday." in content
    assert "Another Claude instance." in content
