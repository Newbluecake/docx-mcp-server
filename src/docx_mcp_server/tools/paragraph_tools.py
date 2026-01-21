"""Paragraph manipulation tools"""
import logging
from mcp.server.fastmcp import FastMCP
from docx_mcp_server.utils.metadata_tools import MetadataTools

logger = logging.getLogger(__name__)


def docx_add_paragraph(session_id: str, text: str, style: str = None, parent_id: str = None) -> str:
    """
    Add a new paragraph to the document or a specific parent container.

    Creates a paragraph with the specified text content. Paragraphs are the fundamental
    building blocks for text content in Word documents.

    Typical Use Cases:
        - Add body text to a document
        - Add content to table cells
        - Create structured content with specific styles

    Args:
        session_id (str): Active session ID returned by docx_create().
        text (str): Text content for the paragraph. Can be empty string.
        style (str, optional): Built-in style name (e.g., 'List Bullet', 'Body Text').
            Defaults to None (Normal style).
        parent_id (str, optional): ID of parent container (e.g., cell_id from docx_get_cell).
            If None, adds to document body.

    Returns:
        str: Element ID of the new paragraph (format: "para_xxxxx").

    Raises:
        ValueError: If session_id is invalid or parent_id not found.
        ValueError: If parent object cannot contain paragraphs.

    Examples:
        Add paragraph to document:
        >>> session_id = docx_create()
        >>> para_id = docx_add_paragraph(session_id, "Hello World")
        >>> print(para_id)
        'para_a1b2c3d4'

        Add styled paragraph:
        >>> para_id = docx_add_paragraph(session_id, "Item 1", style="List Bullet")

        Add paragraph to table cell:
        >>> table_id = docx_add_table(session_id, 2, 2)
        >>> cell_id = docx_get_cell(session_id, table_id, 0, 0)
        >>> para_id = docx_add_paragraph(session_id, "Cell content", parent_id=cell_id)

    Notes:
        - Returns element_id for use in subsequent operations (e.g., adding runs)
        - Sets session context to this paragraph for implicit operations
        - Empty text is valid - use for formatting-only paragraphs

    See Also:
        - docx_add_run: Add formatted text to paragraph
        - docx_add_heading: Add heading instead of paragraph
        - docx_update_paragraph_text: Modify existing paragraph
    """
    from docx_mcp_server.server import session_manager

    logger.debug(f"docx_add_paragraph called: session_id={session_id}, parent_id={parent_id}")
    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"docx_add_paragraph failed: Session {session_id} not found")
        raise ValueError(f"Session {session_id} not found")

    parent = session.document
    if parent_id:
        parent = session.get_object(parent_id)
        if not parent:
            logger.error(f"docx_add_paragraph failed: Parent {parent_id} not found")
            raise ValueError(f"Parent object {parent_id} not found")
        if not hasattr(parent, 'add_paragraph'):
            logger.error(f"docx_add_paragraph failed: Parent {parent_id} cannot contain paragraphs")
            raise ValueError(f"Object {parent_id} cannot contain paragraphs")

    paragraph = parent.add_paragraph(text, style=style)
    p_id = session.register_object(paragraph, "para")

    # Update context: this is a creation action
    session.update_context(p_id, action="create")

    logger.debug(f"docx_add_paragraph success: {p_id}")
    return p_id

def docx_add_heading(session_id: str, text: str, level: int = 1) -> str:
    """
    Add a heading to the document.

    Creates a heading paragraph with the specified level. Headings provide document
    structure and are used for navigation and table of contents generation.

    Typical Use Cases:
        - Create document sections and chapters
        - Structure reports and articles
        - Generate navigable document outlines

    Args:
        session_id (str): Active session ID returned by docx_create().
        text (str): Heading text content.
        level (int, optional): Heading level from 0-9. Level 0 is Title style,
            levels 1-9 are Heading 1-9 styles. Defaults to 1.

    Returns:
        str: Element ID of the new heading paragraph (format: "para_xxxxx").

    Raises:
        ValueError: If session_id is invalid or level is out of range.

    Examples:
        Add main heading:
        >>> session_id = docx_create()
        >>> h1_id = docx_add_heading(session_id, "Chapter 1", level=1)

        Add title and subheadings:
        >>> title_id = docx_add_heading(session_id, "Report Title", level=0)
        >>> h2_id = docx_add_heading(session_id, "Introduction", level=2)

    Notes:
        - Level 0 applies Title style (larger, centered)
        - Levels 1-9 apply Heading 1-9 styles
        - Headings are paragraphs with special styling

    See Also:
        - docx_add_paragraph: Add regular paragraph
    """
    from docx_mcp_server.server import session_manager

    logger.debug(f"docx_add_heading called: session_id={session_id}, text='{text}', level={level}")

    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"docx_add_heading failed: Session {session_id} not found")
        raise ValueError(f"Session {session_id} not found")

    heading = session.document.add_heading(text, level=level)
    h_id = session.register_object(heading, "para")

    # Update context: this is a creation action
    session.update_context(h_id, action="create")

    logger.debug(f"docx_add_heading success: {h_id}")
    return h_id

