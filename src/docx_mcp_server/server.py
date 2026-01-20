import os
import json
from typing import Optional
from mcp.server.fastmcp import FastMCP
from docx_mcp_server.core.session import SessionManager
from docx_mcp_server.core.properties import set_properties
from docx_mcp_server.core.finder import Finder, list_docx_files
from docx_mcp_server.core.copier import clone_table
from docx_mcp_server.core.replacer import replace_text_in_paragraph
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

# Initialize the MCP server
mcp = FastMCP("docx-mcp-server")

# Global session manager
session_manager = SessionManager()

# Helper for alignment
ALIGNMENT_MAP = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
}

@mcp.tool()
def docx_create(file_path: str = None, auto_save: bool = False) -> str:
    """
    Create a new Word document session, optionally loading an existing file.

    Args:
        file_path: Optional absolute path to an existing .docx file.
        auto_save: Whether to automatically save changes after every modification. Requires file_path.

    Returns:
        str: The session_id to be used for subsequent operations.
    """
    if file_path:
        pass
        # We allow creating new files at the path if they don't exist, handled by session manager logic mostly
        # or we can enforce existence. For now let's be flexible to allow "new file at path".

    return session_manager.create_session(file_path, auto_save=auto_save)

@mcp.tool()
def docx_read_content(session_id: str) -> str:
    """
    Read the text content of the document.

    Args:
        session_id: The active session ID.

    Returns:
        str: A text summary of the document content.
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    paragraphs = [p.text for p in session.document.paragraphs if p.text.strip()]
    return "\n".join(paragraphs) if paragraphs else "[Empty Document]"

@mcp.tool()
def docx_find_paragraphs(session_id: str, query: str) -> str:
    """
    Find paragraphs containing specific text and return their IDs.

    Args:
        session_id: The active session ID.
        query: The text to search for (case-insensitive).

    Returns:
        str: JSON string of list of dicts: [{"id": "para_...", "text": "..."}]
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    matches = []
    for p in session.document.paragraphs:
        if query.lower() in p.text.lower():
            # Only register if we found a match to keep registry clean?
            # The design says yes.
            p_id = session.register_object(p, "para")
            matches.append({"id": p_id, "text": p.text})

    return json.dumps(matches)

@mcp.tool()
def docx_get_table(session_id: str, index: int) -> str:
    """
    Get a table by its index (0-based) and set it as current context.

    Args:
        session_id: The active session ID.
        index: The index of the table (0 for the first table).

    Returns:
        str: The element_id of the table.
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    finder = Finder(session.document)
    table = finder.get_table_by_index(index)
    if not table:
        raise ValueError(f"Table at index {index} not found")

    t_id = session.register_object(table, "table")
    session.update_context(t_id, action="access")
    return t_id

@mcp.tool()
def docx_find_table(session_id: str, text: str) -> str:
    """
    Find the first table containing specific text.

    Args:
        session_id: The active session ID.
        text: Text to search for within table cells.

    Returns:
        str: The element_id of the found table.
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    finder = Finder(session.document)
    tables = finder.find_tables_by_text(text)
    if not tables:
        raise ValueError(f"No table found containing text '{text}'")

    # Return the first match
    t_id = session.register_object(tables[0], "table")
    session.update_context(t_id, action="access")
    return t_id

@mcp.tool()
def docx_list_files(directory: str = ".") -> str:
    """
    List .docx files in the specified directory.

    Args:
        directory: Directory path to scan (defaults to current dir).

    Returns:
        str: JSON list of filenames.
    """
    try:
        files = list_docx_files(directory)
        return json.dumps(files)
    except Exception as e:
        raise ValueError(str(e))

@mcp.tool()
def docx_copy_table(session_id: str, table_id: str) -> str:
    """
    Deep copy an existing table and append it to the document.

    Args:
        session_id: The active session ID.
        table_id: The ID of the source table.

    Returns:
        str: The element_id of the new copied table.
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    table = session.get_object(table_id)
    if not table:
        raise ValueError(f"Table {table_id} not found")

    # Check if it is a table
    if not hasattr(table, 'rows'):
        raise ValueError(f"Object {table_id} is not a table")

    new_table = clone_table(table)
    t_id = session.register_object(new_table, "table")

    session.update_context(t_id, action="create")
    return t_id

@mcp.tool()
def docx_add_table_row(session_id: str, table_id: str = None) -> str:
    """
    Add a row to the table.

    Args:
        session_id: The active session ID.
        table_id: The ID of the table. If None, uses context.

    Returns:
        str: Success message.
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    if not table_id:
        table_id = session.last_accessed_id

    table = session.get_object(table_id)
    if not table or not hasattr(table, 'add_row'):
        raise ValueError(f"Valid table context not found for ID {table_id}")

    table.add_row()
    # We could return the new row's cells IDs but usually just adding row is structural.
    # Let's keep context on the table.
    session.update_context(table_id, action="access")
    return f"Row added to {table_id}"

