"""Text run (formatting) tools"""
import logging
from mcp.server.fastmcp import FastMCP
from docx.shared import Pt, RGBColor
from docx_mcp_server.core.response import (
    create_markdown_response,
    create_error_response
)
from docx_mcp_server.services.navigation import PositionResolver
from docx_mcp_server.core.xml_util import ElementManipulator

logger = logging.getLogger(__name__)


def docx_insert_run(session_id: str, text: str, position: str) -> str:
    """
    Add a text run to a paragraph with independent formatting.

    Runs are the atomic text units within paragraphs. Each run can have its own
    formatting (bold, italic, color, size) independent of other runs in the paragraph.

    Typical Use Cases:
        - Add formatted text within a paragraph
        - Mix different text styles in one paragraph
        - Build complex formatted content incrementally

    Args:
        session_id (str): Active session ID returned by docx_create().
        text (str): Text content for the run.
        position (str): Insertion position string.
            Format: "mode:target_id". Modes: after, before, inside, start, end.
            Example: "inside:para_123" (insert run into paragraph).

    Returns:
        str: JSON response with element_id and cursor context.

    Raises:
        ValueError: If session_id is invalid.
        ValueError: If position is invalid or target element not found.
        ValueError: If target element cannot contain runs.

    Examples:
        Add run to specific paragraph:
        >>> session_id = docx_create()
        >>> para_id = docx_insert_paragraph(session_id, "", position="end:document_body")
        >>> run_id = docx_insert_run(session_id, "Hello ", position=f"inside:{para_id}")
        >>> run_id2 = docx_insert_run(session_id, "World", position=f"inside:{para_id}")

        Insert into a paragraph by position:
        >>> para_id = docx_insert_paragraph(session_id, "", position="end:document_body")
        >>> run_id = docx_insert_run(session_id, "Explicit insert", position=f"inside:{para_id}")

        Build formatted paragraph:
        >>> para_id = docx_insert_paragraph(session_id, "", position="end:document_body")
        >>> run1 = docx_insert_run(session_id, "Normal ", position=f"inside:{para_id}")
        >>> run2 = docx_insert_run(session_id, "Bold", position=f"inside:{para_id}")
        >>> docx_set_font(session_id, run2, bold=True)

    Notes:
        - Runs are inserted relative to paragraph/run targets.
        - Use docx_set_font() to apply formatting after creation

    See Also:
        - docx_insert_paragraph: Create parent paragraph
        - docx_set_font: Format the run
        - docx_update_run_text: Modify existing run
    """
    from docx_mcp_server.server import session_manager

    logger.debug(f"docx_insert_run called: session_id={session_id}, text_len={len(text)}, position={position}")

    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"docx_insert_run failed: Session {session_id} not found")
        return create_error_response(f"Session {session_id} not found", error_type="SessionNotFound")

    try:
        resolver = PositionResolver(session)
        target_parent, ref_element, mode = resolver.resolve(position, default_parent=session.document)
    except ValueError as e:
        return create_error_response(str(e), error_type="ValidationError")

    if not hasattr(target_parent, 'add_run'):
        logger.error(f"docx_insert_run failed: Object {type(target_parent).__name__} cannot contain runs")
        return create_error_response(f"Object {type(target_parent).__name__} cannot contain runs", error_type="InvalidElementType")

    try:
        run = target_parent.add_run(text)

        if mode != "append":
            if mode == "before" and ref_element:
                ElementManipulator.insert_xml_before(ref_element._element, run._element)
            elif mode == "after" and ref_element:
                ElementManipulator.insert_xml_after(ref_element._element, run._element)
            elif mode == "start":
                ElementManipulator.insert_at_index(target_parent._element, run._element, 0)
        r_id = session.register_object(run, "run")

        # Update context: this is a creation action
        session.update_context(r_id, action="create")

        # Update cursor to point after the new run
        session.cursor.element_id = r_id
        # parent may be paragraph
        if hasattr(target_parent, '_element'):
            session.cursor.parent_id = session._get_element_id(target_parent, auto_register=True)
        session.cursor.position = "after"

        logger.debug(f"docx_insert_run success: {r_id}")
        return create_markdown_response(
            session=session,
            message="Run added successfully",
            operation="Operation",
            show_context=True,
            element_id=r_id
        
        )
    except Exception as e:
        logger.exception(f"docx_insert_run failed: {e}")
        return create_error_response(f"Failed to add run: {str(e)}", error_type="CreationError")