def docx_update_paragraph_text(session_id: str, paragraph_id: str, new_text: str) -> str:
    """
    Replace all text content in an existing paragraph.

    Clears all existing runs in the paragraph and replaces with a single run
    containing the new text. All previous formatting within the paragraph is lost.

    Typical Use Cases:
        - Update placeholder text in templates
        - Replace entire paragraph content
        - Reset paragraph to plain text

    Args:
        session_id (str): Active session ID returned by docx_create().
        paragraph_id (str): ID of the paragraph to update.
        new_text (str): New text content to replace existing content.

    Returns:
        str: Success message confirming the update.

    Raises:
        ValueError: If session_id or paragraph_id is invalid.
        ValueError: If specified object is not a paragraph.

    Examples:
        Update paragraph text:
        >>> session_id = docx_create()
        >>> para_id = docx_add_paragraph(session_id, "Old text")
        >>> result = docx_update_paragraph_text(session_id, para_id, "New text")
        >>> print(result)
        'Paragraph para_xxx updated successfully'

        Update template placeholder:
        >>> session_id = docx_create(file_path="./template.docx")
        >>> matches = docx_find_paragraphs(session_id, "{{NAME}}")
        >>> para_id = json.loads(matches)[0]["id"]
        >>> docx_update_paragraph_text(session_id, para_id, "John Doe")

    Notes:
        - Removes all existing runs and their formatting
        - Creates a single new run with the new text
        - To preserve formatting, use docx_update_run_text() on individual runs

    See Also:
        - docx_update_run_text: Update run while preserving formatting
        - docx_find_paragraphs: Find paragraphs to update
    """
    from docx_mcp_server.server import session_manager

    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    paragraph = session.get_object(paragraph_id)
    if not paragraph:
        raise ValueError(f"Paragraph {paragraph_id} not found")

    if not hasattr(paragraph, 'text'):
        raise ValueError(f"Object {paragraph_id} is not a paragraph")

    # Clear existing runs and set new text
    paragraph.clear()
    paragraph.add_run(new_text)

    return f"Paragraph {paragraph_id} updated successfully"

def docx_copy_paragraph(session_id: str, paragraph_id: str) -> str:
    """
    Create a deep copy of a paragraph with all formatting and runs.

    Duplicates a paragraph including its style, alignment, and all text runs with
    their individual formatting. The new paragraph is appended to the document.

    Typical Use Cases:
        - Duplicate formatted content
        - Replicate paragraph templates
        - Copy complex formatted text

    Args:
        session_id (str): Active session ID returned by docx_create().
        paragraph_id (str): ID of the paragraph to copy.

    Returns:
        str: Element ID of the new copied paragraph (format: "para_xxxxx").

    Raises:
        ValueError: If session_id or paragraph_id is invalid.
        ValueError: If specified object is not a paragraph.

    Examples:
        Copy a paragraph:
        >>> session_id = docx_create()
        >>> para_id = docx_add_paragraph(session_id, "")
        >>> run_id = docx_add_run(session_id, "Formatted", paragraph_id=para_id)
        >>> docx_set_font(session_id, run_id, bold=True, size=14)
        >>> new_para_id = docx_copy_paragraph(session_id, para_id)

    Notes:
        - Preserves paragraph style and alignment
        - Copies all runs with their formatting (bold, italic, size, color)
        - New paragraph is appended to document end
        - Original paragraph is unchanged

    See Also:
        - docx_copy_table: Copy tables
        - docx_add_paragraph: Create new paragraph
    """
    from docx_mcp_server.server import session_manager

    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    source_para = session.get_object(paragraph_id)
    if not source_para:
        raise ValueError(f"Paragraph {paragraph_id} not found")

    if not hasattr(source_para, 'runs'):
        raise ValueError(f"Object {paragraph_id} is not a paragraph")

    # Create new paragraph with same style
    new_para = session.document.add_paragraph(style=source_para.style)

    # Copy paragraph-level formatting
    if source_para.alignment is not None:
        new_para.alignment = source_para.alignment

    # Copy all runs with their formatting
    for run in source_para.runs:
        new_run = new_para.add_run(run.text)

        # Copy font properties
        if run.font.bold is not None:
            new_run.font.bold = run.font.bold
        if run.font.italic is not None:
            new_run.font.italic = run.font.italic
        if run.font.underline is not None:
            new_run.font.underline = run.font.underline
        if run.font.size is not None:
            new_run.font.size = run.font.size
        if run.font.color.rgb is not None:
            new_run.font.color.rgb = run.font.color.rgb

    # Track lineage metadata using shared utility
    meta = MetadataTools.create_copy_metadata(
        source_id=paragraph_id,
        source_type="paragraph"
    )

    return session.register_object(new_para, "para", metadata=meta)