@mcp.tool()
def docx_add_table_col(session_id: str, table_id: str = None) -> str:
    """
    Add a column to the table.

    Args:
        session_id: The active session ID.
        table_id: The ID of the table.

    Returns:
        str: Success message.
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    if not table_id:
        table_id = session.last_accessed_id

    table = session.get_object(table_id)
    if not table or not hasattr(table, 'add_column'):
        raise ValueError(f"Valid table context not found for ID {table_id}")

    # width is mandatory for add_column in python-docx usually, or defaults?
    # It requires width. Let's default to 1 inch.
    table.add_column(width=Inches(1.0))
    session.update_context(table_id, action="access")
    return f"Column added to {table_id}"

@mcp.tool()
def docx_fill_table(session_id: str, data: str, table_id: str = None, start_row: int = 0) -> str:
    """
    Batch fill a table with data.

    Args:
        session_id: The active session ID.
        data: JSON string representing a 2D array [[col1, col2], [col1, col2]].
        table_id: The ID of the table.
        start_row: The row index to start filling from (0-based).

    Returns:
        str: Success message.
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    if not table_id:
        table_id = session.last_accessed_id

    table = session.get_object(table_id)
    if not table or not hasattr(table, 'rows'):
        raise ValueError(f"Valid table context not found for ID {table_id}")

    try:
        rows_data = json.loads(data)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON data")

    if not isinstance(rows_data, list):
         raise ValueError("Data must be a list of lists")

    current_row_idx = start_row

    for row_data in rows_data:
        # Ensure we have enough rows
        if current_row_idx >= len(table.rows):
            table.add_row()

        row = table.rows[current_row_idx]

        # Fill cells
        for col_idx, cell_value in enumerate(row_data):
            # Ensure we have enough columns?
            # python-docx doesn't auto-expand cols on row access usually.
            # We skip if out of bounds or expand?
            # Requirement says: "If data cols > table cols, auto truncate or ignore" (from requirements doc analysis implicit)
            # Actually design said: "If data cols > table cols, auto truncate or ignore."
            if col_idx < len(row.cells):
                cell = row.cells[col_idx]
                # We simply set text. If complex formatting needed, use atomic tools.
                cell.text = str(cell_value) if cell_value is not None else ""

        current_row_idx += 1

    session.update_context(table_id, action="access")
    return f"Table filled with {len(rows_data)} rows starting at {start_row}"

@mcp.tool()
def docx_insert_image(session_id: str, image_path: str, width: float = None, height: float = None, parent_id: str = None) -> str:
    """
    Insert an image into the document.

    Args:
        session_id: The active session ID.
        image_path: Absolute path to the image file.
        width: Width in inches (optional).
        height: Height in inches (optional).
        parent_id: Optional parent ID (e.g. paragraph or run? Usually added to run).
                   If None, adds a new paragraph at the end.

    Returns:
        str: The element_id of the container (usually a Run or Paragraph).
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    if not os.path.exists(image_path):
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
                 return r_id
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
    return p_id

@mcp.tool()
def docx_replace_text(session_id: str, old_text: str, new_text: str, scope_id: str = None) -> str:
    """
    Replace text occurrences in the document or a specific scope.

    Args:
        session_id: The active session ID.
        old_text: The text to find.
        new_text: The text to replace with.
        scope_id: Optional ID of a specific element (Paragraph, Table) to limit scope.
                  If None, scans the whole document body.

    Returns:
        str: Summary of replacements count.
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    count = 0
    targets = []

    if scope_id:
        obj = session.get_object(scope_id)
        if not obj:
            raise ValueError(f"Scope object {scope_id} not found")
        # Identify what kind of object
        if hasattr(obj, "paragraphs"): # Document or Cell or Table (no, table has rows)
            targets.extend(obj.paragraphs)
        elif hasattr(obj, "rows"): # Table
            for row in obj.rows:
                for cell in row.cells:
                    targets.extend(cell.paragraphs)
        elif hasattr(obj, "text"): # Paragraph or Run
            # If it's a paragraph, we treat it as a target
            if hasattr(obj, "runs"):
                targets.append(obj)
    else:
        # Full document
        targets.extend(session.document.paragraphs)
        for table in session.document.tables:
            for row in table.rows:
                for cell in row.cells:
                    targets.extend(cell.paragraphs)

    for p in targets:
        if replace_text_in_paragraph(p, old_text, new_text):
            count += 1
            # If successful, we updated the paragraph in place

    return f"Replaced {count} occurrences of '{old_text}'"