def docx_update_run_text(session_id: str, run_id: str, new_text: str) -> str:
    """
    Update the text content of an existing run while preserving formatting.

    Replaces the text in a run without affecting its formatting properties
    (bold, italic, color, size, etc.). Useful for updating content while maintaining style.

    Typical Use Cases:
        - Update formatted text without losing styling
        - Replace placeholders in styled content
        - Modify specific text portions in a paragraph

    Args:
        session_id (str): Active session ID returned by docx_create().
        run_id (str): ID of the run to update.
        new_text (str): New text content to replace existing text.

    Returns:
        str: JSON response with success message and cursor context.

    Raises:
        ValueError: If session_id or run_id is invalid.
        ValueError: If specified object is not a run.

    Examples:
        Update run text:
        >>> session_id = docx_create()
        >>> para_id = docx_insert_paragraph(session_id, "", position="end:document_body")
        >>> run_id = docx_insert_run(session_id, "Old", position=f"inside:{para_id}")
        >>> docx_set_font(session_id, run_id, bold=True, size=14)
        >>> result = docx_update_run_text(session_id, run_id, "New")
        >>> print(result)
        'Run run_xxx updated successfully'

    Notes:
        - Preserves all formatting: bold, italic, size, color, etc.
        - Only the text content is changed
        - More precise than docx_update_paragraph_text()

    See Also:
        - docx_update_paragraph_text: Replace entire paragraph content
        - docx_set_font: Modify run formatting
    """
    from docx_mcp_server.server import session_manager

    logger.debug(f"docx_update_run_text called: session_id={session_id}, run_id={run_id}, new_text_len={len(new_text)}")

    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"docx_update_run_text failed: Session {session_id} not found")
        return create_error_response(f"Session {session_id} not found", error_type="SessionNotFound")

    run = session.get_object(run_id)
    if not run:
        logger.error(f"docx_update_run_text failed: Run {run_id} not found")
        return create_error_response(f"Run {run_id} not found", error_type="ElementNotFound")

    if not hasattr(run, 'text'):
        logger.error(f"docx_update_run_text failed: Object {run_id} is not a run")
        return create_error_response(f"Object {run_id} is not a run", error_type="InvalidElementType")

    try:
        # Capture old content for diff
        old_text = run.text

        # Update text while preserving formatting
        run.text = new_text

        # Update cursor
        session.cursor.element_id = run_id
        session.cursor.position = "after"

        logger.debug(f"docx_update_run_text success: {run_id}")
        return create_markdown_response(
            session=session,
            message="Run text updated successfully",
            element_id=run_id,
            operation="Update Run Text",
            show_context=True,
            show_diff=True,
            old_content=old_text,
            new_content=new_text,
            changed_fields=["text"]
        )
    except Exception as e:
        logger.exception(f"docx_update_run_text failed: {e}")
        return create_error_response(f"Failed to update run text: {str(e)}", error_type="UpdateError")

