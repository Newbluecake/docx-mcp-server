"""Session management tools"""
import json
import logging
from typing import Optional
from mcp.server.fastmcp import FastMCP
from docx_mcp_server.core.response import create_markdown_response, create_error_response

logger = logging.getLogger(__name__)


def docx_create(
    auto_save: bool = False,
    backup_on_save: bool = False,
    backup_dir: str = "",
    backup_suffix: str = ""
) -> str:
    """
    Create a new Word document session using the global active file.

    This is the entry point for all document operations. Creates an isolated session
    with a unique session_id that maintains document state and object registry.

    **Breaking Change (v3.0)**: The file_path parameter has been removed. Files are now
    managed centrally by the Launcher via HTTP API (/api/file/switch). Use the Launcher
    to select files, or run the server with --file parameter to set initial active file.

    Typical Use Cases:
        - Create a session for the current active file (set by Launcher)
        - Enable auto-save for real-time document updates

    Args:
        auto_save (bool, optional): Enable automatic saving after each modification.
            Requires active_file to be set. Defaults to False.

    Returns:
        str: Markdown-formatted response with session_id.

    Raises:
        FileNotFoundError: If active_file is set but file does not exist.
        ValueError: If auto_save is True but active_file is None.

    Examples:
        Create a session for the active file:
        >>> session_id = docx_create()
        >>> print(session_id)
        'abc-123-def-456'

        Enable auto-save mode:
        >>> session_id = docx_create(auto_save=True)

    Notes:
        - File selection is now handled by the Launcher GUI or --file CLI parameter
        - Each session is independent and isolated from others
        - Sessions auto-expire after 1 hour of inactivity
        - Always call docx_close() when done to free resources

    Migration from v2.x:
        Old (v2.x):
        >>> session_id = docx_create(file_path="./template.docx")

        New (v3.0):
        1. Use Launcher to select file (calls /api/file/switch)
        2. Then create session:
        >>> session_id = docx_create()

    See Also:
        - docx_save: Save document to disk
        - docx_close: Close session and free resources
        - /api/file/switch: HTTP API to switch active file (called by Launcher)
    """
    from docx_mcp_server.server import session_manager
    from docx_mcp_server.core.global_state import global_state

    # Get active file from global state
    file_path = global_state.active_file

    logger.info(
        f"docx_create called: active_file={file_path}, auto_save={auto_save}, "
        f"backup_on_save={backup_on_save}, backup_dir={backup_dir}, backup_suffix={backup_suffix}"
    )
    try:
        session_id = session_manager.create_session(
            file_path or None,
            auto_save=auto_save,
            backup_on_save=backup_on_save,
            backup_dir=backup_dir or None,
            backup_suffix=backup_suffix or None,
        )
        logger.info(f"docx_create success: session_id={session_id}")

        return create_markdown_response(
            session=None,
            message=f"Session created successfully: {session_id}",
            element_id=None,
            operation="Create Session",
            show_context=False,
            session_id=session_id,
            file_path=file_path or "New blank document",
            auto_save=auto_save
        )
    except Exception as e:
        logger.exception(f"docx_create failed: {e}")
        return create_error_response(
            message=f"Failed to create session: {str(e)}",
            error_type="CreationError"
        )

def docx_close(session_id: str) -> str:
    """
    Close the session and free all associated resources.

    Terminates the document session, releasing memory and clearing the object registry.
    Should be called when document operations are complete to prevent resource leaks.

    Typical Use Cases:
        - Clean up after document generation is complete
        - Free resources in long-running processes
        - Ensure proper session lifecycle management

    Args:
        session_id (str): Active session ID to close.

    Returns:
        str: Markdown-formatted success message confirming session closure.

    Examples:
        Complete document workflow:
        >>> session_id = docx_create()
        >>> para_id = docx_insert_paragraph(session_id, "Content", position="end:document_body")
        >>> docx_save(session_id, "./output.docx")
        >>> result = docx_close(session_id)
        >>> print(result)
        'Session abc-123 closed successfully'

    Notes:
        - Unsaved changes will be lost - always call docx_save() first
        - Closed sessions cannot be reopened - create a new session instead
        - Sessions auto-expire after 1 hour, but explicit closure is recommended
        - Calling close on an already closed session returns a not-found message

    See Also:
        - docx_create: Create a new session
        - docx_save: Save before closing
    """
    from docx_mcp_server.server import session_manager

    logger.info(f"docx_close called: session_id={session_id}")
    success = session_manager.close_session(session_id)
    if success:
        return create_markdown_response(
            session=None,
            message=f"Session {session_id} closed successfully",
            operation="Close Session",
            show_context=False,
            session_id=session_id
        )
    else:
        logger.warning(f"docx_close: Session {session_id} not found")
        return create_error_response(
            message=f"Session {session_id} not found",
            error_type="SessionNotFound"
        )

