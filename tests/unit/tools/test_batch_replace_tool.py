import pytest
import json
from docx_mcp_server.server import docx_create, docx_add_paragraph, docx_batch_replace_text

def test_docx_batch_replace_tool():
    """Test the batch replace tool via server API."""
    session_id = docx_create()

    # Create content
    docx_add_paragraph(session_id, "Hello {NAME}, today is {DAY}.")
    docx_add_paragraph(session_id, "Another {NAME} instance.")

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
