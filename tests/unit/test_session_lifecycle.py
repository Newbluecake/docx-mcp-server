import json
import os
import time
import tempfile

from docx_mcp_server.tools.session_tools import (
    docx_create,
    docx_close,
    docx_save,
    docx_get_context,
    docx_list_sessions,
    docx_cleanup_sessions,
)
from docx_mcp_server.server import session_manager


def test_create_and_context_with_backup_flags():
    session_id = docx_create(auto_save=False, backup_on_save=True, backup_suffix="-bak")
    ctx = json.loads(docx_get_context(session_id))

    assert ctx["session_id"] == session_id
    assert ctx["auto_save"] is False
    assert ctx["backup_on_save"] is True

    docx_close(session_id)


def test_save_with_backup_creates_backup_file(tmp_path):
    target = tmp_path / "sample.docx"

    # Create session bound to the target path
    session_id = docx_create(file_path=str(target), auto_save=False)

    # First save creates the file
    first = json.loads(docx_save(session_id, str(target)))
    assert first["status"] == "success"
    assert os.path.exists(target)

    # Second save with backup should produce a backup file
    second = json.loads(
        docx_save(session_id, str(target), backup=True, backup_suffix="-bak")
    )
    assert second["status"] == "success"
    backup_path = second["data"]["backup_path"]
    assert backup_path
    assert os.path.exists(backup_path)

    docx_close(session_id)


def test_list_sessions_includes_active_session():
    session_id = docx_create()
    listing = json.loads(docx_list_sessions())

    assert listing["status"] == "success"
    ids = [item["session_id"] for item in listing["data"]]
    assert session_id in ids

    docx_close(session_id)


def test_cleanup_sessions_removes_idle():
    session_id = docx_create()
    session = session_manager.get_session(session_id)

    # Simulate idleness
    session.last_accessed = time.time() - 5

    result = json.loads(docx_cleanup_sessions(max_idle_seconds=1))
    assert result["status"] == "success"
    assert result["data"]["cleaned"] >= 1

    # Ensure session removed
    assert session_manager.get_session(session_id) is None