def docx_save(
    session_id: str,
    file_path: str,
    backup: bool = False,
    backup_dir: str = "",
    backup_suffix: str = "",
) -> str:
    """
    Save the document to disk at the specified path.

    Persists all modifications made during the session to a .docx file.
    Supports saving to a new location or overwriting the original file.

    Typical Use Cases:
        - Save generated document to output location
        - Create a modified copy of a template
        - Checkpoint document state during long operations

    Args:
        session_id (str): Active session ID returned by docx_create().
        file_path (str): Absolute or relative path where the file should be saved.
            Parent directory must exist. Use relative paths for portability.

    Returns:
        str: Markdown-formatted success message with the saved file path.

    Raises:
        ValueError: If session_id is invalid or session has expired.
        RuntimeError: If file cannot be saved (permission denied, disk full, etc.).
        FileNotFoundError: If parent directory does not exist.

    Examples:
        Save a new document:
        >>> session_id = docx_create()
        >>> para_id = docx_insert_paragraph(session_id, "Hello World", position="end:document_body")
        >>> result = docx_save(session_id, "./output.docx")
        >>> print(result)
        'Document saved successfully to ./output.docx'

        Save modified template:
        >>> session_id = docx_create(file_path="./template.docx")
        >>> # ... make modifications ...
        >>> docx_save(session_id, "./filled_template.docx")

    Notes:
        - If file exists, it will be overwritten without warning
        - In auto_save mode, this is called automatically after each modification
        - Live preview feature will refresh Word if file is open

    See Also:
        - docx_create: Create session with auto_save option
        - docx_close: Close session after saving
    """
    from docx_mcp_server.server import session_manager

    logger.info(
        f"docx_save called: session_id={session_id}, file_path={file_path}, "
        f"backup={backup}, backup_dir={backup_dir}, backup_suffix={backup_suffix}"
    )
    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"docx_save failed: Session {session_id} not found")
        return create_error_response(
            message=f"Session {session_id} not found or expired",
            error_type="SessionNotFound"
        )

    # Security check: Ensure we are writing to an allowed location if needed.
    # For now, we assume the user (Claude) acts with the user's permissions.

    # LIVE PREVIEW: Prepare for save (release locks if file is open in Word)
    try:
        session.preview_controller.prepare_for_save(file_path)
    except Exception as e:
        # Log but don't block save
        logger.warning(f"Preview prepare failed: {e}")

    try:
        backup_path = session._save_with_optional_backup(
            file_path,
            backup=backup,
            backup_dir=backup_dir or None,
            backup_suffix=backup_suffix or None,
        )
        logger.info(f"docx_save success: {file_path}, backup={backup_path}")
    except Exception as e:
        logger.exception(f"docx_save failed: {e}")
        return create_error_response(
            message=f"Failed to save document: {str(e)}",
            error_type="SaveError"
        )

    # LIVE PREVIEW: Refresh (reload file in Word)
    try:
        session.preview_controller.refresh(file_path)
    except Exception as e:
         logger.warning(f"Preview refresh failed: {e}")

    # T-003: Mark session as saved (clear dirty flag)
    session.mark_saved()

    return create_markdown_response(
        session=None,
        message=f"Document saved successfully to {file_path}",
        operation="Save Document",
        show_context=False,
        file_path=file_path,
        backup_path=backup_path,
        backup=backup
    )

def docx_get_context(session_id: str) -> str:
    """
    Get the current context state of the session.

    Returns information about the session's current state, including the last created
    and accessed elements, file path, and auto-save status.

    Typical Use Cases:
        - Debug session state
        - Verify current context before operations
        - Check session configuration

    Args:
        session_id (str): Active session ID returned by docx_create().

    Returns:
        str: Markdown-formatted session context information.

    Raises:
        ValueError: If session_id is invalid or session has expired.

    Examples:
        Check session context:
        >>> session_id = docx_create(file_path="./report.docx")
        >>> para_id = docx_insert_paragraph(session_id, "Text", position="end:document_body")
        >>> context = docx_get_context(session_id)
        >>> import json
        >>> data = json.loads(context)
        >>> print(f"Last created: {data['last_created_id']}")

    Notes:
        - Useful for debugging implicit context operations
        - Shows which element will be used for context-based operations
        - Auto-save status indicates if changes are automatically persisted

    See Also:
        - docx_create: Create session with configuration
    """
    from docx_mcp_server.server import session_manager

    session = session_manager.get_session(session_id)
    if not session:
        return create_error_response(
            message=f"Session {session_id} not found",
            error_type="SessionNotFound"
        )

    return create_markdown_response(
        session=None,
        message="Session context retrieved successfully",
        operation="Get Context",
        show_context=False,
        session_id=session.session_id,
        last_created_id=session.last_created_id or "None",
        last_accessed_id=session.last_accessed_id or "None",
        file_path=session.file_path or "None",
        auto_save=session.auto_save,
        backup_on_save=session.backup_on_save
    )


