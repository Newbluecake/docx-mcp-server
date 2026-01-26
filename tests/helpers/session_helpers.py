"""Session management helpers for testing."""

from docx_mcp_server.tools.session_tools import docx_create
from docx_mcp_server.core.global_state import global_state


def create_session_with_file(file_path: str, **kwargs) -> str:
    """
    Create a session with a specific file (for testing Breaking Change v3.0).

    In v3.0, docx_create() no longer accepts file_path parameter.
    This helper sets global_state.active_file then calls docx_create().

    Args:
        file_path: Path to the file to load
        **kwargs: Additional arguments to pass to docx_create()

    Returns:
        str: Markdown response from docx_create()

    Example:
        >>> response = create_session_with_file("/path/to/file.docx")
        >>> session_id = extract_session_id(response)
    """
    # Set global active file
    global_state.active_file = file_path

    # Create session (will use global_state.active_file)
    return docx_create(**kwargs)


def clear_active_file():
    """Clear the global active file (useful for test cleanup)."""
    global_state.active_file = None
