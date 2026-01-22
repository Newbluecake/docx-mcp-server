"""Composite tools for common scenarios - high-level operations"""
import logging
import json
from typing import Optional
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


def docx_add_formatted_paragraph(
    session_id: str,
    text: str,
    bold: bool = False,
    italic: bool = False,
    size: float = None,
    color_hex: str = None,
    alignment: str = None,
    style: str = None
) -> str:
    """
    Create a formatted paragraph in one step.

    Combines docx_add_paragraph + docx_add_run + docx_set_font + docx_set_alignment
    into a single operation for common use cases.

    Typical Use Cases:
        - Quickly add formatted content to documents
        - Create styled headings or emphasis text
        - Reduce multiple tool calls to one

    Args:
        session_id (str): Active session ID.
        text (str): Paragraph text content.
        bold (bool): Make text bold. Defaults to False.
        italic (bool): Make text italic. Defaults to False.
        size (float): Font size in points (e.g., 12.0, 14.5).
        color_hex (str): Hex color without '#' (e.g., "FF0000" for red).
        alignment (str): Paragraph alignment: "left", "center", "right", "justify".
        style (str): Built-in style name (e.g., 'Body Text').

    Returns:
        str: Element ID of the created paragraph.

    Examples:
        Create bold red text:
        >>> para_id = docx_add_formatted_paragraph(
        ...     session_id, "Important!", bold=True, color_hex="FF0000"
        ... )

        Create centered heading:
        >>> para_id = docx_add_formatted_paragraph(
        ...     session_id, "Title", size=16, alignment="center"
        ... )
    """
    from docx_mcp_server.server import session_manager
    from docx_mcp_server.tools.paragraph_tools import docx_add_paragraph
    from docx_mcp_server.tools.run_tools import docx_add_run, docx_set_font
    from docx_mcp_server.tools.format_tools import docx_set_alignment

    try:
        # Step 1: Create paragraph
        para_id = docx_add_paragraph(session_id, "", style=style)

        # Step 2: Add run with text
        run_id = docx_add_run(session_id, text, paragraph_id=para_id)

        # Step 3: Apply font formatting if specified
        if any([bold, italic, size, color_hex]):
            docx_set_font(session_id, run_id, size=size, bold=bold, italic=italic, color_hex=color_hex)

        # Step 4: Apply alignment if specified
        if alignment:
            docx_set_alignment(session_id, para_id, alignment)

        logger.info(f"Created formatted paragraph: {para_id}")
        return para_id

    except Exception as e:
        logger.exception(f"Failed to create formatted paragraph: {e}")
        raise ValueError(f"Failed to create formatted paragraph: {e}")


def docx_quick_edit(
    session_id: str,
    search_text: str,
    new_text: str = None,
    bold: bool = None,
    italic: bool = None,
    size: float = None,
    color_hex: str = None
) -> str:
    """
    Find and edit paragraphs in one step.

    Combines docx_find_paragraphs + docx_update_paragraph_text + formatting
    for quick editing workflows.

    Typical Use Cases:
        - Edit existing documents quickly
        - Find and replace with formatting changes
        - Update specific content without manual ID tracking

    Args:
        session_id (str): Active session ID.
        search_text (str): Text to search for in paragraphs.
        new_text (str): New text to replace (if None, only formatting changes).
        bold (bool): Set bold formatting.
        italic (bool): Set italic formatting.
        size (float): Font size in points.
        color_hex (str): Hex color without '#'.

    Returns:
        str: JSON with modified paragraph count and IDs.

    Examples:
        Replace text:
        >>> result = docx_quick_edit(session_id, "old text", new_text="new text")

        Change formatting only:
        >>> result = docx_quick_edit(session_id, "important", bold=True, color_hex="FF0000")
    """
    from docx_mcp_server.tools.content_tools import docx_find_paragraphs
    from docx_mcp_server.tools.paragraph_tools import docx_update_paragraph_text
    from docx_mcp_server.tools.run_tools import docx_set_font
    from docx_mcp_server.server import session_manager

    try:
        # Find matching paragraphs
        matches_json = docx_find_paragraphs(session_id, search_text)
        matches = json.loads(matches_json)

        if not matches:
            return json.dumps({"modified_count": 0, "message": "No matching paragraphs found"})

        modified_ids = []

        for match in matches:
            para_id = match["id"]

            # Update text if specified
            if new_text is not None:
                docx_update_paragraph_text(session_id, para_id, new_text)

            # Apply formatting if specified
            if any([bold is not None, italic is not None, size, color_hex]):
                session = session_manager.get_session(session_id)
                paragraph = session.get_object(para_id)

                # Apply formatting to all runs in paragraph
                for run in paragraph.runs:
                    run_id = session._get_element_id(run, auto_register=True)
                    docx_set_font(session_id, run_id, size=size, bold=bold, italic=italic, color_hex=color_hex)

            modified_ids.append(para_id)

        result = {
            "modified_count": len(modified_ids),
            "paragraph_ids": modified_ids
        }

        logger.info(f"Quick edit modified {len(modified_ids)} paragraphs")
        return json.dumps(result)

    except Exception as e:
        logger.exception(f"Quick edit failed: {e}")
        raise ValueError(f"Quick edit failed: {e}")