def docx_list_sessions() -> str:
    """
    List all active sessions with their metadata.

    Returns information about all currently active document editing sessions,
    including session IDs, file paths, and configuration settings.

    **No Session Required**: This tool operates at the server level and does
    not need a session_id. Use it to inspect active sessions for debugging
    or monitoring purposes.

    Typical Use Cases:
        - Debug session state and identify active sessions
        - Monitor server resource usage
        - Verify session creation before operations
        - Check which files are currently being edited

    Returns:
        str: Markdown-formatted response containing:
            - **Active Sessions**: Count of active sessions
            - **Sessions**: JSON array with session details (id, file_path, auto_save, etc.)

    Examples:
        List all active sessions:
        >>> result = docx_list_sessions()
        >>> # Response includes session count and details

        Check if specific session exists:
        >>> result = docx_list_sessions()
        >>> import json, re
        >>> match = re.search(r'\*\*Sessions\*\*:\s*```json\n(.+?)\n```', result, re.DOTALL)
        >>> if match:
        ...     sessions = json.loads(match.group(1))
        ...     session_ids = [s['session_id'] for s in sessions]
        ...     print(f"Active sessions: {session_ids}")

    Notes:
        - Sessions auto-expire after 1 hour of inactivity
        - Each session maintains independent document state
        - Use docx_cleanup_sessions() to manually remove expired sessions

    See Also:
        - docx_create: Create a new session
        - docx_cleanup_sessions: Remove expired sessions
        - docx_get_context: Get detailed context for a specific session
    """
    from docx_mcp_server.server import session_manager

    sessions = session_manager.list_sessions()
    return create_markdown_response(
        session=None,
        message=f"Active sessions: {len(sessions)}",
        operation="List Sessions",
        show_context=False,
        active_sessions=len(sessions),
        sessions=json.dumps(sessions, indent=2)
    )


def docx_cleanup_sessions(max_idle_seconds: int = 0) -> str:
    """
    Clean up expired or idle sessions to free server resources.

    Removes sessions that have exceeded their idle timeout, releasing memory
    and clearing object registries. Can be called manually or runs automatically
    via the session manager's cleanup mechanism.

    **No Session Required**: This tool operates at the server level and does
    not need a session_id. Use it for server maintenance and resource management.

    Typical Use Cases:
        - Free memory after batch document processing
        - Clean up abandoned sessions in long-running servers
        - Force cleanup before server shutdown
        - Implement custom session timeout policies

    Args:
        max_idle_seconds (int, optional): Maximum idle time in seconds before
            a session is considered expired. If 0 or not provided, uses the
            default TTL (3600 seconds = 1 hour). Defaults to 0.

    Returns:
        str: Markdown-formatted response containing:
            - **Cleaned**: Number of sessions removed
            - **Max Idle Seconds**: Timeout threshold used

    Examples:
        Clean up with default timeout (1 hour):
        >>> result = docx_cleanup_sessions()
        >>> # Removes sessions idle for more than 1 hour

        Clean up with custom timeout (5 minutes):
        >>> result = docx_cleanup_sessions(max_idle_seconds=300)
        >>> # Removes sessions idle for more than 5 minutes

        Extract cleanup count:
        >>> result = docx_cleanup_sessions()
        >>> import re
        >>> match = re.search(r'\*\*Cleaned\*\*:\s*(\d+)', result)
        >>> count = int(match.group(1)) if match else 0
        >>> print(f"Cleaned up {count} sessions")

    Notes:
        - Closed sessions cannot be recovered - ensure work is saved first
        - Active sessions (recently accessed) are never cleaned up
        - Automatic cleanup runs periodically in the background
        - Use docx_list_sessions() to check active sessions before cleanup

    See Also:
        - docx_list_sessions: View active sessions before cleanup
        - docx_close: Explicitly close a specific session
        - docx_save: Save session before cleanup
    """
    from docx_mcp_server.server import session_manager

    cleaned = session_manager.cleanup_expired(max_idle_seconds=max_idle_seconds or None)
    return create_markdown_response(
        session=None,
        message=f"Cleaned up {cleaned} expired sessions",
        operation="Cleanup Sessions",
        show_context=False,
        cleaned=cleaned,
        max_idle_seconds=max_idle_seconds
    )


def register_tools(mcp: FastMCP):
    """Register session management tools"""
    mcp.tool()(docx_create)
    mcp.tool()(docx_close)
    mcp.tool()(docx_save)
    mcp.tool()(docx_get_context)
    mcp.tool()(docx_list_sessions)
    mcp.tool()(docx_cleanup_sessions)
