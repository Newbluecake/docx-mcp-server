"""Text run (formatting) tools"""
import logging
from mcp.server.fastmcp import FastMCP
from docx.shared import Pt, RGBColor

logger = logging.getLogger(__name__)


def docx_add_run(session_id: str, text: str, paragraph_id: str = None) -> str:
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
        paragraph_id (str, optional): ID of the parent paragraph. If None, uses
            the last created paragraph from session context.

    Returns:
        str: Element ID of the new run (format: "run_xxxxx").

    Raises:
        ValueError: If session_id is invalid or paragraph_id not found.
        ValueError: If no paragraph context available when paragraph_id is None.
        ValueError: If specified object is not a paragraph.

    Examples:
        Add run to specific paragraph:
        >>> session_id = docx_create()
        >>> para_id = docx_add_paragraph(session_id, "")
        >>> run_id = docx_add_run(session_id, "Hello ", paragraph_id=para_id)
        >>> run_id2 = docx_add_run(session_id, "World", paragraph_id=para_id)

        Use implicit context:
        >>> para_id = docx_add_paragraph(session_id, "")
        >>> run_id = docx_add_run(session_id, "Implicit context")

        Build formatted paragraph:
        >>> para_id = docx_add_paragraph(session_id, "")
        >>> run1 = docx_add_run(session_id, "Normal ", paragraph_id=para_id)
        >>> run2 = docx_add_run(session_id, "Bold", paragraph_id=para_id)
        >>> docx_set_font(session_id, run2, bold=True)

    Notes:
        - Supports legacy signature: docx_add_run(sid, para_id, text) for compatibility
        - Context mechanism allows omitting paragraph_id for sequential operations
        - Use docx_set_font() to apply formatting after creation

    See Also:
        - docx_add_paragraph: Create parent paragraph
        - docx_set_font: Format the run
        - docx_update_run_text: Modify existing run
    """
    from docx_mcp_server.server import session_manager

    # Compatibility shim for legacy calls: docx_add_run(sid, para_id, text)
    # If 'text' looks like a para_id and 'paragraph_id' is present (and doesn't look like a para_id)
    if text and text.startswith("para_") and paragraph_id and not paragraph_id.startswith("para_"):
        # Swap arguments
        real_para_id = text
        real_text = paragraph_id
        text = real_text
        paragraph_id = real_para_id

    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    if paragraph_id is None:
        # Implicit context
        if not session.last_created_id:
            raise ValueError("No paragraph context available. Please specify paragraph_id.")
        paragraph_id = session.last_created_id

    paragraph = session.get_object(paragraph_id)
    if not paragraph:
        raise ValueError(f"Paragraph {paragraph_id} not found")

    # Simple type check
    if not hasattr(paragraph, 'add_run'):
         # If the last_created_id was a table or something else, we might have an issue
         raise ValueError(f"Object {paragraph_id} is not a paragraph (cannot add run)")

    run = paragraph.add_run(text)
    r_id = session.register_object(run, "run")

    # Update context: access action (we modified the paragraph, but the 'current' object of interest is now the run)
    session.update_context(r_id, action="access")

    return r_id

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
        str: Success message confirming the update.

    Raises:
        ValueError: If session_id or run_id is invalid.
        ValueError: If specified object is not a run.

    Examples:
        Update run text:
        >>> session_id = docx_create()
        >>> para_id = docx_add_paragraph(session_id, "")
        >>> run_id = docx_add_run(session_id, "Old", paragraph_id=para_id)
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

    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    run = session.get_object(run_id)
    if not run:
        raise ValueError(f"Run {run_id} not found")

    if not hasattr(run, 'text'):
        raise ValueError(f"Object {run_id} is not a run")

    # Update text while preserving formatting
    run.text = new_text

    return f"Run {run_id} updated successfully"

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
        str: Success message confirming font update.

    Raises:
        ValueError: If session_id or run_id is invalid.
        ValueError: If color_hex is not valid 6-character hex string.

    Examples:
        Basic formatting:
        >>> session_id = docx_create()
        >>> para_id = docx_add_paragraph(session_id, "")
        >>> run_id = docx_add_run(session_id, "Important", paragraph_id=para_id)
        >>> docx_set_font(session_id, run_id, size=14, bold=True)

        Apply color:
        >>> run_id = docx_add_run(session_id, "Red text", paragraph_id=para_id)
        >>> docx_set_font(session_id, run_id, color_hex="FF0000")

        Multiple properties:
        >>> run_id = docx_add_run(session_id, "Styled", paragraph_id=para_id)
        >>> docx_set_font(session_id, run_id, size=16, bold=True, italic=True, color_hex="0000FF")

    Notes:
        - Size is in points (1 point = 1/72 inch)
        - Color format is RRGGBB without '#' prefix
        - Omitted parameters are not changed
        - Setting bold/italic to False explicitly removes the formatting

    See Also:
        - docx_add_run: Create run to format
        - docx_set_properties: Advanced formatting options
    """
    from docx_mcp_server.server import session_manager

    

    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    run = session.get_object(run_id)
    if not run:
        raise ValueError(f"Run {run_id} not found")

    font = run.font
    if size is not None:
        font.size = Pt(size)
    if bold is not None:
        font.bold = bold
    if italic is not None:
        font.italic = italic
    if color_hex:
        # Parse hex string "RRGGBB"
        try:
            r = int(color_hex[0:2], 16)
            g = int(color_hex[2:4], 16)
            b = int(color_hex[4:6], 16)
            font.color.rgb = RGBColor(r, g, b)
        except ValueError:
            raise ValueError(f"Invalid hex color: {color_hex}")

    return f"Font updated for {run_id}"


def register_tools(mcp: FastMCP):
    """Register text run (formatting) tools"""
    mcp.tool()(docx_add_run)
    mcp.tool()(docx_update_run_text)
    mcp.tool()(docx_set_font)