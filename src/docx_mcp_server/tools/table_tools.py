"""Table manipulation tools"""
import json
import logging
from mcp.server.fastmcp import FastMCP
from docx.shared import Inches
from docx_mcp_server.core.finder import Finder
from docx_mcp_server.core.copier import clone_table
from docx_mcp_server.utils.metadata_tools import MetadataTools
from docx_mcp_server.core.response import (
    create_context_aware_response,
    create_error_response,
    create_success_response
)

logger = logging.getLogger(__name__)


def docx_add_table(session_id: str, rows: int, cols: int) -> str:
    """
    Create a new table in the document.

    Adds a table with the specified dimensions. Tables are created with default
    'Table Grid' style and can be populated using cell operations.

    Typical Use Cases:
        - Create data tables for reports
        - Build structured layouts
        - Display tabular information

    Args:
        session_id (str): Active session ID returned by docx_create().
        rows (int): Number of rows to create (must be >= 1).
        cols (int): Number of columns to create (must be >= 1).

    Returns:
        str: JSON response with element_id and cursor context.

    Raises:
        ValueError: If session_id is invalid or rows/cols are less than 1.

    Examples:
        Create a simple table:
        >>> session_id = docx_create()
        >>> table_id = docx_add_table(session_id, rows=3, cols=2)
        >>> print(table_id)
        'table_a1b2c3d4'

        Create and populate table:
        >>> table_id = docx_add_table(session_id, 2, 3)
        >>> cell_id = docx_get_cell(session_id, table_id, 0, 0)
        >>> docx_add_paragraph_to_cell(session_id, cell_id, "Header 1")

    Notes:
        - Default style is 'Table Grid' with borders
        - Cells are not pre-registered - use docx_get_cell() to access them
        - Rows and columns can be added later with docx_add_table_row/col()

    See Also:
        - docx_get_cell: Access table cells
        - docx_fill_table: Batch populate table data
        - docx_add_table_row: Add rows dynamically
    """
    from docx_mcp_server.server import session_manager

    logger.debug(f"docx_add_table called: session_id={session_id}, rows={rows}, cols={cols}")
    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"docx_add_table failed: Session {session_id} not found")
        return create_error_response(f"Session {session_id} not found", error_type="SessionNotFound")

    try:
        table = session.document.add_table(rows=rows, cols=cols)
        table.style = 'Table Grid' # Default style
        t_id = session.register_object(table, "table")

        session.update_context(t_id, action="create")

        # Update cursor to point after the new table
        session.cursor.element_id = t_id
        session.cursor.parent_id = "document_body"
        session.cursor.position = "after"

        logger.debug(f"docx_add_table success: {t_id}")
        return create_context_aware_response(
            session,
            message=f"Table created successfully ({rows}x{cols})",
            element_id=t_id,
            rows=rows,
            cols=cols
        )
    except Exception as e:
        logger.exception(f"docx_add_table failed: {e}")
        return create_error_response(f"Failed to create table: {str(e)}", error_type="CreationError")

def docx_get_table(session_id: str, index: int) -> str:
    """
    Get a table by its position index in the document.

    Retrieves a table by its sequential position (0-based index) in the document.
    Useful when you know the table's position.

    Typical Use Cases:
        - Access tables by position in structured documents
        - Iterate through all tables in a document
        - Access specific table when structure is known

    Args:
        session_id (str): Active session ID returned by docx_create().
        index (int): Zero-based index of the table (0 for first table).

    Returns:
        str: JSON response with element_id.

    Raises:
        ValueError: If session_id is invalid.
        ValueError: If index is out of range (no table at that position).

    Examples:
        Get first table:
        >>> session_id = docx_create(file_path="./report.docx")
        >>> table_id = docx_get_table(session_id, 0)
        >>> print(table_id)
        'table_abc123'

        Iterate through all tables:
        >>> for i in range(3):
        ...     try:
        ...         table_id = docx_get_table(session_id, i)
        ...         print(f"Table {i}: {table_id}")
        ...     except ValueError:
        ...         break

    Notes:
        - Index is 0-based (first table is index 0)
        - Sets table as current context
        - Raises ValueError if index out of range

    See Also:
        - docx_find_table: Find table by content
    """
    from docx_mcp_server.server import session_manager

    logger.debug(f"docx_get_table called: session_id={session_id}, index={index}")

    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"docx_get_table failed: Session {session_id} not found")
        return create_error_response(f"Session {session_id} not found", error_type="SessionNotFound")

    try:
        finder = Finder(session.document)
        table = finder.get_table_by_index(index)
        if not table:
            logger.error(f"docx_get_table failed: Table at index {index} not found")
            return create_error_response(f"Table at index {index} not found", error_type="ElementNotFound")

        t_id = session._get_element_id(table, auto_register=True)
        session.update_context(t_id, action="access")

        logger.debug(f"docx_get_table success: {t_id}")
        return create_success_response(
            message=f"Table at index {index} retrieved",
            element_id=t_id,
            index=index
        )
    except Exception as e:
        logger.exception(f"docx_get_table failed: {e}")
        return create_error_response(f"Failed to get table: {str(e)}", error_type="RetrievalError")