def docx_set_font(
    session_id: str,
    run_id: str,
    size: float = None,
    bold: bool = None,
    italic: bool = None,
    color_hex: str = None
) -> str:
    """
    Set font properties for a specific text run.

    Applies formatting to a run, allowing fine-grained control over text appearance.
    Multiple properties can be set in a single call.

    Typical Use Cases:
        - Format important text (bold, larger size)
        - Apply color coding to text
        - Create styled headings and emphasis

    Args:
        session_id (str): Active session ID returned by docx_create().
        run_id (str): ID of the text run to format.
        size (float, optional): Font size in points (e.g., 12.0, 14.5).
        bold (bool, optional): True to make bold, False to remove bold.
        italic (bool, optional): True to make italic, False to remove italic.
        color_hex (str, optional): Hex color code without '#' (e.g., "FF0000" for red,
            "0000FF" for blue). Must be 6 characters (RRGGBB format).

    Returns:
        str: JSON response with success message and cursor context.

    Raises:
        ValueError: If session_id or run_id is invalid.
        ValueError: If color_hex is not valid 6-character hex string.

    Examples:
        Basic formatting:
        >>> session_id = docx_create()
        >>> para_id = docx_insert_paragraph(session_id, "", position="end:document_body")
        >>> run_id = docx_insert_run(session_id, "Important", position=f"inside:{para_id}")
        >>> docx_set_font(session_id, run_id, size=14, bold=True)

        Apply color:
        >>> run_id = docx_insert_run(session_id, "Red text", position=f"inside:{para_id}")
        >>> docx_set_font(session_id, run_id, color_hex="FF0000")

        Multiple properties:
        >>> run_id = docx_insert_run(session_id, "Styled", position=f"inside:{para_id}")
        >>> docx_set_font(session_id, run_id, size=16, bold=True, italic=True, color_hex="0000FF")

    Notes:
        - Size is in points (1 point = 1/72 inch)
        - Color format is RRGGBB without '#' prefix
        - Omitted parameters are not changed
        - Setting bold/italic to False explicitly removes the formatting

    See Also:
        - docx_insert_run: Create run to format
        - docx_set_properties: Advanced formatting options
    """
    from docx_mcp_server.server import session_manager

    logger.debug(f"docx_set_font called: session_id={session_id}, run_id={run_id}, size={size}, bold={bold}, italic={italic}, color_hex={color_hex}")

    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"docx_set_font failed: Session {session_id} not found")
        return create_error_response(f"Session {session_id} not found", error_type="SessionNotFound")

    run = session.get_object(run_id)
    if not run:
        logger.error(f"docx_set_font failed: Run {run_id} not found")
        return create_error_response(f"Run {run_id} not found", error_type="ElementNotFound")

    try:
        font = run.font
        changed = []
        if size is not None:
            font.size = Pt(size)
            changed.append("size")
        if bold is not None:
            font.bold = bold
            changed.append("bold")
        if italic is not None:
            font.italic = italic
            changed.append("italic")
        if color_hex:
            # Parse hex string "RRGGBB"
            try:
                r = int(color_hex[0:2], 16)
                g = int(color_hex[2:4], 16)
                b = int(color_hex[4:6], 16)
                font.color.rgb = RGBColor(r, g, b)
                changed.append("color")
            except ValueError:
                logger.error(f"docx_set_font failed: Invalid hex color {color_hex}")
                return create_error_response(f"Invalid hex color: {color_hex}", error_type="ValidationError")

        # Update cursor to point to this run
        session.cursor.element_id = run_id
        session.cursor.position = "after"

        logger.debug(f"docx_set_font success: {run_id}")
        return create_markdown_response(
            session=session,
            message="Font updated successfully",
            operation="Operation",
            show_context=True,
            element_id=run_id,
            changed_properties=changed,
            bold=font.bold,
            italic=font.italic,
            size=font.size.pt if font.size else None,
            color_hex=color_hex if color_hex else None,
            color=color_hex if color_hex else None
        )
    except Exception as e:
        logger.exception(f"docx_set_font failed: {e}")
        return create_error_response(f"Failed to update font: {str(e)}", error_type="UpdateError")


def register_tools(mcp: FastMCP):
    """Register text run (formatting) tools"""
    mcp.tool()(docx_insert_run)
    mcp.tool()(docx_update_run_text)
    mcp.tool()(docx_set_font)