@mcp.tool()
def docx_get_context(session_id: str) -> str:
    """
    Get the current context state of the session.

    Args:
        session_id: The active session ID.

    Returns:
        str: JSON string with last_created_id, last_accessed_id, etc.
    """
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

@mcp.tool()
def docx_delete(session_id: str, element_id: str = None) -> str:
    """
    Delete an element from the document.
    Note: Deleting is complex in python-docx as parent references aren't always perfect.
    We generally support deleting Paragraphs and Tables.

    Args:
        session_id: The active session ID.
        element_id: The ID of the element to delete. If None, uses context.

    Returns:
        str: Success message.
    """
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

@mcp.tool()
def docx_save(session_id: str, file_path: str) -> str:
    """
    Save the document associated with the session to a file.

    Args:
        session_id: The ID of the active session.
        file_path: The absolute path where the file should be saved.

    Returns:
        str: A success message.
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found or expired")

    # Security check: Ensure we are writing to an allowed location if needed.
    # For now, we assume the user (Claude) acts with the user's permissions.
    try:
        session.document.save(file_path)
        return f"Document saved successfully to {file_path}"
    except Exception as e:
        raise RuntimeError(f"Failed to save document: {str(e)}")

@mcp.tool()
def docx_close(session_id: str) -> str:
    """
    Close the session and free resources.

    Args:
        session_id: The ID of the session to close.
    """
    success = session_manager.close_session(session_id)
    if success:
        return f"Session {session_id} closed successfully"
    else:
        return f"Session {session_id} not found"

@mcp.tool()
def docx_add_paragraph(session_id: str, text: str, style: str = None, parent_id: str = None) -> str:
    """
    Add a paragraph to the document or a specific parent (like a Cell).

    Args:
        session_id: The active session ID.
        text: The text content of the paragraph.
        style: Optional style name (e.g., 'List Bullet').
        parent_id: Optional ID of the parent object (e.g., a cell_id).
                   If None, adds to the end of the document body.

    Returns:
        str: The element_id of the new paragraph (e.g., "para_1234").
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    parent = session.document
    if parent_id:
        parent = session.get_object(parent_id)
        if not parent:
            raise ValueError(f"Parent object {parent_id} not found")
        if not hasattr(parent, 'add_paragraph'):
            raise ValueError(f"Object {parent_id} cannot contain paragraphs")

    paragraph = parent.add_paragraph(text, style=style)
    p_id = session.register_object(paragraph, "para")

    # Update context: this is a creation action
    session.update_context(p_id, action="create")

    return p_id

@mcp.tool()
def docx_add_heading(session_id: str, text: str, level: int = 1) -> str:
    """
    Add a heading to the document.

    Args:
        session_id: The active session ID.
        text: The heading text.
        level: The heading level (0-9).

    Returns:
        str: The element_id of the new paragraph.
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    heading = session.document.add_heading(text, level=level)
    return session.register_object(heading, "para")

@mcp.tool()
def docx_add_run(session_id: str, text: str, paragraph_id: str = None) -> str:
    """
    Append a text run to a paragraph.
    Supports both (text, paragraph_id) and legacy (paragraph_id, text) signatures.

    Args:
        session_id: The active session ID.
        text: The text to append.
        paragraph_id: The ID of the parent paragraph.
                      If None, uses the last created paragraph context.

    Returns:
        str: The element_id of the new run.
    """
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

@mcp.tool()
def docx_set_properties(session_id: str, properties: str, element_id: str = None) -> str:
    """
    Set various properties on a document element (Run, Paragraph, Table, Cell).

    Args:
        session_id: The active session ID.
        properties: A JSON string defining the properties to set.
                    Example: '{"font": {"bold": true, "size": 12}, "paragraph_format": {"alignment": "center"}}'
        element_id: The ID of the element to modify.
                    If None, uses the last accessed object (context).

    Returns:
        str: Success message.
    """
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

@mcp.tool()
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

    Args:
        session_id: The active session ID.
        run_id: The ID of the text run to modify.
        size: Font size in points (e.g., 12.0).
        bold: True to set bold, False to unset.
        italic: True to set italic, False to unset.
        color_hex: Hex color string (e.g., "FF0000" for red).

    Returns:
        str: Success message.
    """
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

@mcp.tool()
def docx_set_alignment(session_id: str, paragraph_id: str, alignment: str) -> str:
    """
    Set paragraph alignment.

    Args:
        session_id: The active session ID.
        paragraph_id: The ID of the paragraph.
        alignment: One of "left", "center", "right", "justify".

    Returns:
        str: Success message.
    """
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

