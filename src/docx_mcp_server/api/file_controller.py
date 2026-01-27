"""File management controller for HTTP API.

This module provides the FileController class which handles file switching,
status queries, and session lifecycle management for the HTTP API.

The FileController coordinates between:
- Global state (active_file, active_session_id)
- Session manager (creating, closing sessions)
- File system (validation, permissions, locks)
"""

import os
import logging
from typing import Optional, Dict, Any
from docx_mcp_server.core.global_state import global_state
from docx_mcp_server.core.validators import validate_path_safety
from docx_mcp_server.core.session import SessionManager

logger = logging.getLogger(__name__)

# Global session manager instance (will be set by server.py)
_session_manager_instance: Optional[SessionManager] = None
_server_version: Optional[str] = None

def set_session_manager(session_manager: SessionManager, version: str):
    """Set the global session manager instance and server version.

    This should be called by server.py during initialization.
    """
    global _session_manager_instance, _server_version
    _session_manager_instance = session_manager
    _server_version = version

def _get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    if _session_manager_instance is None:
        raise RuntimeError("Session manager not initialized. Call set_session_manager() first.")
    return _session_manager_instance

def _get_version() -> str:
    """Get server version."""
    if _server_version is None:
        raise RuntimeError("Server version not initialized. Call set_session_manager() first.")
    return _server_version


class FileLockError(Exception):
    """Exception raised when a file is locked by another process."""
    pass


class UnsavedChangesError(Exception):
    """Exception raised when attempting to switch files with unsaved changes."""
    pass