def docx_delete(session_id: str, element_id: str = None) -> str:
    """
    Delete an element from the document.

    Removes a paragraph or table from the document. Note that deletion in python-docx
    is complex due to XML structure; primarily supports paragraphs and tables.

    Typical Use Cases:
        - Remove unwanted content
        - Clean up template placeholders
        - Delete empty or obsolete elements

    Args:
        session_id (str): Active session ID returned by docx_create().
        element_id (str, optional): ID of element to delete (paragraph or table).
            If None, uses last accessed element from context.

    Returns:
        str: Success message confirming deletion.

    Raises:
        ValueError: If session_id or element_id is invalid.
        ValueError: If no element context available when element_id is None.
        ValueError: If element cannot be deleted (no parent or unsupported type).

    Examples:
        Delete specific paragraph:
        >>> session_id = docx_create()
        >>> para_id = docx_add_paragraph(session_id, "Temporary")
        >>> docx_delete(session_id, para_id)
        'Deleted para_xxx'

        Delete using context:
        >>> para_id = docx_add_paragraph(session_id, "Remove me")
        >>> docx_delete(session_id)

        Delete found paragraph:
        >>> matches = docx_find_paragraphs(session_id, "{{REMOVE}}")
        >>> for match in json.loads(matches):
        ...     docx_delete(session_id, match["id"])

    Notes:
        - Primarily supports paragraphs and tables
        - Element is removed from object registry
        - Context is reset if deleted element was in context
        - Cannot delete runs independently (delete parent paragraph instead)

    See Also:
        - docx_find_paragraphs: Find paragraphs to delete
        - docx_replace_text: Alternative to deletion for text changes
    """
    from docx_mcp_server.server import session_manager

    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    if not element_id:
        element_id = session.last_accessed_id

    obj = session.get_object(element_id)
    if not obj:
         raise ValueError(f"Object {element_id} not found")

    # Try to delete
    # Strategy: get the XML element and remove it from its parent
    try:
        if hasattr(obj, "_element") and obj._element.getparent() is not None:
            obj._element.getparent().remove(obj._element)
            # Remove from registry?
            if element_id in session.object_registry:
                del session.object_registry[element_id]

            # Reset context if it pointed here
            if session.last_accessed_id == element_id:
                session.last_accessed_id = None
            if session.last_created_id == element_id:
                session.last_created_id = None

            return f"Deleted {element_id}"
        else:
             raise ValueError("Element has no parent or cannot be deleted")
    except Exception as e:
        raise ValueError(f"Failed to delete {element_id}: {str(e)}")

def docx_add_page_break(session_id: str) -> str:
    """
    Insert a page break at the current position in the document.

    Forces content after the break to start on a new page. Useful for separating
    sections or chapters in a document.

    Typical Use Cases:
        - Separate chapters or major sections
        - Start new content on a fresh page
        - Control pagination in reports

    Args:
        session_id (str): Active session ID returned by docx_create().

    Returns:
        str: Success message confirming page break insertion.

    Raises:
        ValueError: If session_id is invalid or session has expired.

    Examples:
        Add page break between sections:
        >>> session_id = docx_create()
        >>> docx_add_heading(session_id, "Chapter 1", level=1)
        >>> docx_add_paragraph(session_id, "Content of chapter 1...")
        >>> docx_add_page_break(session_id)
        >>> docx_add_heading(session_id, "Chapter 2", level=1)

    Notes:
        - Page break is inserted at the end of the document
        - Content added after this call will appear on the new page
        - Does not return an element_id (structural operation)

    See Also:
        - docx_add_heading: Add section headings
    """
    from docx_mcp_server.server import session_manager

    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    session.document.add_page_break()
    return "Page break added"


def register_tools(mcp: FastMCP):
    """Register paragraph manipulation tools"""
    mcp.tool()(docx_add_paragraph)
    mcp.tool()(docx_add_heading)
    mcp.tool()(docx_update_paragraph_text)
    mcp.tool()(docx_copy_paragraph)
    mcp.tool()(docx_delete)
    mcp.tool()(docx_add_page_break)