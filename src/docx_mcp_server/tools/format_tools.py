"""Formatting and styling tools"""
import json
import logging
from mcp.server.fastmcp import FastMCP
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches
from docx_mcp_server.core.properties import set_properties
from docx_mcp_server.core.format_painter import FormatPainter
from docx_mcp_server.utils.format_template import TemplateManager

logger = logging.getLogger(__name__)

# Helper for alignment
ALIGNMENT_MAP = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
}


def docx_set_alignment(session_id: str, paragraph_id: str, alignment: str) -> str:
    """
    Set horizontal alignment for a paragraph.

    Controls how text is aligned within the paragraph margins. Affects the entire
    paragraph, not individual runs.

    Typical Use Cases:
        - Center headings and titles
        - Right-align dates or signatures
        - Justify body text for formal documents

    Args:
        session_id (str): Active session ID returned by docx_create().
        paragraph_id (str): ID of the paragraph to align.
        alignment (str): Alignment value. Must be one of:
            - "left": Align text to left margin (default)
            - "center": Center text between margins
            - "right": Align text to right margin
            - "justify": Distribute text evenly between margins

    Returns:
        str: Success message confirming alignment change.

    Raises:
        ValueError: If session_id or paragraph_id is invalid.
        ValueError: If alignment is not one of the valid values.

    Examples:
        Center a heading:
        >>> session_id = docx_create()
        >>> para_id = docx_add_heading(session_id, "Title", level=0)
        >>> docx_set_alignment(session_id, para_id, "center")

        Right-align a date:
        >>> para_id = docx_add_paragraph(session_id, "January 21, 2026")
        >>> docx_set_alignment(session_id, para_id, "right")

        Justify body text:
        >>> para_id = docx_add_paragraph(session_id, "Long paragraph text...")
        >>> docx_set_alignment(session_id, para_id, "justify")

    Notes:
        - Alignment is case-insensitive
        - Applies to entire paragraph, not individual runs
        - Default alignment is "left"

    See Also:
        - docx_add_paragraph: Create paragraph to align
        - docx_set_properties: Advanced paragraph formatting
    """
    from docx_mcp_server.server import session_manager

    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    paragraph = session.get_object(paragraph_id)
    if not paragraph:
        raise ValueError(f"Paragraph {paragraph_id} not found")

    if alignment.lower() not in ALIGNMENT_MAP:
        raise ValueError(f"Invalid alignment: {alignment}. Must be one of {list(ALIGNMENT_MAP.keys())}")

    paragraph.alignment = ALIGNMENT_MAP[alignment.lower()]
    return f"Alignment set to {alignment} for {paragraph_id}"

def docx_set_properties(session_id: str, properties: str, element_id: str = None) -> str:
    """
    Set advanced properties on a document element using JSON configuration.

    Provides flexible property setting for runs, paragraphs, tables, and cells.
    Supports font, paragraph format, and other advanced formatting options.

    Typical Use Cases:
        - Apply complex formatting in one call
        - Set properties not covered by dedicated tools
        - Batch apply multiple formatting options

    Args:
        session_id (str): Active session ID returned by docx_create().
        properties (str): JSON string defining properties to set. Structure:
            {
                "font": {"bold": true, "size": 12, "name": "Arial"},
                "paragraph_format": {"alignment": "center", "line_spacing": 1.5}
            }
        element_id (str, optional): ID of element to modify (run, paragraph, table, cell).
            If None, uses last accessed object from session context.

    Returns:
        str: Success message confirming property update.

    Raises:
        ValueError: If session_id or element_id is invalid.
        ValueError: If properties is not valid JSON.
        ValueError: If no element context available when element_id is None.

    Examples:
        Set font properties:
        >>> session_id = docx_create()
        >>> para_id = docx_add_paragraph(session_id, "")
        >>> run_id = docx_add_run(session_id, "Text", paragraph_id=para_id)
        >>> props = '{"font": {"bold": true, "size": 14, "name": "Arial"}}'
        >>> docx_set_properties(session_id, props, element_id=run_id)

        Set paragraph format:
        >>> props = '{"paragraph_format": {"alignment": "center", "line_spacing": 1.5}}'
        >>> docx_set_properties(session_id, props, element_id=para_id)

    Notes:
        - JSON must be valid and properly escaped
        - Available properties depend on element type
        - Use dedicated tools (docx_set_font, docx_set_alignment) for simpler cases

    See Also:
        - docx_set_font: Simpler font formatting
        - docx_set_alignment: Simpler alignment setting
    """
    from docx_mcp_server.server import session_manager

    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    target_id = element_id
    if not target_id:
        target_id = session.last_accessed_id
        if not target_id:
            raise ValueError("No element context available. Please specify element_id.")

    obj = session.get_object(target_id)
    if not obj:
        raise ValueError(f"Object {target_id} not found")

    try:
        props_dict = json.loads(properties)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON string in properties")

    set_properties(obj, props_dict)

    # Update context: we accessed/modified this object
    session.update_context(target_id, action="access")

    return f"Properties updated for {target_id}"