def docx_find_table(session_id: str, text: str) -> str:
    """
    Find the first table containing specific text in any cell.

    Searches through all tables in the document and returns the first table
    that contains the specified text in any of its cells.

    Typical Use Cases:
        - Locate tables by header text
        - Find tables containing specific keywords
        - Navigate to tables in large documents

    Args:
        session_id (str): Active session ID returned by docx_create().
        text (str): Text to search for within table cells (case-insensitive).

    Returns:
        str: JSON response with element_id of the found table.

    Raises:
        ValueError: If session_id is invalid.
        ValueError: If no table found containing the specified text.

    Examples:
        Find table by header:
        >>> session_id = docx_create(file_path="./report.docx")
        >>> table_id = docx_find_table(session_id, "Sales Data")
        >>> print(table_id)
        'table_abc123'

        Find and modify table:
        >>> table_id = docx_find_table(session_id, "Employee")
        >>> docx_add_table_row(session_id, table_id)

    Notes:
        - Search is case-insensitive
        - Returns first matching table only
        - Searches all cells in all tables
        - Sets table as current context

    See Also:
        - docx_get_table: Get table by index
        - docx_find_paragraphs: Find paragraphs by text
    """
    from docx_mcp_server.server import session_manager

    logger.debug(f"docx_find_table called: session_id={session_id}, text='{text}'")

    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"docx_find_table failed: Session {session_id} not found")
        return create_error_response(f"Session {session_id} not found", error_type="SessionNotFound")

    try:
        finder = Finder(session.document)
        tables = finder.find_tables_by_text(text)
        if not tables:
            logger.error(f"docx_find_table failed: No table found containing text '{text}'")
            return create_error_response(f"No table found containing text '{text}'", error_type="NotFound")

        # Return the first match
        t_id = session._get_element_id(tables[0], auto_register=True)
        session.update_context(t_id, action="access")

        logger.debug(f"docx_find_table success: {t_id}")
        return create_success_response(
            message=f"Table found containing '{text}'",
            element_id=t_id,
            search_text=text
        )
    except Exception as e:
        logger.exception(f"docx_find_table failed: {e}")
        return create_error_response(f"Failed to find table: {str(e)}", error_type="SearchError")

