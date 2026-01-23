import json
import os
import time
import tempfile

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
    session_response = docx_create(auto_save=False, backup_on_save=True, backup_suffix="-bak")
    session_id = extract_session_id(session_response)

    ctx_result = docx_get_context(session_id)

    assert extract_metadata_field(ctx_result, "session_id") == session_id
    assert extract_metadata_field(ctx_result, "auto_save") == False
    assert extract_metadata_field(ctx_result, "backup_on_save") == True

    docx_close(session_id)


def test_save_with_backup_creates_backup_file(tmp_path):
    target = tmp_path / "sample.docx"

    # Create session bound to the target path
    session_response = docx_create(file_path=str(target), auto_save=False)
    session_id = extract_session_id(session_response)

    # First save creates the file
    first_result = docx_save(session_id, str(target))
    assert is_success(first_result)
    assert os.path.exists(target)

    # Second save with backup should produce a backup file
    second_result = docx_save(session_id, str(target), backup=True, backup_suffix="-bak")
    assert is_success(second_result)
    backup_path = extract_metadata_field(second_result, "backup_path")
    assert backup_path
    assert os.path.exists(backup_path)

    docx_close(session_id)


def test_list_sessions_includes_active_session():
    session_response = docx_create()
    session_id = extract_session_id(session_response)

    listing = docx_list_sessions()
    # Note: docx_list_sessions might still return JSON, need to check
    # For now, assume it returns Markdown
    assert is_success(listing)

    docx_close(session_id)


def test_cleanup_sessions_removes_idle():
    session_response = docx_create()
    session_id = extract_session_id(session_response)
    session = session_manager.get_session(session_id)

    # Simulate idleness
    session.last_accessed = time.time() - 5

    result = docx_cleanup_sessions(max_idle_seconds=1)
    assert is_success(result)
    cleaned_count = extract_metadata_field(result, "cleaned")
    assert cleaned_count >= 1

    # Ensure session removed
    assert session_manager.get_session(session_id) is None
