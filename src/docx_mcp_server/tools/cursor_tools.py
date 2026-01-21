"""Cursor navigation and insertion tools"""
import logging
from typing import Optional, Literal
from mcp.server.fastmcp import FastMCP
from docx.text.paragraph import Paragraph
from docx.table import Table, _Cell
from docx.oxml import OxmlElement
from docx.shared import Inches
from docx_mcp_server.core.cursor import Cursor

logger = logging.getLogger(__name__)

def docx_cursor_get(session_id: str) -> dict:
    """
    Get the current cursor position and state.

    Args:
        session_id (str): Active session ID.

    Returns:
        dict: Cursor state containing:
            - parent_id: ID of the container
            - element_id: ID of the reference element (if any)
            - position: "before", "after", "inside_start", "inside_end"
            - description: Human readable description
    """
    from docx_mcp_server.server import session_manager

    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    cursor = session.cursor

    return {
        "parent_id": cursor.parent_id,
        "element_id": cursor.element_id,
        "position": cursor.position,
        "description": f"Cursor is {cursor.position} {cursor.element_id or cursor.parent_id}"
    }

def docx_cursor_move(
    session_id: str,
    element_id: str,
    position: str = "after"
) -> str:
    """
    Move the insertion cursor to a specific location.

    Args:
        session_id (str): Active session ID.
        element_id (str): Reference element ID (paragraph, table, etc.) or container ID.
        position (str): Relation to element.
            - "before": Place cursor before the element.
            - "after": Place cursor after the element.
            - "inside_start": Place cursor at start of container.
            - "inside_end": Place cursor at end of container.

    Returns:
        str: Success message with new location description.
    """
    from docx_mcp_server.server import session_manager

    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    # Validate position
    if position not in ["before", "after", "inside_start", "inside_end"]:
        raise ValueError(f"Invalid position: {position}")

    # Special case: selecting the document body
    if element_id == "document_body":
        if position in ["before", "after"]:
            raise ValueError("Cannot place cursor before/after document body")
        session.cursor.parent_id = "document_body"
        session.cursor.element_id = None
        session.cursor.position = position
        return f"Cursor moved to {position} of document"

    # Get object to verify it exists and determine parent
    obj = session.get_object(element_id)
    if not obj:
        raise ValueError(f"Element {element_id} not found")

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
        # We don't strictly update parent_id here because finding it from element is complex
        # without searching the whole tree.
        # The insertion logic will access element._parent.

    return f"Cursor moved {position} {element_id}"


def docx_insert_paragraph_at_cursor(
    session_id: str,
    text: str,
    style: str = None
) -> str:
    """
    Insert a paragraph at the current cursor position.

    Args:
        session_id (str): Active session ID.
        text (str): Paragraph text.
        style (str, optional): Style name.

    Returns:
        str: ID of the new paragraph.
    """
    from docx_mcp_server.server import session_manager

    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    cursor = session.cursor

    # 1. Determine Parent and Reference Element
    parent = None
    ref_element = None

    if cursor.element_id:
        ref_obj = session.get_object(cursor.element_id)
        if not ref_obj:
            raise ValueError(f"Reference element {cursor.element_id} no longer exists")

        if cursor.position in ["before", "after"]:
            # Parent is the parent of the reference object
            # Access internal _parent
            if hasattr(ref_obj, "_parent"):
                parent = ref_obj._parent
            else:
                # Fallback: assume document body if we can't find parent
                # This might fail for nested tables
                parent = session.document
            ref_element = ref_obj
        else:
            # "inside" -> ref_obj IS the parent
            parent = ref_obj
            ref_element = None
    else:
        # No reference element, use parent_id
        if cursor.parent_id == "document_body":
            parent = session.document
        else:
            parent = session.get_object(cursor.parent_id)
            if not parent:
                raise ValueError(f"Parent {cursor.parent_id} not found")

    # 2. Create the new paragraph
    # We always use parent.add_paragraph() first to ensure proper creation
    try:
        new_para = parent.add_paragraph(text, style)
    except AttributeError:
         raise ValueError(f"Target container ({type(parent).__name__}) does not support adding paragraphs")

    # 3. Move it if necessary
    if cursor.position == "inside_end":
        # Already at end
        pass

    elif cursor.position == "inside_start":
        # Move to beginning of parent
        # parent._element is the container (e.g. w:body, w:tc)
        # We want to insert new_para._element at index 0
        parent_element = parent._element
        if len(parent_element) > 1: # >1 because we just added one
             # Remove from end
             parent_element.remove(new_para._element)
             # Insert at 0
             parent_element.insert(0, new_para._element)

    elif cursor.position == "before" and ref_element:
        # Move before ref_element
        new_para._element.getparent().remove(new_para._element)
        ref_element._element.addprevious(new_para._element)

    elif cursor.position == "after" and ref_element:
        # Move after ref_element
        new_para._element.getparent().remove(new_para._element)
        ref_element._element.addnext(new_para._element)

    return session.register_object(new_para, "para")


def docx_insert_table_at_cursor(
    session_id: str,
    rows: int,
    cols: int
) -> str:
    """
    Insert a table at the current cursor position.

    Args:
        session_id (str): Active session ID.
        rows (int): Number of rows.
        cols (int): Number of columns.

    Returns:
        str: ID of the new table.
    """
    from docx_mcp_server.server import session_manager

    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    cursor = session.cursor

    # Logic similar to insert_paragraph
    parent = None
    ref_element = None

    if cursor.element_id:
        ref_obj = session.get_object(cursor.element_id)
        if not ref_obj:
            raise ValueError(f"Reference element {cursor.element_id} no longer exists")

        if cursor.position in ["before", "after"]:
            if hasattr(ref_obj, "_parent"):
                parent = ref_obj._parent
            else:
                parent = session.document
            ref_element = ref_obj
        else:
            parent = ref_obj
            ref_element = None
    else:
        if cursor.parent_id == "document_body":
            parent = session.document
        else:
            parent = session.get_object(cursor.parent_id)

    # Create table
    try:
        new_table = parent.add_table(rows, cols)
    except TypeError as e:
        if "width" in str(e):
             # BlockItemContainer (like Body) requires width
             new_table = parent.add_table(rows, cols, Inches(6.0))
        else:
            raise e
    except AttributeError:
         raise ValueError(f"Target container ({type(parent).__name__}) does not support adding tables")

    # Move it
    if cursor.position == "inside_start":
        parent_element = parent._element
        if len(parent_element) > 1:
             parent_element.remove(new_table._element)
             parent_element.insert(0, new_table._element)

    elif cursor.position == "before" and ref_element:
        new_table._element.getparent().remove(new_table._element)
        ref_element._element.addprevious(new_table._element)

    elif cursor.position == "after" and ref_element:
        new_table._element.getparent().remove(new_table._element)
        ref_element._element.addnext(new_table._element)

    return session.register_object(new_table, "table")

def register_tools(mcp: FastMCP):
    """Register cursor tools"""
    mcp.tool()(docx_cursor_get)
    mcp.tool()(docx_cursor_move)
    mcp.tool()(docx_insert_paragraph_at_cursor)
    mcp.tool()(docx_insert_table_at_cursor)
