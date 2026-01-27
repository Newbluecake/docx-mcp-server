"""Session management helpers for testing.

This module provides helper functions for setting up and tearing down
test sessions in the v4.0 architecture where sessions are managed globally.
"""

from typing import Optional
from docx_mcp_server.server import session_manager
from docx_mcp_server.core.global_state import global_state


def setup_active_session(file_path: Optional[str] = None) -> str:
    """Setup a global active session for testing.

    Creates a session and sets it as the active session in global_state.
    This replaces the need to call docx_create() in tests.

    Args:
        file_path: Optional file path to load. If None, creates an empty document.

    Returns:
        str: Created session_id

    Example:
        >>> def test_something():
        ...     session_id = setup_active_session()
        ...     # Test code here
        ...     teardown_active_session()
    """
    session_id = session_manager.create_session(file_path)
    global_state.active_session_id = session_id
    if file_path:
        global_state.active_file = file_path
    return session_id


def teardown_active_session():
    """Teardown the global active session.

    Closes the active session and clears global_state.
    Should be called in test cleanup to prevent state leakage.

    Example:
        >>> def test_something():
        ...     setup_active_session()
        ...     # Test code here
        ...     teardown_active_session()
    """
    if global_state.active_session_id:
        session_manager.close_session(global_state.active_session_id)
    global_state.clear()


def create_session_with_file(file_path: str, **kwargs) -> str:
    """Create a session with a specific file (legacy compatibility).

    This function is kept for backward compatibility with existing tests.
    New tests should use setup_active_session() instead.

    Args:
        file_path: Path to the file to load
        **kwargs: Additional arguments (auto_save, backup_on_save, etc.)

    Returns:
        str: Created session_id

    Example:
        >>> session_id = create_session_with_file("/path/to/file.docx")
    """
    session_id = session_manager.create_session(
        file_path=file_path,
        auto_save=kwargs.get('auto_save', False),
        backup_on_save=kwargs.get('backup_on_save', False),
        backup_dir=kwargs.get('backup_dir'),
        backup_suffix=kwargs.get('backup_suffix')
    )
    global_state.active_session_id = session_id
    global_state.active_file = file_path
    return session_id


def clear_active_file():
    """Clear the global active file (useful for test cleanup).

    This is a legacy function kept for compatibility.
    New tests should use teardown_active_session() instead.
    """
    global_state.active_file = None
    global_state.active_session_id = None