def docx_get_structure_summary(
    session_id: str,
    max_headings: int = 10,
    max_tables: int = 5,
    max_paragraphs: int = 0,
    include_content: bool = False
) -> str:
    """
    Get a lightweight document structure summary.

    Returns a simplified structure with configurable limits to reduce token usage.
    Much lighter than docx_extract_template_structure for quick overview.

    Typical Use Cases:
        - Quickly understand document layout
        - Get table of contents
        - Find specific sections without full content

    Args:
        session_id (str): Active session ID.
        max_headings (int): Maximum headings to return. Defaults to 10.
        max_tables (int): Maximum tables to return. Defaults to 5.
        max_paragraphs (int): Maximum paragraphs to return. Defaults to 0 (none).
        include_content (bool): Include text content. Defaults to False (structure only).

    Returns:
        str: JSON with document structure summary.

    Examples:
        Get headings only:
        >>> summary = docx_get_structure_summary(session_id)

        Get headings and tables:
        >>> summary = docx_get_structure_summary(session_id, max_tables=10)
    """
    from docx_mcp_server.server import session_manager

    try:
        session = session_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        doc = session.document
        structure = {
            "headings": [],
            "tables": [],
            "paragraphs": []
        }

        heading_count = 0
        table_count = 0
        para_count = 0

        for element in doc.element.body:
            # Process headings
            if element.tag.endswith('p'):
                para = next((p for p in doc.paragraphs if p._element == element), None)
                if para and para.style.name.startswith('Heading'):
                    if heading_count < max_headings:
                        heading_info = {
                            "level": int(para.style.name.split()[-1]) if para.style.name.split()[-1].isdigit() else 1,
                            "style": para.style.name
                        }
                        if include_content:
                            heading_info["text"] = para.text
                        structure["headings"].append(heading_info)
                        heading_count += 1

                # Process regular paragraphs
                elif para and max_paragraphs > 0 and para_count < max_paragraphs:
                    para_info = {"style": para.style.name}
                    if include_content:
                        para_info["text"] = para.text[:100]  # Truncate long text
                    structure["paragraphs"].append(para_info)
                    para_count += 1

            # Process tables
            elif element.tag.endswith('tbl') and table_count < max_tables:
                table = next((t for t in doc.tables if t._element == element), None)
                if table:
                    table_info = {
                        "rows": len(table.rows),
                        "cols": len(table.columns)
                    }
                    if include_content:
                        # Include first row as header sample
                        table_info["first_row"] = [cell.text[:50] for cell in table.rows[0].cells]
                    structure["tables"].append(table_info)
                    table_count += 1

        structure["summary"] = {
            "total_headings": heading_count,
            "total_tables": table_count,
            "total_paragraphs": para_count
        }

        logger.info(f"Generated structure summary for session {session_id}")
        return json.dumps(structure, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.exception(f"Failed to generate structure summary: {e}")
        raise ValueError(f"Failed to generate structure summary: {e}")


def docx_smart_fill_table(
    session_id: str,
    table_identifier: str,
    data: str,
    has_header: bool = True,
    auto_resize: bool = True
) -> str:
    """
    Intelligently fill table with data, auto-expanding rows as needed.

    Combines table lookup + fill + row addition in one operation.

    Typical Use Cases:
        - Fill tables from database query results
        - Import CSV/JSON data into documents
        - Populate templates with dynamic data

    Args:
        session_id (str): Active session ID.
        table_identifier (str): Table index (e.g., "0") or text to find table.
        data (str): JSON array of arrays: [["col1", "col2"], ["val1", "val2"]].
        has_header (bool): First row is header. Defaults to True.
        auto_resize (bool): Auto-add rows if needed. Defaults to True.

    Returns:
        str: JSON with fill status and row count.

    Examples:
        Fill table by index:
        >>> data = '[["Name", "Age"], ["Alice", "30"], ["Bob", "25"]]'
        >>> result = docx_smart_fill_table(session_id, "0", data)

        Fill table by content:
        >>> result = docx_smart_fill_table(session_id, "Employee", data)
    """
    from docx_mcp_server.tools.table_tools import (
        docx_get_table, docx_find_table, docx_fill_table, docx_add_table_row
    )
    from docx_mcp_server.server import session_manager

    try:
        # Parse data
        data_array = json.loads(data)
        if not isinstance(data_array, list) or not data_array:
            raise ValueError("Data must be a non-empty JSON array")

        # Find table
        try:
            # Try as index first
            table_id = docx_get_table(session_id, int(table_identifier))
        except (ValueError, TypeError):
            # Try as search text
            table_id = docx_find_table(session_id, table_identifier)

        session = session_manager.get_session(session_id)
        table = session.get_object(table_id)

        # Calculate rows needed
        data_rows = len(data_array) - (1 if has_header else 0)
        existing_rows = len(table.rows) - (1 if has_header else 0)

        # Add rows if needed
        if auto_resize and data_rows > existing_rows:
            rows_to_add = data_rows - existing_rows
            for _ in range(rows_to_add):
                docx_add_table_row(session_id, table_id)
            logger.info(f"Added {rows_to_add} rows to table")

        # Fill table
        start_row = 1 if has_header else 0
        docx_fill_table(session_id, data, table_id, start_row=start_row)

        result = {
            "status": "success",
            "rows_filled": len(data_array),
            "rows_added": max(0, data_rows - existing_rows) if auto_resize else 0
        }

        logger.info(f"Smart fill completed: {result}")
        return json.dumps(result)

    except Exception as e:
        logger.exception(f"Smart fill table failed: {e}")
        raise ValueError(f"Smart fill table failed: {e}")


def docx_format_range(
    session_id: str,
    start_text: str,
    end_text: str,
    bold: bool = None,
    italic: bool = None,
    size: float = None,
    color_hex: str = None
) -> str:
    """
    Apply formatting to a range of paragraphs between two markers.

    Finds paragraphs containing start_text and end_text, then formats
    all paragraphs in between (inclusive).

    Typical Use Cases:
        - Format entire sections at once
        - Apply consistent styling to ranges
        - Bulk formatting operations

    Args:
        session_id (str): Active session ID.
        start_text (str): Text marking range start.
        end_text (str): Text marking range end.
        bold (bool): Set bold formatting.
        italic (bool): Set italic formatting.
        size (float): Font size in points.
        color_hex (str): Hex color without '#'.

    Returns:
        str: JSON with formatted paragraph count.

    Examples:
        Format section:
        >>> result = docx_format_range(
        ...     session_id, "Chapter 1", "Chapter 2", bold=True, size=14
        ... )
    """
    from docx_mcp_server.server import session_manager
    from docx_mcp_server.tools.run_tools import docx_set_font

    try:
        session = session_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        doc = session.document
        paragraphs = list(doc.paragraphs)

        # Find start and end indices
        start_idx = None
        end_idx = None

        for i, para in enumerate(paragraphs):
            if start_text in para.text and start_idx is None:
                start_idx = i
            if end_text in para.text:
                end_idx = i

        if start_idx is None:
            raise ValueError(f"Start text '{start_text}' not found")
        if end_idx is None:
            raise ValueError(f"End text '{end_text}' not found")
        if start_idx > end_idx:
            raise ValueError("Start text appears after end text")

        # Format range
        formatted_count = 0
        for i in range(start_idx, end_idx + 1):
            para = paragraphs[i]
            for run in para.runs:
                run_id = session._get_element_id(run, auto_register=True)
                docx_set_font(session_id, run_id, size=size, bold=bold, italic=italic, color_hex=color_hex)
            formatted_count += 1

        result = {
            "formatted_count": formatted_count,
            "start_index": start_idx,
            "end_index": end_idx
        }

        logger.info(f"Formatted range: {formatted_count} paragraphs")
        return json.dumps(result)

    except Exception as e:
        logger.exception(f"Format range failed: {e}")
        raise ValueError(f"Format range failed: {e}")


def register_tools(mcp: FastMCP):
    """Register composite tools with MCP server"""
    mcp.tool()(docx_add_formatted_paragraph)
    mcp.tool()(docx_quick_edit)
    mcp.tool()(docx_get_structure_summary)
    mcp.tool()(docx_smart_fill_table)
    mcp.tool()(docx_format_range)
    logger.info("Composite tools registered")
