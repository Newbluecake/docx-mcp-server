import os
from mcp.server.fastmcp import FastMCP
from docx_mcp_server.core.session import SessionManager
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
def docx_create() -> str:
    """
    Create a new empty Word document session.

    Returns:
        str: The session_id to be used for subsequent operations.
    """
    return session_manager.create_session()

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
def docx_add_paragraph(session_id: str, text: str, style: str = None) -> str:
    """
    Add a paragraph to the document.

    Args:
        session_id: The active session ID.
        text: The text content of the paragraph.
        style: Optional style name (e.g., 'List Bullet').

    Returns:
        str: The element_id of the new paragraph (e.g., "para_1234").
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    paragraph = session.document.add_paragraph(text, style=style)
    return session.register_object(paragraph, "para")

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
def docx_add_run(session_id: str, paragraph_id: str, text: str) -> str:
    """
    Append a text run to an existing paragraph.

    Args:
        session_id: The active session ID.
        paragraph_id: The ID of the parent paragraph.
        text: The text to append.

    Returns:
        str: The element_id of the new run.
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    paragraph = session.get_object(paragraph_id)
    if not paragraph:
        raise ValueError(f"Paragraph {paragraph_id} not found")

    # Simple type check could be added here
    if not hasattr(paragraph, 'add_run'):
         raise ValueError(f"Object {paragraph_id} is not a paragraph")

    run = paragraph.add_run(text)
    return session.register_object(run, "run")

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
    return session.register_object(table, "table")

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



def main():
    mcp.run()

if __name__ == "__main__":
    main()