@mcp.tool()
def docx_add_page_break(session_id: str) -> str:
    """
    Add a page break to the document.

    Args:
        session_id: The active session ID.

    Returns:
        str: Success message.
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    session.document.add_page_break()
    return "Page break added"

@mcp.tool()
def docx_set_margins(
    session_id: str,
    top: float = None,
    bottom: float = None,
    left: float = None,
    right: float = None
) -> str:
    """
    Set page margins for the current section (usually the whole document if one section).
    Units are in Inches.

    Args:
        session_id: The active session ID.
        top: Top margin in inches.
        bottom: Bottom margin in inches.
        left: Left margin in inches.
        right: Right margin in inches.
    """
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

@mcp.tool()
def docx_add_table(session_id: str, rows: int, cols: int) -> str:
    """
    Add a table to the document.

    Args:
        session_id: The active session ID.
        rows: Number of rows.
        cols: Number of columns.

    Returns:
        str: The element_id of the new table (e.g., "table_123").
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    table = session.document.add_table(rows=rows, cols=cols)
    table.style = 'Table Grid' # Default style
    t_id = session.register_object(table, "table")

    session.update_context(t_id, action="create")

    return t_id

@mcp.tool()
def docx_get_cell(session_id: str, table_id: str, row: int, col: int) -> str:
    """
    Get the element_id for a specific cell in a table.
    Cells are not automatically registered when a table is created to save memory.
    You must request the cell ID to edit it.

    Args:
        session_id: The active session ID.
        table_id: The ID of the table.
        row: Row index (0-based).
        col: Column index (0-based).

    Returns:
        str: The element_id of the cell (e.g., "cell_456").
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    table = session.get_object(table_id)
    if not table:
        raise ValueError(f"Table {table_id} not found")

    try:
        cell = table.cell(row, col)
    except IndexError:
        raise ValueError(f"Cell ({row}, {col}) out of range")

    return session.register_object(cell, "cell")

@mcp.tool()
def docx_add_paragraph_to_cell(session_id: str, cell_id: str, text: str) -> str:
    """
    Add a paragraph to a specific cell.
    Note: Cells usually come with one empty paragraph by default.
    This adds a NEW paragraph. To edit the existing one, accessing it via children isn't fully exposed yet,
    so adding new content is the primary path.

    Args:
        session_id: The active session ID.
        cell_id: The ID of the cell.
        text: Text content.

    Returns:
        str: The element_id of the new paragraph.
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    cell = session.get_object(cell_id)
    if not cell:
        raise ValueError(f"Cell {cell_id} not found")

    # If the cell is empty (just has the default empty paragraph), we might want to use it?
    # For simplicity/consistency, let's just use the add_paragraph method of the cell.
    # But usually, user wants to fill the cell.
    # Check if cell.paragraphs[0] is empty?
    if len(cell.paragraphs) == 1 and not cell.paragraphs[0].text:
        p = cell.paragraphs[0]
        p.text = text
        return session.register_object(p, "para")
    else:
        p = cell.add_paragraph(text)
        return session.register_object(p, "para")

@mcp.tool()
def docx_copy_paragraph(session_id: str, paragraph_id: str) -> str:
    """
    Copy a paragraph with all its formatting and runs.

    Args:
        session_id: The active session ID.
        paragraph_id: The ID of the paragraph to copy.

    Returns:
        str: The element_id of the new copied paragraph.
    """
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

    return session.register_object(new_para, "para")

@mcp.tool()
def docx_update_paragraph_text(session_id: str, paragraph_id: str, new_text: str) -> str:
    """
    Update the text content of an existing paragraph.
    This replaces all runs in the paragraph with a single run containing the new text.

    Args:
        session_id: The active session ID.
        paragraph_id: The ID of the paragraph to update.
        new_text: The new text content.

    Returns:
        str: Success message.
    """
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

@mcp.tool()
def docx_update_run_text(session_id: str, run_id: str, new_text: str) -> str:
    """
    Update the text content of an existing run while preserving its formatting.

    Args:
        session_id: The active session ID.
        run_id: The ID of the run to update.
        new_text: The new text content.

    Returns:
        str: Success message.
    """
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


def main():
    import argparse
    parser = argparse.ArgumentParser(description="DOCX MCP Server")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "sse"], help="Transport protocol")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (SSE only)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (SSE only)")

    # Parse known args to avoid conflict if FastMCP parses its own (though we call run explicitly)
    args, unknown = parser.parse_known_args()

    if args.transport == "sse":
        print(f"Starting SSE server on {args.host}:{args.port}...", flush=True)

        # FastMCP.run() doesn't accept host/port args, we must update settings directly
        mcp.settings.host = args.host
        mcp.settings.port = args.port

        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