class FileController:
    """Controller for file management operations.

    This class provides static methods for:
    - Switching active files (with validation and safety checks)
    - Querying server status
    - Closing sessions

    All methods coordinate with the global_state and session_manager.
    """

    @staticmethod
    def switch_file(file_path: str, force: bool = False) -> Dict[str, Any]:
        """Switch to a new active file.

        This method performs comprehensive checks before switching files:
        1. Path safety validation (prevent path traversal)
        2. File existence check
        3. File permissions check (read + write)
        4. File lock check (best effort)
        5. Unsaved changes check (unless force=True)

        Args:
            file_path: Absolute path to the .docx file
            force: If True, discard unsaved changes without prompting

        Returns:
            dict: Status dictionary with currentFile and sessionId keys

        Raises:
            ValueError: Invalid path format
            FileNotFoundError: File does not exist (HTTP 404)
            PermissionError: Insufficient permissions (HTTP 403)
            FileLockError: File is locked by another process (HTTP 423)
            UnsavedChangesError: Unsaved changes exist and force=False (HTTP 409)
        """
        logger.debug(f"switch_file() called: {file_path}, force={force}")

        # Use lazy import to avoid circular dependency
        session_manager = _get_session_manager()

        # 1. Validate path safety
        try:
            validate_path_safety(file_path)
            logger.debug("Path validation passed")
        except ValueError as e:
            logger.error(f"Path validation failed: {e}")
            raise

        # 2. Check file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
        logger.debug("File exists check passed")

        # 3. Check file permissions
        if not os.access(file_path, os.R_OK | os.W_OK):
            logger.error(f"Permission denied: {file_path}")
            raise PermissionError(f"Permission denied: {file_path}")
        logger.debug("Permission check passed")

        # 4. Check file lock (best effort)
        if FileController._is_file_locked(file_path):
            logger.error(f"File is locked: {file_path}")
            raise FileLockError(f"File is locked by another process: {file_path}")
        logger.debug("File lock check passed")

        # 5. Check unsaved changes (read current state without atomic)
        current_session_id = global_state.active_session_id
        logger.debug(f"Current session ID: {current_session_id}")

        if current_session_id:
            session = session_manager.get_session(current_session_id)
            if session and FileController._has_unsaved_changes(session):
                if not force:
                    current_file = global_state.active_file or "unknown"
                    logger.warning(f"Unsaved changes in {current_file}, force=False")
                    raise UnsavedChangesError(
                        f"Unsaved changes exist in {current_file}. "
                        f"Call with force=true to discard changes."
                    )
                logger.warning(f"Discarding unsaved changes (force=True)")

        # 6. Close active session if exists
        if current_session_id:
            logger.info(f"Closing session before file switch: {current_session_id}")
            session_manager.close_session(current_session_id)

        # 7. Set new active file (atomic write)
        global_state.active_file = file_path
        global_state.active_session_id = None
        logger.debug("Active file and session updated")

        logger.info(f"File switched to: {file_path}")
        return {
            "currentFile": file_path,
            "sessionId": None
        }

    @staticmethod
    def get_status() -> Dict[str, Any]:
        """Get current server status.

        Returns:
            dict: Status dictionary containing:
                - currentFile: Path to active file (or None)
                - sessionId: Active session ID (or None)
                - hasUnsaved: Whether active session has unsaved changes
                - serverVersion: Server version string
        """
        logger.debug("get_status() called")

        try:
            session_manager = _get_session_manager()
            logger.debug("Got session manager")

            VERSION = _get_version()
            logger.debug(f"Got version: {VERSION}")

            has_unsaved = False
            current_session_id = global_state.active_session_id
            logger.debug(f"Current session ID: {current_session_id}")

            if current_session_id:
                session = session_manager.get_session(current_session_id)
                if session:
                    has_unsaved = FileController._has_unsaved_changes(session)

            status = {
                "currentFile": global_state.active_file,
                "sessionId": current_session_id,
                "hasUnsaved": has_unsaved,
                "serverVersion": VERSION
            }

            logger.debug(f"Status query: {status}")
            return status
        except Exception as e:
            logger.exception(f"Error in get_status: {e}")
            raise

    @staticmethod
    def close_session(save: bool = False) -> Dict[str, Any]:
        """Close the active session.

        Args:
            save: If True, save the document before closing

        Returns:
            dict: Result dictionary with success status and message
        """
        logger.debug(f"close_session() called: save={save}")
        session_manager = _get_session_manager()

        current_session_id = global_state.active_session_id

        if not current_session_id:
            logger.debug("No active session to close")
            return {
                "success": True,
                "message": "No active session"
            }

        # Save if requested
        if save and global_state.active_file:
            session = session_manager.get_session(current_session_id)
            if session:
                try:
                    session.document.save(global_state.active_file)
                    logger.info(f"Saved before closing: {global_state.active_file}")
                except Exception as e:
                    logger.error(f"Failed to save before closing: {e}")
                    raise

        # Close session
        session_manager.close_session(current_session_id)
        global_state.active_session_id = None
        logger.info(f"Session closed: {current_session_id}")

        return {
            "success": True,
            "message": "Session closed successfully"
        }

    @staticmethod
    def _is_file_locked(file_path: str) -> bool:
        """Check if a file is locked (best effort).

        This method attempts to open the file in read-write mode.
        If the file cannot be opened, it is considered locked.

        Note: This is a best-effort check and may not be reliable on all platforms.

        Args:
            file_path: Path to the file to check

        Returns:
            bool: True if file appears to be locked, False otherwise
        """
        try:
            # Try to open in read-write mode
            with open(file_path, 'r+b') as f:
                pass
            return False
        except (IOError, OSError) as e:
            logger.debug(f"File lock check failed for {file_path}: {e}")
            return True

    @staticmethod
    def _has_unsaved_changes(session) -> bool:
        """Check if a session has unsaved changes.

        This method checks if the session's dirty flag is set, indicating
        that modifications have been made since the last save.

        Args:
            session: The Session object to check

        Returns:
            bool: True if session has unsaved changes, False otherwise
        """
        # Check if session has has_unsaved_changes method (new API)
        if hasattr(session, 'has_unsaved_changes'):
            return session.has_unsaved_changes()

        # Fallback: check history_stack (legacy API)
        if hasattr(session, 'history_stack'):
            return len(session.history_stack) > 0

        # Default: assume no unsaved changes
        logger.warning(f"Cannot determine unsaved changes for session {session.session_id}")
        return False
