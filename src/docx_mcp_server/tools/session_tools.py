"""Session management tools"""
import json
import logging
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


def docx_create(file_path: str = None, auto_save: bool = False) -> str:
    """
    Create a new Word document session or load an existing document.

    This is the entry point for all document operations. Creates an isolated session
    with a unique session_id that maintains document state and object registry.

    Typical Use Cases:
        - Create a new blank document for content generation
        - Load an existing template for modification
        - Enable auto-save for real-time document updates

    Args:
        file_path (str, optional): Path to an existing .docx file to load.
            If None, creates a new blank document. Use relative paths (e.g., "./doc.docx")
            for cross-platform compatibility. Absolute paths must match the server's OS.
        auto_save (bool, optional): Enable automatic saving after each modification.
            Requires file_path to be set. Defaults to False.

    Returns:
        str: Unique session_id (UUID format) for subsequent operations.

    Raises:
        FileNotFoundError: If file_path is specified but file does not exist.
        ValueError: If auto_save is True but file_path is None.

    Examples:
        Create a new blank document:
        >>> session_id = docx_create()
        >>> print(session_id)
        'abc-123-def-456'

        Load an existing document:
        >>> session_id = docx_create(file_path="./template.docx")

        Enable auto-save mode:
        >>> session_id = docx_create(file_path="./output.docx", auto_save=True)

    Notes:
        - Each session is independent and isolated from others
        - Sessions auto-expire after 1 hour of inactivity
        - Always call docx_close() when done to free resources

    See Also:
        - docx_save: Save document to disk
        - docx_close: Close session and free resources
    """
    from docx_mcp_server.server import session_manager

    logger.info(f"docx_create called: file_path={file_path}, auto_save={auto_save}")
    try:
        session_id = session_manager.create_session(file_path, auto_save=auto_save)
        logger.info(f"docx_create success: session_id={session_id}")
        return session_id
    except Exception as e:
        logger.exception(f"docx_create failed: {e}")
        raise

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
        str: Success message confirming session closure.

    Examples:
        Complete document workflow:
        >>> session_id = docx_create()
        >>> para_id = docx_add_paragraph(session_id, "Content")
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
        return f"Session {session_id} closed successfully"
    else:
        logger.warning(f"docx_close: Session {session_id} not found")
        return f"Session {session_id} not found"

def docx_save(session_id: str, file_path: str) -> str:
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
        str: Success message with the saved file path.

    Raises:
        ValueError: If session_id is invalid or session has expired.
        RuntimeError: If file cannot be saved (permission denied, disk full, etc.).
        FileNotFoundError: If parent directory does not exist.

    Examples:
        Save a new document:
        >>> session_id = docx_create()
        >>> para_id = docx_add_paragraph(session_id, "Hello World")
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

    logger.info(f"docx_save called: session_id={session_id}, file_path={file_path}")
    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"docx_save failed: Session {session_id} not found")
        raise ValueError(f"Session {session_id} not found or expired")

    # Security check: Ensure we are writing to an allowed location if needed.
    # For now, we assume the user (Claude) acts with the user's permissions.

    # LIVE PREVIEW: Prepare for save (release locks if file is open in Word)
    try:
        session.preview_controller.prepare_for_save(file_path)
    except Exception as e:
        # Log but don't block save
        logger.warning(f"Preview prepare failed: {e}")

    try:
        session.document.save(file_path)
        logger.info(f"docx_save success: {file_path}")
    except Exception as e:
        logger.exception(f"docx_save failed: {e}")
        raise RuntimeError(f"Failed to save document: {str(e)}")

    # LIVE PREVIEW: Refresh (reload file in Word)
    try:
        session.preview_controller.refresh(file_path)
    except Exception as e:
         logger.warning(f"Preview refresh failed: {e}")

    return f"Document saved successfully to {file_path}"

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
        str: JSON string with session context information:
            {
                "session_id": "...",
                "last_created_id": "para_xxx",
                "last_accessed_id": "table_xxx",
                "file_path": "./doc.docx",
                "auto_save": false
            }

    Raises:
        ValueError: If session_id is invalid or session has expired.

    Examples:
        Check session context:
        >>> session_id = docx_create(file_path="./report.docx")
        >>> para_id = docx_add_paragraph(session_id, "Text")
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
        raise ValueError(f"Session {session_id} not found")

    info = {
        "session_id": session.session_id,
        "last_created_id": session.last_created_id,
        "last_accessed_id": session.last_accessed_id,
        "file_path": session.file_path,
        "auto_save": session.auto_save
    }
    return json.dumps(info, indent=2)


def register_tools(mcp: FastMCP):
    """Register session management tools"""
    mcp.tool()(docx_create)
    mcp.tool()(docx_close)
    mcp.tool()(docx_save)
    mcp.tool()(docx_get_context)