"""Advanced document operations"""
import os
import json
import logging
from mcp.server.fastmcp import FastMCP
from docx.shared import Inches
from docx_mcp_server.core.replacer import replace_text_in_paragraph
from docx_mcp_server.utils.text_tools import TextTools

logger = logging.getLogger(__name__)


def docx_replace_text(session_id: str, old_text: str, new_text: str, scope_id: str = None) -> str:
    """
    Replace all occurrences of text in the document or a specific scope.

    Searches and replaces text while preserving formatting. Can operate on the entire
    document or be limited to a specific element (paragraph, table, etc.).

    Typical Use Cases:
        - Replace placeholders in templates
        - Update repeated text globally
        - Batch text modifications

    Args:
        session_id (str): Active session ID returned by docx_create().
        old_text (str): Text to find and replace (exact match).
        new_text (str): Replacement text.
        scope_id (str, optional): ID of element to limit scope (paragraph, table, cell).
            If None, searches entire document body.

    Returns:
        str: Summary message with count of replacements made.

    Raises:
        ValueError: If session_id or scope_id is invalid.

    Examples:
        Replace globally:
        >>> session_id = docx_create(file_path="./template.docx")
        >>> result = docx_replace_text(session_id, "{{COMPANY}}", "Acme Corp")
        >>> print(result)
        'Replaced 5 occurrences of {{COMPANY}}'

        Replace in specific paragraph:
        >>> para_id = docx_find_paragraphs(session_id, "{{NAME}}")[0]["id"]
        >>> docx_replace_text(session_id, "{{NAME}}", "John", scope_id=para_id)

        Replace in table:
        >>> table_id = docx_find_table(session_id, "Invoice")
        >>> docx_replace_text(session_id, "TBD", "Completed", scope_id=table_id)

    Notes:
        - Preserves text formatting (bold, italic, etc.)
        - Exact text match (case-sensitive)
        - Searches document body, tables, and cells
        - Does not search headers/footers

    See Also:
        - docx_find_paragraphs: Find specific paragraphs
        - docx_update_paragraph_text: Replace entire paragraph
    """
    from docx_mcp_server.server import session_manager

    logger.debug(f"docx_replace_text called: session_id={session_id}, old_text='{old_text}', new_text='{new_text}', scope_id={scope_id}")

    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"docx_replace_text failed: Session {session_id} not found")
        raise ValueError(f"Session {session_id} not found")

    # Use shared scope resolution logic
    tools = TextTools()
    if scope_id:
        obj = session.get_object(scope_id)
        if not obj:
            logger.error(f"docx_replace_text failed: Scope object {scope_id} not found")
            raise ValueError(f"Scope object {scope_id} not found")
        targets = tools.collect_paragraphs_from_scope(obj)
    else:
        targets = tools.collect_paragraphs_from_scope(None, session.document)

    count = 0
    for p in targets:
        if replace_text_in_paragraph(p, old_text, new_text):
            count += 1

    logger.debug(f"docx_replace_text success: replaced {count} occurrences")
    return f"Replaced {count} occurrences of '{old_text}'"

def docx_batch_replace_text(session_id: str, replacements_json: str, scope_id: str = None) -> str:
    """
    Perform batch text replacement across the document or a specific scope.

    Efficiently replaces multiple text patterns in a single pass. Strictly preserves
    formatting by only replacing text within individual runs. Does NOT match text
    that spans across multiple runs (e.g., if half a word is bold and half is not).

    Typical Use Cases:
        - Bulk fill templates ({NAME} -> "John", {DATE} -> "2023")
        - Anonymize documents (replace names with Redacted)
        - Update terminology globally

    Args:
        session_id (str): Active session ID.
        replacements_json (str): JSON object mapping old text to new text.
            Example: '{"{{NAME}}": "John Doe", "{{DATE}}": "2023-01-01"}'
        scope_id (str, optional): ID of element to limit scope (paragraph, table).
            If None, applies to entire document body.

    Returns:
        str: Summary message with total replacement count.

    Raises:
        ValueError: If JSON is invalid or session not found.
    """
    from docx_mcp_server.server import session_manager

    logger.debug(f"docx_batch_replace_text called: session_id={session_id}, replacements_len={len(replacements_json)}, scope_id={scope_id}")

    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"docx_batch_replace_text failed: Session {session_id} not found")
        raise ValueError(f"Session {session_id} not found")

    try:
        replacements = json.loads(replacements_json)
    except json.JSONDecodeError as e:
        logger.error(f"docx_batch_replace_text failed: Invalid JSON - {e}")
        raise ValueError("Invalid JSON for replacements")

    # Use shared scope resolution logic
    tools = TextTools()
    if scope_id:
        obj = session.get_object(scope_id)
        if not obj:
            logger.error(f"docx_batch_replace_text failed: Scope object {scope_id} not found")
            raise ValueError(f"Scope object {scope_id} not found")
        targets = tools.collect_paragraphs_from_scope(obj)
    else:
        targets = tools.collect_paragraphs_from_scope(None, session.document)

    count = tools.batch_replace_text(targets, replacements)

    logger.debug(f"docx_batch_replace_text success: replaced {count} occurrences")
    return f"Batch replacement completed. Replaced {count} occurrences."