def docx_get_cell(session_id: str, table_id: str, row: int, col: int) -> str:
    """
    Get a cell from a table by its row and column indices.

    Retrieves and registers a specific cell for subsequent operations. Cells are
    not automatically registered when tables are created to conserve memory.

    Typical Use Cases:
        - Access cells to add content
        - Modify specific cell properties
        - Navigate table structure

    Args:
        session_id (str): Active session ID returned by docx_create().
        table_id (str): ID of the table containing the cell.
        row (int): Row index (0-based, 0 is first row).
        col (int): Column index (0-based, 0 is first column).

    Returns:
        str: JSON response with element_id of the cell.

    Raises:
        ValueError: If session_id or table_id is invalid.
        ValueError: If row or col indices are out of range.

    Examples:
        Access table cells:
        >>> session_id = docx_create()
        >>> table_id = docx_add_table(session_id, 3, 2)
        >>> cell_id = docx_get_cell(session_id, table_id, 0, 0)
        >>> print(cell_id)
        'cell_a1b2c3d4'

        Populate first row:
        >>> for col in range(2):
        ...     cell_id = docx_get_cell(session_id, table_id, 0, col)
        ...     docx_add_paragraph_to_cell(session_id, cell_id, f"Header {col+1}")

    Notes:
        - Indices are 0-based (first cell is row=0, col=0)
        - Cell is registered and can be reused in subsequent calls
        - Out-of-range indices raise ValueError

    See Also:
        - docx_add_table: Create table
        - docx_add_paragraph_to_cell: Add content to cell
    """
    from docx_mcp_server.server import session_manager

    session = session_manager.get_session(session_id)
    if not session:
        return create_error_response(f"Session {session_id} not found", error_type="SessionNotFound")

    table = session.get_object(table_id)
    if not table:
        return create_error_response(f"Table {table_id} not found", error_type="ElementNotFound")

    try:
        cell = table.cell(row, col)
        c_id = session.register_object(cell, "cell")

        # Update context: accessing/getting a cell
        session.update_context(c_id, action="access")

        return create_success_response(
            message=f"Cell ({row}, {col}) retrieved",
            element_id=c_id,
            row=row,
            col=col
        )
    except IndexError:
        return create_error_response(f"Cell ({row}, {col}) out of range", error_type="IndexError")
    except Exception as e:
        logger.exception(f"docx_get_cell failed: {e}")
        return create_error_response(f"Failed to get cell: {str(e)}", error_type="RetrievalError")

def docx_add_paragraph_to_cell(session_id: str, cell_id: str, text: str) -> str:
    """
    Add a paragraph to a table cell.

    Adds text content to a cell. If the cell contains only an empty default paragraph,
    it reuses that paragraph; otherwise, it adds a new paragraph.

    Typical Use Cases:
        - Populate table cells with content
        - Add multiple paragraphs to a single cell
        - Fill table data programmatically

    Args:
        session_id (str): Active session ID returned by docx_create().
        cell_id (str): ID of the cell (from docx_get_cell()).
        text (str): Text content for the paragraph.

    Returns:
        str: JSON response with element_id of the paragraph and cursor context.

    Raises:
        ValueError: If session_id or cell_id is invalid.

    Examples:
        Add content to cell:
        >>> session_id = docx_create()
        >>> table_id = docx_add_table(session_id, 2, 2)
        >>> cell_id = docx_get_cell(session_id, table_id, 0, 0)
        >>> para_id = docx_add_paragraph_to_cell(session_id, cell_id, "Header")

        Add multiple paragraphs to cell:
        >>> para1 = docx_add_paragraph_to_cell(session_id, cell_id, "Line 1")
        >>> para2 = docx_add_paragraph_to_cell(session_id, cell_id, "Line 2")

    Notes:
        - Cells have one empty paragraph by default
        - First call reuses default paragraph if empty
        - Subsequent calls add new paragraphs

    See Also:
        - docx_get_cell: Get cell to populate
        - docx_fill_table: Batch populate multiple cells
    """
    from docx_mcp_server.server import session_manager

    session = session_manager.get_session(session_id)
    if not session:
        return create_error_response(f"Session {session_id} not found", error_type="SessionNotFound")

    cell = session.get_object(cell_id)
    if not cell:
        return create_error_response(f"Cell {cell_id} not found", error_type="ElementNotFound")

    try:
        # If the cell is empty (just has the default empty paragraph), reuse it
        if len(cell.paragraphs) == 1 and not cell.paragraphs[0].text:
            p = cell.paragraphs[0]
            p.text = text
            p_id = session.register_object(p, "para")

            # Update context: modifying existing paragraph
            session.update_context(p_id, action="access")

            # Update cursor
            session.cursor.element_id = p_id
            session.cursor.parent_id = cell_id
            session.cursor.position = "after"

            return create_context_aware_response(
                session,
                message="Cell paragraph updated",
                element_id=p_id
            )
        else:
            p = cell.add_paragraph(text)
            p_id = session.register_object(p, "para")

            # Update context: creating new paragraph
            session.update_context(p_id, action="create")

            # Update cursor
            session.cursor.element_id = p_id
            session.cursor.parent_id = cell_id
            session.cursor.position = "after"

            return create_context_aware_response(
                session,
                message="Paragraph added to cell",
                element_id=p_id
            )
    except Exception as e:
        logger.exception(f"docx_add_paragraph_to_cell failed: {e}")
        return create_error_response(f"Failed to add paragraph to cell: {str(e)}", error_type="CreationError")

