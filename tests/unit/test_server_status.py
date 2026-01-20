import json
import os
import platform
import sys
from docx_mcp_server.server import docx_server_status

def test_docx_server_status():
    # Call the tool
    result = docx_server_status()

    # Parse the JSON response
    data = json.loads(result)

    # Verify standard fields
    assert data["status"] == "running"
    assert "version" in data
    assert data["cwd"] == os.getcwd()
    assert data["os_name"] == os.name
    assert data["os_system"] == platform.system()
    assert data["path_sep"] == os.sep
    assert "python_version" in data
    assert "start_time" in data
    assert "uptime_seconds" in data
    assert "active_sessions" in data

    # Verify values are reasonable
    assert isinstance(data["uptime_seconds"], float)
    assert data["uptime_seconds"] >= 0
    assert isinstance(data["active_sessions"], int)