def docx_format_copy(session_id: str, source_id: str, target_id: str) -> str:
    """
    Copy formatting from source element to target element.

    Transfers formatting properties between elements of the same type. Supports
    Run-to-Run, Paragraph-to-Paragraph, and Table-to-Table copying.

    Typical Use Cases:
        - Apply consistent formatting across elements
        - Replicate styling from templates
        - Maintain formatting consistency

    Args:
        session_id (str): Active session ID returned by docx_create().
        source_id (str): ID of source element to copy formatting from.
        target_id (str): ID of target element to apply formatting to.

    Returns:
        str: Success message confirming format copy.

    Raises:
        ValueError: If session_id, source_id, or target_id is invalid.
        ValueError: If source and target are not the same element type.

    Examples:
        Copy run formatting:
        >>> session_id = docx_create()
        >>> para_id = docx_add_paragraph(session_id, "")
        >>> run1 = docx_add_run(session_id, "Styled", paragraph_id=para_id)
        >>> docx_set_font(session_id, run1, bold=True, size=14, color_hex="FF0000")
        >>> run2 = docx_add_run(session_id, "Copy style", paragraph_id=para_id)
        >>> docx_format_copy(session_id, run1, run2)

        Copy paragraph formatting:
        >>> para1 = docx_add_paragraph(session_id, "Source")
        >>> docx_set_alignment(session_id, para1, "center")
        >>> para2 = docx_add_paragraph(session_id, "Target")
        >>> docx_format_copy(session_id, para1, para2)

    Notes:
        - Source and target must be same type (run/paragraph/table)
        - Only formatting is copied, not content
        - Target content is preserved
        - Supports: font properties, alignment, spacing, borders

    See Also:
        - docx_set_font: Set specific font properties
        - docx_set_alignment: Set alignment directly
    """
    from docx_mcp_server.server import session_manager

    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    source = session.get_object(source_id)
    if not source:
        raise ValueError(f"Source object {source_id} not found")

    target = session.get_object(target_id)
    if not target:
        raise ValueError(f"Target object {target_id} not found")

    painter = FormatPainter()
    painter.copy_format(source, target)

    # Update context: we modified the target
    session.update_context(target_id, action="access")

    return f"Format copied from {source_id} to {target_id}"

def docx_set_margins(
    session_id: str,
    top: float = None,
    bottom: float = None,
    left: float = None,
    right: float = None
) -> str:
    """
    Set page margins for the document section.

    Adjusts the white space around the content area on each page. Applies to the
    last section of the document (typically the entire document if single-section).

    Typical Use Cases:
        - Adjust margins for printing requirements
        - Create narrow margins for more content
        - Set wide margins for annotations

    Args:
        session_id (str): Active session ID returned by docx_create().
        top (float, optional): Top margin in inches.
        bottom (float, optional): Bottom margin in inches.
        left (float, optional): Left margin in inches.
        right (float, optional): Right margin in inches.

    Returns:
        str: Success message confirming margin update.

    Raises:
        ValueError: If session_id is invalid or session has expired.

    Examples:
        Set all margins:
        >>> session_id = docx_create()
        >>> docx_set_margins(session_id, top=1.0, bottom=1.0, left=1.0, right=1.0)

        Set narrow margins:
        >>> docx_set_margins(session_id, top=0.5, bottom=0.5, left=0.5, right=0.5)

        Set only top and bottom:
        >>> docx_set_margins(session_id, top=1.5, bottom=1.5)

    Notes:
        - All measurements are in inches (1 inch = 2.54 cm)
        - Omitted parameters leave existing margins unchanged
        - Applies to the last section (usually entire document)
        - Default Word margins are typically 1 inch on all sides

    See Also:
        - docx_add_page_break: Control page breaks
    """
    from docx_mcp_server.server import session_manager



    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    # For simplicity, apply to the last section (usually where we are working)
    # or all sections? Let's apply to the last section for now as a default "current" context.
    section = session.document.sections[-1]

    if top is not None:
        section.top_margin = Inches(top)
    if bottom is not None:
        section.bottom_margin = Inches(bottom)
    if left is not None:
        section.left_margin = Inches(left)
    if right is not None:
        section.right_margin = Inches(right)

    return "Margins updated"

def docx_extract_format_template(session_id: str, element_id: str) -> str:
    """
    Extract style and formatting properties from an element as a reusable template.

    Captures font, paragraph, or table properties into a JSON structure that can be
    stored and applied to other elements later.

    Typical Use Cases:
        - Create a library of reusable styles
        - "Pickup" formatting to apply elsewhere
        - Persist styles between sessions

    Args:
        session_id (str): Active session ID.
        element_id (str): ID of the element to extract format from.

    Returns:
        str: JSON string containing the format template.

    Raises:
        ValueError: If element not found or type unsupported.
    """
    from docx_mcp_server.server import session_manager

    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    element = session.get_object(element_id)
    if not element:
        raise ValueError(f"Element {element_id} not found")

    manager = TemplateManager()
    try:
        template = manager.extract_template(element)
        return manager.to_json(template)
    except Exception as e:
        raise ValueError(f"Failed to extract template: {str(e)}")


def docx_apply_format_template(session_id: str, element_id: str, template_json: str) -> str:
    """
    Apply a format template to an element.

    Applies properties defined in the template JSON to the target element.
    Ignores properties that don't apply to the target type.

    Typical Use Cases:
        - Apply standard styles
        - Replicate formatting extracted earlier
        - Batch format elements

    Args:
        session_id (str): Active session ID.
        element_id (str): Target element ID.
        template_json (str): JSON string returned by docx_extract_format_template.

    Returns:
        str: Success message.
    """
    from docx_mcp_server.server import session_manager

    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    element = session.get_object(element_id)
    if not element:
        raise ValueError(f"Element {element_id} not found")

    manager = TemplateManager()
    try:
        template = manager.from_json(template_json)
        manager.apply_template(element, template)
        return f"Template applied to {element_id}"
    except Exception as e:
        raise ValueError(f"Failed to apply template: {str(e)}")


def register_tools(mcp: FastMCP):
    """Register formatting and styling tools"""
    mcp.tool()(docx_set_alignment)
    mcp.tool()(docx_set_properties)
    mcp.tool()(docx_format_copy)
    mcp.tool()(docx_set_margins)
    mcp.tool()(docx_extract_format_template)
    mcp.tool()(docx_apply_format_template)
