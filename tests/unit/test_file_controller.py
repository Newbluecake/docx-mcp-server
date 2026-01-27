"""Unit tests for FileController.

Tests file switching, status queries, and error handling.
"""

import os
import pytest
import tempfile
from unittest.mock import Mock, patch, MagicMock
from docx_mcp_server.api.file_controller import (
    FileController,
    FileLockError,
    UnsavedChangesError
)
from docx_mcp_server.core.global_state import global_state


@pytest.fixture
def temp_docx():
    """Create a temporary .docx file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        f.write(b"PK")  # Minimal ZIP signature
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def mock_session_manager():
    """Mock the session_manager and version."""
    mock = MagicMock()
    with patch('docx_mcp_server.api.file_controller._get_session_manager', return_value=mock), \
         patch('docx_mcp_server.api.file_controller._get_version', return_value="test-version"):
        yield mock


@pytest.fixture(autouse=True)
def reset_global_state():
    """Reset global state before each test."""
    global_state.clear()
    yield
    global_state.clear()


class TestFileControllerSwitchFile:
    """Test suite for FileController.switch_file()."""

    def test_switch_file_success(self, temp_docx, mock_session_manager):
        """Test successful file switch."""
        result = FileController.switch_file(temp_docx, force=False)

        assert result["currentFile"] == temp_docx
        assert result["sessionId"] is None
        assert global_state.active_file == temp_docx
        assert global_state.active_session_id is None

    def test_switch_file_not_found(self, mock_session_manager):
        """Test switching to non-existent file."""
        with pytest.raises(FileNotFoundError) as exc_info:
            FileController.switch_file("/nonexistent/file.docx")

        assert "File not found" in str(exc_info.value)

    def test_switch_file_permission_denied(self, temp_docx, mock_session_manager):
        """Test switching to file without permissions."""
        # Make file read-only
        os.chmod(temp_docx, 0o444)

        try:
            with pytest.raises(PermissionError) as exc_info:
                FileController.switch_file(temp_docx)

            assert "Permission denied" in str(exc_info.value)
        finally:
            # Restore permissions for cleanup
            os.chmod(temp_docx, 0o644)

    def test_switch_file_with_unsaved_changes_no_force(self, temp_docx, mock_session_manager):
        """Test switching with unsaved changes (force=False) raises error."""
        # Setup: active session with unsaved changes
        global_state.active_file = "/old.docx"
        global_state.active_session_id = "session-123"

        mock_session = Mock()
        mock_session.has_unsaved_changes = Mock(return_value=True)
        mock_session_manager.get_session = Mock(return_value=mock_session)

        # Should raise UnsavedChangesError
        with pytest.raises(UnsavedChangesError) as exc_info:
            FileController.switch_file(temp_docx, force=False)

        assert "Unsaved changes exist" in str(exc_info.value)
        # Should not close session or switch file
        assert global_state.active_file == "/old.docx"
        assert global_state.active_session_id == "session-123"

    def test_switch_file_with_unsaved_changes_force(self, temp_docx, mock_session_manager):
        """Test switching with unsaved changes (force=True) succeeds."""
        # Setup: active session with unsaved changes
        global_state.active_file = "/old.docx"
        global_state.active_session_id = "session-123"

        mock_session = Mock()
        mock_session.has_unsaved_changes = Mock(return_value=True)
        mock_session_manager.get_session = Mock(return_value=mock_session)

        # Should succeed with force=True
        result = FileController.switch_file(temp_docx, force=True)

        assert result["currentFile"] == temp_docx
        assert global_state.active_file == temp_docx
        assert global_state.active_session_id is None
        # Should close old session
        mock_session_manager.close_session.assert_called_once_with("session-123")

    def test_switch_file_closes_existing_session(self, temp_docx, mock_session_manager):
        """Test that switching closes existing session."""
        # Setup: active session without unsaved changes
        global_state.active_file = "/old.docx"
        global_state.active_session_id = "session-123"

        mock_session = Mock()
        mock_session.has_unsaved_changes = Mock(return_value=False)
        mock_session_manager.get_session = Mock(return_value=mock_session)

        # Switch file
        FileController.switch_file(temp_docx)

        # Should close old session
        mock_session_manager.close_session.assert_called_once_with("session-123")
        assert global_state.active_file == temp_docx
        assert global_state.active_session_id is None

    def test_switch_file_invalid_path(self, mock_session_manager):
        """Test switching with invalid path."""
        with pytest.raises(FileNotFoundError):
            FileController.switch_file("../../../etc/passwd")

    @patch('docx_mcp_server.api.file_controller.FileController._is_file_locked')
    def test_switch_file_locked(self, mock_is_locked, temp_docx, mock_session_manager):
        """Test switching to locked file."""
        mock_is_locked.return_value = True

        with pytest.raises(FileLockError) as exc_info:
            FileController.switch_file(temp_docx)

        assert "locked" in str(exc_info.value).lower()


class TestFileControllerGetStatus:
    """Test suite for FileController.get_status()."""

    def test_get_status_no_active_file(self, mock_session_manager):
        """Test status query with no active file."""
        status = FileController.get_status()

        assert status["currentFile"] is None
        assert status["sessionId"] is None
        assert status["hasUnsaved"] is False
        assert "serverVersion" in status

    def test_get_status_with_active_file_no_session(self, mock_session_manager):
        """Test status query with active file but no session."""
        global_state.active_file = "/path/to/doc.docx"

        status = FileController.get_status()

        assert status["currentFile"] == "/path/to/doc.docx"
        assert status["sessionId"] is None
        assert status["hasUnsaved"] is False

    def test_get_status_with_active_session_no_changes(self, mock_session_manager):
        """Test status query with active session without changes."""
        global_state.active_file = "/path/to/doc.docx"
        global_state.active_session_id = "session-123"

        mock_session = Mock()
        mock_session.has_unsaved_changes = Mock(return_value=False)
        mock_session_manager.get_session = Mock(return_value=mock_session)

        status = FileController.get_status()

        assert status["currentFile"] == "/path/to/doc.docx"
        assert status["sessionId"] == "session-123"
        assert status["hasUnsaved"] is False

    def test_get_status_with_unsaved_changes(self, mock_session_manager):
        """Test status query with unsaved changes."""
        global_state.active_file = "/path/to/doc.docx"
        global_state.active_session_id = "session-123"

        mock_session = Mock()
        mock_session.has_unsaved_changes = Mock(return_value=True)
        mock_session_manager.get_session = Mock(return_value=mock_session)

        status = FileController.get_status()

        assert status["hasUnsaved"] is True


class TestFileControllerCloseSession:
    """Test suite for FileController.close_session()."""

    def test_close_session_no_active_session(self, mock_session_manager):
        """Test closing when no session is active."""
        result = FileController.close_session()

        assert result["success"] is True
        assert "No active session" in result["message"]
        mock_session_manager.close_session.assert_not_called()

    def test_close_session_without_save(self, mock_session_manager):
        """Test closing session without saving."""
        global_state.active_session_id = "session-123"

        result = FileController.close_session(save=False)

        assert result["success"] is True
        mock_session_manager.close_session.assert_called_once_with("session-123")
        assert global_state.active_session_id is None

    def test_close_session_with_save(self, mock_session_manager):
        """Test closing session with save."""
        global_state.active_file = "/path/to/doc.docx"
        global_state.active_session_id = "session-123"

        mock_session = Mock()
        mock_document = Mock()
        mock_session.document = mock_document
        mock_session_manager.get_session = Mock(return_value=mock_session)

        result = FileController.close_session(save=True)

        assert result["success"] is True
        mock_document.save.assert_called_once_with("/path/to/doc.docx")
        mock_session_manager.close_session.assert_called_once_with("session-123")


class TestFileControllerHelpers:
    """Test suite for FileController helper methods."""

    def test_is_file_locked_not_locked(self, temp_docx):
        """Test file lock check for unlocked file."""
        assert FileController._is_file_locked(temp_docx) is False

    def test_has_unsaved_changes_with_method(self):
        """Test unsaved changes check with has_unsaved_changes method."""
        mock_session = Mock()
        mock_session.has_unsaved_changes = Mock(return_value=True)

        assert FileController._has_unsaved_changes(mock_session) is True

    def test_has_unsaved_changes_with_history_stack(self):
        """Test unsaved changes check with history_stack (legacy)."""
        from docx_mcp_server.core.commit import Commit

        mock_session = Mock()
        del mock_session.has_unsaved_changes  # Remove method to test fallback
        mock_session.history_stack = [Commit.create(
            operation="test_operation",
            changes={},
            affected_elements=[]
        )]

        assert FileController._has_unsaved_changes(mock_session) is True

    def test_has_unsaved_changes_no_changes(self):
        """Test unsaved changes check with no changes."""
        mock_session = Mock()
        mock_session.has_unsaved_changes = Mock(return_value=False)

        assert FileController._has_unsaved_changes(mock_session) is False
