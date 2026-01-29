import json
import os
import platform
import sys
import re
from docx_mcp_server.server import docx_server_status

def test_docx_server_status():
    # Call the tool
    result = docx_server_status()

    # Parse the Markdown response
    assert "# Server Status" in result
    assert "**Status**: running" in result
    assert "**Version**:" in result
    assert "## Environment" in result

    # Extract specific fields using regex
    def extract_field(field_name):
        match = re.search(rf'\*\*{field_name}\*\*:\s*(.+?)(?:\n|$)', result)
        return match.group(1).strip() if match else None

    # Verify standard fields
    assert extract_field("Status") == "running"
    assert extract_field("Version") is not None
    assert extract_field("Active Sessions") is not None
    assert extract_field("Log Level") is not None

    # Verify environment fields
    assert extract_field("OS") is not None
    assert extract_field("Python") is not None
    assert extract_field("Working Directory") is not None

    # Verify uptime is present and reasonable
    uptime_str = extract_field("Uptime")
    assert uptime_str is not None
    assert "seconds" in uptime_str