def docx_add_table_row(session_id: str, table_id: str = None) -> str:
    """
    Add a new row to the end of a table.

    Appends a row with the same number of columns as existing rows. Useful for
    dynamically expanding tables as data is added.

    Typical Use Cases:
        - Add data rows to existing tables
        - Expand tables dynamically
        - Build tables incrementally

    Args:
        session_id (str): Active session ID returned by docx_create().
        table_id (str, optional): ID of the table. If None, uses last accessed table
            from session context.

    Returns:
        str: JSON response confirming row addition.

    Raises:
        ValueError: If session_id or table_id is invalid.
        ValueError: If no table context available when table_id is None.

    Examples:
        Add row to specific table:
        >>> session_id = docx_create()
        >>> table_id = docx_add_table(session_id, 2, 3)
        >>> docx_add_table_row(session_id, table_id)
        'Row added to table_xxx'

        Use implicit context:
        >>> table_id = docx_add_table(session_id, 2, 3)
        >>> docx_add_table_row(session_id)

    Notes:
        - New row has same column count as existing rows
        - Cells in new row are empty by default
        - Use docx_get_cell() to populate new row

    See Also:
        - docx_add_table_col: Add column to table
        - docx_get_cell: Access cells in new row
    """
    from docx_mcp_server.server import session_manager

    logger.debug(f"docx_add_table_row called: session_id={session_id}, table_id={table_id}")

    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"docx_add_table_row failed: Session {session_id} not found")
        return create_error_response(f"Session {session_id} not found", error_type="SessionNotFound")

    if not table_id:
        table_id = session.last_accessed_id

    if not table_id:
        return create_error_response("No table specified and no context available", error_type="NoContext")

    table = session.get_object(table_id)
    if not table or not hasattr(table, 'add_row'):
        logger.error(f"docx_add_table_row failed: Valid table context not found for ID {table_id}")
        return create_error_response(f"Valid table context not found for ID {table_id}", error_type="InvalidElementType")

    try:
        table.add_row()
        session.update_context(table_id, action="access")

        # Update cursor to point to the table (structural change)
        session.cursor.element_id = table_id
        session.cursor.position = "after"

        logger.debug(f"docx_add_table_row success: row added to {table_id}")
        return create_context_aware_response(
            session,
            message=f"Row added to table",
            table_id=table_id,
            new_row_count=len(table.rows)
        )
    except Exception as e:
        logger.exception(f"docx_add_table_row failed: {e}")
        return create_error_response(f"Failed to add row: {str(e)}", error_type="ModificationError")

def docx_add_table_col(session_id: str, table_id: str = None) -> str:
    """
    Add a new column to the right side of a table.

    Appends a column to all rows in the table. Default width is 1 inch.

    Typical Use Cases:
        - Expand table structure dynamically
        - Add columns for additional data fields
        - Adjust table layout after creation

    Args:
        session_id (str): Active session ID returned by docx_create().
        table_id (str, optional): ID of the table. If None, uses last accessed table
            from session context.

    Returns:
        str: JSON response confirming column addition.

    Raises:
        ValueError: If session_id or table_id is invalid.
        ValueError: If no table context available when table_id is None.

    Examples:
        Add column to table:
        >>> session_id = docx_create()
        >>> table_id = docx_add_table(session_id, 3, 2)
        >>> docx_add_table_col(session_id, table_id)
        'Column added to table_xxx'

    Notes:
        - New column is added to the right (last position)
        - Default width is 1 inch
        - All rows receive the new column

    See Also:
        - docx_add_table_row: Add row to table
    """
    from docx_mcp_server.server import session_manager

    logger.debug(f"docx_add_table_col called: session_id={session_id}, table_id={table_id}")

    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"docx_add_table_col failed: Session {session_id} not found")
        return create_error_response(f"Session {session_id} not found", error_type="SessionNotFound")

    if not table_id:
        table_id = session.last_accessed_id

    if not table_id:
        return create_error_response("No table specified and no context available", error_type="NoContext")

    table = session.get_object(table_id)
    if not table or not hasattr(table, 'add_column'):
        logger.error(f"docx_add_table_col failed: Valid table context not found for ID {table_id}")
        return create_error_response(f"Valid table context not found for ID {table_id}", error_type="InvalidElementType")

    try:
        table.add_column(width=Inches(1.0))
        session.update_context(table_id, action="access")

        # Update cursor
        session.cursor.element_id = table_id
        session.cursor.position = "after"

        logger.debug(f"docx_add_table_col success: column added to {table_id}")
        return create_context_aware_response(
            session,
            message=f"Column added to table",
            table_id=table_id,
            new_col_count=len(table.columns)
        )
    except Exception as e:
        logger.exception(f"docx_add_table_col failed: {e}")
        return create_error_response(f"Failed to add column: {str(e)}", error_type="ModificationError")

