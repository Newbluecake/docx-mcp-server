import pytest
import time
from unittest.mock import MagicMock, patch
from docx_mcp_server.core.session import Session, SessionManager

def test_session_initialization():
    doc = MagicMock()
    session = Session(session_id="test", document=doc)
    assert session.last_created_id is None
    assert session.last_accessed_id is None
    assert session.auto_save is False

def test_update_context_create():
    doc = MagicMock()
    session = Session(session_id="test", document=doc)

    session.update_context("para_1", action="create")
    assert session.last_created_id == "para_1"
    assert session.last_accessed_id == "para_1"

def test_update_context_access():
    doc = MagicMock()
    session = Session(session_id="test", document=doc)

    # First create something
    session.update_context("para_1", action="create")

    # Now access something else
    session.update_context("para_2", action="access")

    # last_created_id should remain para_1
    assert session.last_created_id == "para_1"
    # last_accessed_id should be updated to para_2
    assert session.last_accessed_id == "para_2"

def test_auto_save_trigger():
    doc = MagicMock()
    session = Session(session_id="test", document=doc, file_path="/tmp/test.docx", auto_save=True)

    session.update_context("para_1", action="create")
    doc.save.assert_called_with("/tmp/test.docx")

def test_auto_save_disabled():
    doc = MagicMock()
    session = Session(session_id="test", document=doc, file_path="/tmp/test.docx", auto_save=False)

    session.update_context("para_1", action="create")
    doc.save.assert_not_called()

def test_session_manager_create_with_autosave():
    manager = SessionManager()
    with patch("docx_mcp_server.core.session.Document") as mock_doc:
        sid = manager.create_session(file_path="/tmp/test.docx", auto_save=True)
        session = manager.get_session(sid)
        assert session.auto_save is True
        assert session.file_path == "/tmp/test.docx"
