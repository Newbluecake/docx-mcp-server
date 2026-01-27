"""Cursor navigation tools"""
import logging
from mcp.server.fastmcp import FastMCP
from docx_mcp_server.core.response import (
    create_markdown_response,
    create_error_response,
    create_context_aware_response
)
from docx_mcp_server.utils.session_helpers import get_active_session

logger = logging.getLogger(__name__)

def docx_cursor_get() -> str:
    """
    Get the current cursor position and state.

    Args:
    Returns:
        str: JSON response with cursor state containing:
            - parent_id: ID of the container
            - element_id: ID of the reference element (if any)
            - position: "before", "after", "inside_start", "inside_end"
            - description: Human readable description
            - context: Current cursor context
    """
    from docx_mcp_server.server import session_manager


    session, error = get_active_session()
    if error:
        return error
    logger.debug(f"docx_cursor_get called: session_id={session.session_id}")

    cursor = session.cursor

    # Add context
    context_text = "Context unavailable"
    try:
        context_text = session.get_cursor_context()
    except Exception as e:
        logger.warning(f"Failed to get cursor context: {e}")

    logger.debug(f"docx_cursor_get success: position={cursor.position}")
    return create_markdown_response(
            session=session,
            message="Cursor position retrieved successfully",
            operation="Operation",
            show_context=True,
        parent_id=cursor.parent_id,
        element_id=cursor.element_id,
        position=cursor.position,
        description=f"Cursor is {cursor.position} {cursor.element_id or cursor.parent_id}",
        context=context_text
    
        )

def docx_cursor_move(
    element_id: str,
    position: str = "after"
) -> str:
    """
    Move the insertion cursor to a specific location.

    Args:        element_id (str): Reference element ID (paragraph, table, etc.) or container ID.
        position (str): Relation to element.
            - "before": Place cursor before the element.
            - "after": Place cursor after the element.
            - "inside_start": Place cursor at start of container.
            - "inside_end": Place cursor at end of container.

    Returns:
        str: JSON response with success message and cursor context.
    """
    from docx_mcp_server.server import session_manager


    session, error = get_active_session()
    if error:
        return error
    logger.debug(f"docx_cursor_move called: session_id={session.session_id}, element_id={element_id}, position={position}")

    # Validate position
    if position not in ["before", "after", "inside_start", "inside_end"]:
        logger.error(f"docx_cursor_move failed: Invalid position {position}")
        return create_error_response(f"Invalid position: {position}", error_type="ValidationError")

    # Special case: selecting the document body
    if element_id == "document_body":
        if position in ["before", "after"]:
            logger.error(f"docx_cursor_move failed: Cannot place cursor before/after document body")
            return create_error_response("Cannot place cursor before/after document body", error_type="ValidationError")
        session.cursor.parent_id = "document_body"
        session.cursor.element_id = None
        session.cursor.position = position
        logger.debug(f"docx_cursor_move success: moved to {position} of document")
        return create_context_aware_response(
            session,
            message=f"Cursor moved to {position} of document",
            element_id=element_id,
            position=position
        )

    # Get object to verify it exists and determine parent
    try:

        obj = session.get_object(element_id)

    except ValueError as e:

        if "Special ID" in str(e) or "not available" in str(e):

            return create_error_response(str(e), error_type="SpecialIDNotAvailable")

        raise

    if not obj:
        logger.error(f"docx_cursor_move failed: Element {element_id} not found")
        return create_error_response(f"Element {element_id} not found", error_type="ElementNotFound")

    if position in ["inside_start", "inside_end"]:
        # Element must be a container (Body is handled above, Cell is the other main one)
        # Note: We treat Table as a block, not usually a container for cursor unless we select a cell.
        # But for now let's just allow setting cursor inside container-like things.

        # If it's a paragraph, we don't usually put cursor "inside" it for block insertion,
        # unless we support run insertion (which we do).
        # But 'add_paragraph' inside a paragraph doesn't make sense.
        # For now, we assume 'inside' implies it becomes the parent_id.
        session.cursor.parent_id = element_id
        session.cursor.element_id = None
        session.cursor.position = position
    else:
        # before/after
        # We need to find the parent of this element.
        # python-docx objects don't always expose parent easily or reliably in public API
        # but we can try to find it via session context or rely on the user knowing structure?
        # Actually, for the cursor system, we mostly care about 'where do I insert?'.
        # If I insert 'after' paragraph A, I need to know A's parent.

        # We will optimistically set the cursor.
        # The insertion tool will be responsible for resolving the parent via _parent attribute or XML.

        # Try to resolve parent_id from object if possible (optional enhancement)
        # For now, we keep the previous parent_id if we are just moving around siblings?
        # No, that's risky.
        # We will store the element_id and let insertion logic figure out the parent from the element.

        session.cursor.element_id = element_id
        session.cursor.position = position

        # Attempt to resolve parent_id to ensure context generation works
        # This is critical when moving cursor between different scopes (e.g. from cell to body)
        if hasattr(obj, "_parent"):
            parent = obj._parent
            # Check if parent is the document's body
            # python-docx Paragraph._parent is usually the Body object
            if hasattr(session.document, '_body') and parent == session.document._body:
                 session.cursor.parent_id = "document_body"
            else:
                 # It's likely a cell or other container. Try to get its ID.
                 # Using protected method _get_element_id as we are inside the server package
                 p_id = session._get_element_id(parent, auto_register=True)
                 if p_id:
                     session.cursor.parent_id = p_id

    logger.debug(f"docx_cursor_move success: {position} {element_id}")
    return create_context_aware_response(
        session,
        message=f"Cursor moved {position} {element_id}",
        element_id=element_id,
        position=position
    )



def register_tools(mcp: FastMCP):
    """Register cursor tools"""
    mcp.tool()(docx_cursor_get)
    mcp.tool()(docx_cursor_move)