def docx_fill_table(session_id: str, data: str, table_id: str = None, start_row: int = 0) -> str:
    """
    Batch populate table cells with data from a 2D array.

    Efficiently fills multiple rows and columns in one operation. Data is provided
    as a JSON array of arrays, where each inner array represents a row.

    Typical Use Cases:
        - Populate tables from database query results
        - Fill tables with CSV or JSON data
        - Batch insert data efficiently

    Args:
        session_id (str): Active session ID returned by docx_create().
        data (str): JSON string representing 2D array: [["col1", "col2"], ["val1", "val2"]].
            Each inner array is a row, each element is a cell value.
        table_id (str, optional): ID of the table. If None, uses last accessed table.
        start_row (int, optional): Row index to start filling from (0-based). Defaults to 0.

    Returns:
        str: JSON response with number of rows filled.

    Raises:
        ValueError: If session_id or table_id is invalid.
        ValueError: If data is not valid JSON or not a 2D array.

    Examples:
        Fill table with data:
        >>> session_id = docx_create()
        >>> table_id = docx_add_table(session_id, 1, 3)
        >>> data = '[["Name", "Age", "City"], ["Alice", "30", "NYC"], ["Bob", "25", "LA"]]'
        >>> result = docx_fill_table(session_id, data, table_id)
        >>> print(result)
        'Table filled with 3 rows starting at 0'

        Fill starting from row 1 (skip header):
        >>> data = '[["Alice", "30", "NYC"], ["Bob", "25", "LA"]]'
        >>> docx_fill_table(session_id, data, table_id, start_row=1)

    Notes:
        - Automatically adds rows if data exceeds table size
        - If data columns > table columns, extra data is truncated
        - Null values are converted to empty strings
        - Overwrites existing cell content

    See Also:
        - docx_add_table: Create table to fill
        - docx_add_paragraph_to_cell: Fill individual cells
    """
    from docx_mcp_server.server import session_manager

    logger.debug(f"docx_fill_table called: session_id={session_id}, data_len={len(data)}, table_id={table_id}, start_row={start_row}")

    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"docx_fill_table failed: Session {session_id} not found")
        return create_error_response(f"Session {session_id} not found", error_type="SessionNotFound")

    if not table_id:
        table_id = session.last_accessed_id

    if not table_id:
        return create_error_response("No table specified and no context available", error_type="NoContext")

    table = session.get_object(table_id)
    if not table or not hasattr(table, 'rows'):
        logger.error(f"docx_fill_table failed: Valid table context not found for ID {table_id}")
        return create_error_response(f"Valid table context not found for ID {table_id}", error_type="InvalidElementType")

    try:
        rows_data = json.loads(data)
    except json.JSONDecodeError as e:
        logger.error(f"docx_fill_table failed: Invalid JSON data - {e}")
        return create_error_response("Invalid JSON data", error_type="JSONDecodeError")

    if not isinstance(rows_data, list):
        logger.error(f"docx_fill_table failed: Data must be a list of lists")
        return create_error_response("Data must be a list of lists", error_type="InvalidDataFormat")

    try:
        current_row_idx = start_row

        for row_data in rows_data:
            # Ensure we have enough rows
            if current_row_idx >= len(table.rows):
                table.add_row()

            row = table.rows[current_row_idx]

            # Fill cells
            for col_idx, cell_value in enumerate(row_data):
                if col_idx < len(row.cells):
                    cell = row.cells[col_idx]
                    cell.text = str(cell_value) if cell_value is not None else ""

            current_row_idx += 1

        session.update_context(table_id, action="access")

        # Update cursor
        session.cursor.element_id = table_id
        session.cursor.position = "after"

        logger.debug(f"docx_fill_table success: filled {len(rows_data)} rows starting at {start_row}")
        return create_context_aware_response(
            session,
            message=f"Table filled with {len(rows_data)} rows",
            table_id=table_id,
            rows_filled=len(rows_data),
            start_row=start_row
        )
    except Exception as e:
        logger.exception(f"docx_fill_table failed: {e}")
        return create_error_response(f"Failed to fill table: {str(e)}", error_type="FillError")