def docx_insert_image(session_id: str, image_path: str, width: float = None, height: float = None, parent_id: str = None) -> str:
    """
    Insert an image into the document.

    Adds an image file to the document with optional size constraints. Images can be
    added to the document body or within specific paragraphs.

    Typical Use Cases:
        - Add logos or diagrams to documents
        - Insert charts or screenshots
        - Embed visual content in reports

    Args:
        session_id (str): Active session ID returned by docx_create().
        image_path (str): Absolute or relative path to the image file (PNG, JPG, etc.).
        width (float, optional): Image width in inches. If None, uses original size.
        height (float, optional): Image height in inches. If None, uses original size.
        parent_id (str, optional): ID of parent paragraph. If None, creates new paragraph.

    Returns:
        str: Element ID of the container paragraph (format: "para_xxxxx").

    Raises:
        ValueError: If session_id is invalid or image_path not found.
        FileNotFoundError: If image file does not exist.

    Examples:
        Insert image with default size:
        >>> session_id = docx_create()
        >>> para_id = docx_insert_image(session_id, "./logo.png")

        Insert with specific dimensions:
        >>> para_id = docx_insert_image(session_id, "./chart.png", width=4.0, height=3.0)

        Insert into existing paragraph:
        >>> para_id = docx_add_paragraph(session_id, "See image: ")
        >>> docx_insert_image(session_id, "./diagram.png", width=2.0, parent_id=para_id)

    Notes:
        - Supported formats: PNG, JPG, GIF, BMP
        - Size is in inches (1 inch = 2.54 cm)
        - If only width or height specified, aspect ratio is preserved
        - Image is embedded in document (increases file size)

    See Also:
        - docx_add_paragraph: Create container paragraph
    """
    from docx_mcp_server.server import session_manager

    logger.debug(f"docx_insert_image called: session_id={session_id}, image_path={image_path}, width={width}, height={height}, parent_id={parent_id}")

    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"docx_insert_image failed: Session {session_id} not found")
        raise ValueError(f"Session {session_id} not found")

    if not os.path.exists(image_path):
        logger.error(f"docx_insert_image failed: Image file not found - {image_path}")
        raise ValueError(f"Image file not found: {image_path}")

    # Determine parent
    parent = session.document
    if parent_id:
        parent_obj = session.get_object(parent_id)
        if parent_obj:
            # If parent is a paragraph, we can add a run with picture?
            # python-docx: run.add_picture()
            if hasattr(parent_obj, "add_run"):
                 # It's a paragraph
                 run = parent_obj.add_run()
                 run.add_picture(image_path, width=Inches(width) if width else None, height=Inches(height) if height else None)
                 r_id = session.register_object(run, "run")
                 session.update_context(r_id, action="create")

                 # Update cursor
                 session.cursor.element_id = r_id
                 session.cursor.position = "after"

                 # Attach context
                 result_msg = r_id
                 try:
                     context = session.get_cursor_context()
                     result_msg = f"{r_id}\n\n{context}"
                 except Exception as e:
                     logger.warning(f"Failed to get cursor context: {e}")

                 logger.debug(f"docx_insert_image success: created run {r_id} in paragraph {parent_id}")
                 return result_msg
            elif hasattr(parent_obj, "add_picture"):
                 # Maybe it's a run already? No, runs don't have add_picture, they ARE the container
                 # Actually run.add_picture exists.
                 pass

    # Default: Add new paragraph then run with picture
    paragraph = session.document.add_paragraph()
    run = paragraph.add_run()
    run.add_picture(image_path, width=Inches(width) if width else None, height=Inches(height) if height else None)

    # Register the run as the object of interest? Or the paragraph?
    # Let's register the paragraph as the structural element.
    p_id = session.register_object(paragraph, "para")
    session.update_context(p_id, action="create")

    # Update cursor
    session.cursor.element_id = p_id
    session.cursor.parent_id = "document_body"
    session.cursor.position = "after"

    # Attach context
    result_msg = p_id
    try:
        context = session.get_cursor_context()
        result_msg = f"{p_id}\n\n{context}"
    except Exception as e:
        logger.warning(f"Failed to get cursor context: {e}")

    logger.debug(f"docx_insert_image success: created paragraph {p_id}")
    return result_msg


def register_tools(mcp: FastMCP):
    """Register advanced document operations"""
    mcp.tool()(docx_replace_text)
    mcp.tool()(docx_batch_replace_text)
    mcp.tool()(docx_insert_image)