def docx_copy_table(session_id: str, table_id: str) -> str:
    """
    Create a deep copy of an existing table.

    Duplicates a table with all its content, formatting, and structure. The new
    table is appended to the document.

    Typical Use Cases:
        - Duplicate table templates
        - Create multiple similar tables
        - Replicate table structure with formatting

    Args:
        session_id (str): Active session ID returned by docx_create().
        table_id (str): ID of the source table to copy.

    Returns:
        str: JSON response with new element_id and cursor context.

    Raises:
        ValueError: If session_id or table_id is invalid.
        ValueError: If specified object is not a table.

    Examples:
        Copy a table:
        >>> session_id = docx_create()
        >>> table_id = docx_add_table(session_id, 2, 3)
        >>> docx_fill_table(session_id, '[["A", "B", "C"]]', table_id)
        >>> new_table_id = docx_copy_table(session_id, table_id)
        >>> print(new_table_id)
        'table_xyz789'

    Notes:
        - Creates complete deep copy (content + formatting)
        - New table is appended to document end
        - Original table is unchanged

    See Also:
        - docx_add_table: Create new table
        - docx_copy_paragraph: Copy paragraphs
    """
    from docx_mcp_server.server import session_manager

    logger.debug(f"docx_copy_table called: session_id={session_id}, table_id={table_id}")

    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"docx_copy_table failed: Session {session_id} not found")
        return create_error_response(f"Session {session_id} not found", error_type="SessionNotFound")

    table = session.get_object(table_id)
    if not table:
        logger.error(f"docx_copy_table failed: Table {table_id} not found")
        return create_error_response(f"Table {table_id} not found", error_type="ElementNotFound")

    # Check if it is a table
    if not hasattr(table, 'rows'):
        logger.error(f"docx_copy_table failed: Object {table_id} is not a table")
        return create_error_response(f"Object {table_id} is not a table", error_type="InvalidElementType")

    try:
        new_table = clone_table(table)

        # Track lineage metadata using shared utility
        meta = MetadataTools.create_copy_metadata(
            source_id=table_id,
            source_type="table"
        )

        t_id = session.register_object(new_table, "table", metadata=meta)

        session.update_context(t_id, action="create")

        # Update cursor
        session.cursor.element_id = t_id
        session.cursor.parent_id = "document_body"
        session.cursor.position = "after"

        logger.debug(f"docx_copy_table success: {t_id}")
        return create_context_aware_response(
            session,
            message="Table copied successfully",
            element_id=t_id,
            source_id=table_id
        )
    except Exception as e:
        logger.exception(f"docx_copy_table failed: {e}")
        return create_error_response(f"Failed to copy table: {str(e)}", error_type="CopyError")


def register_tools(mcp: FastMCP):
    """Register table manipulation tools"""
    mcp.tool()(docx_add_table)
    mcp.tool()(docx_get_table)
    mcp.tool()(docx_find_table)
    mcp.tool()(docx_get_cell)
    mcp.tool()(docx_add_paragraph_to_cell)
    mcp.tool()(docx_add_table_row)
    mcp.tool()(docx_add_table_col)
    mcp.tool()(docx_fill_table)
    mcp.tool()(docx_copy_table)