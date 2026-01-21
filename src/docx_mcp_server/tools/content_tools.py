"""Content reading and search tools"""
import json
import logging
from mcp.server.fastmcp import FastMCP
from docx_mcp_server.core.finder import Finder, list_docx_files
from docx_mcp_server.core.template_parser import TemplateParser

logger = logging.getLogger(__name__)


def docx_read_content(session_id: str) -> str:
    """
    Read and extract all text content from the document.

    Extracts text from all paragraphs in the document body, preserving order
    but not formatting. Useful for content analysis, search, or preview.

    Typical Use Cases:
        - Preview document content before modification
        - Extract text for analysis or indexing
        - Verify document content after generation

    Args:
        session_id (str): Active session ID returned by docx_create().

    Returns:
        str: Newline-separated text content of all paragraphs.
            Returns "[Empty Document]" if document has no content.

    Raises:
        ValueError: If session_id is invalid or session has expired.

    Examples:
        Read content from a document:
        >>> session_id = docx_create(file_path="./report.docx")
        >>> content = docx_read_content(session_id)
        >>> print(content)
        'Chapter 1\nIntroduction\nThis is the first paragraph...'

    Notes:
        - Only extracts text, formatting information is not included
        - Empty paragraphs are skipped
        - Does not extract text from tables or headers/footers

    See Also:
        - docx_find_paragraphs: Search for specific text in paragraphs
        - docx_extract_template_structure: Get full document structure
    """
    from docx_mcp_server.server import session_manager

    logger.debug(f"docx_read_content called: session_id={session_id}")

    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"docx_read_content failed: Session {session_id} not found")
        raise ValueError(f"Session {session_id} not found")

    paragraphs = [p.text for p in session.document.paragraphs if p.text.strip()]
    result = "\n".join(paragraphs) if paragraphs else "[Empty Document]"

    logger.debug(f"docx_read_content success: extracted {len(paragraphs)} paragraphs")
    return result

def docx_find_paragraphs(session_id: str, query: str) -> str:
    """
    Find all paragraphs containing specific text and return their IDs.

    Searches through all paragraphs in the document and returns those containing
    the query text. Useful for locating and modifying specific content.

    Typical Use Cases:
        - Find placeholders to replace (e.g., "{{NAME}}")
        - Locate paragraphs for modification
        - Search document content programmatically

    Args:
        session_id (str): Active session ID returned by docx_create().
        query (str): Text to search for (case-insensitive substring match).

    Returns:
        str: JSON array of objects with paragraph IDs and text:
            [{"id": "para_xxx", "text": "paragraph content"}, ...]

    Raises:
        ValueError: If session_id is invalid or session has expired.

    Examples:
        Find placeholders:
        >>> session_id = docx_create(file_path="./template.docx")
        >>> matches = docx_find_paragraphs(session_id, "{{NAME}}")
        >>> import json
        >>> results = json.loads(matches)
        >>> for match in results:
        ...     docx_update_paragraph_text(session_id, match["id"], "John Doe")

        Search for keyword:
        >>> matches = docx_find_paragraphs(session_id, "important")
        >>> results = json.loads(matches)
        >>> print(f"Found {len(results)} paragraphs with 'important'")

    Notes:
        - Search is case-insensitive
        - Returns all matching paragraphs
        - Paragraphs are automatically registered for subsequent operations
        - Empty paragraphs are not searched

    See Also:
        - docx_update_paragraph_text: Modify found paragraphs
        - docx_replace_text: Replace text globally
        - docx_find_table: Find tables by content
    """
    from docx_mcp_server.server import session_manager

    logger.debug(f"docx_find_paragraphs called: session_id={session_id}, query='{query}'")

    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"docx_find_paragraphs failed: Session {session_id} not found")
        raise ValueError(f"Session {session_id} not found")

    matches = []
    for p in session.document.paragraphs:
        if query.lower() in p.text.lower():
            # Only register if we found a match to keep registry clean?
            # The design says yes.
            p_id = session.register_object(p, "para")
            matches.append({"id": p_id, "text": p.text})

    logger.debug(f"docx_find_paragraphs success: found {len(matches)} matches")
    return json.dumps(matches)

def docx_list_files(directory: str = None) -> str:
    """
    List all .docx files in the specified directory.

    Scans a directory and returns a list of Word document files. Useful for
    discovering available documents before opening them.

    Typical Use Cases:
        - Discover available templates
        - List documents in a folder
        - Find documents to process

    Args:
        directory (str, optional): Directory path to scan. Defaults to current directory (".").
            Can be absolute or relative path.

    Returns:
        str: JSON array of filenames (strings): ["file1.docx", "file2.docx", ...]

    Raises:
        ValueError: If directory does not exist or is not accessible.

    Examples:
        List files in current directory:
        >>> files = docx_list_files()
        >>> import json
        >>> file_list = json.loads(files)
        >>> print(f"Found {len(file_list)} documents")

        List files in specific directory:
        >>> files = docx_list_files("./templates")
        >>> for filename in json.loads(files):
        ...     print(f"Found: {filename}")

    Notes:
        - Only returns .docx files (not .doc or other formats)
        - Returns filenames only, not full paths
        - Does not search subdirectories recursively
        - Hidden files (starting with .) are excluded

    See Also:
        - docx_create: Open discovered files
    """
    logger.debug(f"docx_list_files called: directory={directory}")

    if directory is None:
        directory = "."

    try:
        files = list_docx_files(directory)
        logger.debug(f"docx_list_files success: found {len(files)} files")
        return json.dumps(files)
    except Exception as e:
        logger.error(f"docx_list_files failed: {e}")
        raise ValueError(str(e))

def docx_extract_template_structure(session_id: str) -> str:
    """
    Extract the complete structure of a Word document template.

    Analyzes and returns a comprehensive JSON representation of the document structure,
    including headings, tables, paragraphs, and their properties. Automatically detects
    table headers based on formatting (bold text or background color).

    Typical Use Cases:
        - Analyze template structure before filling
        - Understand document layout programmatically
        - Generate documentation from templates
        - Validate template format

    Args:
        session_id (str): Active session ID returned by docx_create().

    Returns:
        str: JSON string containing document structure with metadata. Format:
            {
                "metadata": {"extracted_at": "...", "docx_version": "..."},
                "document_structure": [
                    {"type": "heading", "level": 1, "text": "...", "style": {...}},
                    {"type": "table", "rows": 5, "cols": 3, "headers": [...], ...},
                    {"type": "paragraph", "text": "...", "style": {...}}
                ]
            }

    Raises:
        ValueError: If session_id is invalid or document is empty.
        ValueError: If table header cannot be detected in strict mode.

    Examples:
        Extract template structure:
        >>> session_id = docx_create(file_path="./template.docx")
        >>> structure = docx_extract_template_structure(session_id)
        >>> import json
        >>> data = json.loads(structure)
        >>> print(f"Document has {len(data['document_structure'])} elements")

        Find all tables in structure:
        >>> data = json.loads(structure)
        >>> tables = [e for e in data['document_structure'] if e['type'] == 'table']
        >>> print(f"Found {len(tables)} tables")

    Notes:
        - Preserves element order as in original document
        - Automatically detects table headers (bold or colored background)
        - Returns complete styling information
        - Does not extract images or embedded objects

    See Also:
        - docx_read_content: Simple text extraction
        - docx_find_table: Find specific tables
    """
    from docx_mcp_server.server import session_manager

    logger.debug(f"docx_extract_template_structure called: session_id={session_id}")

    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"docx_extract_template_structure failed: Session {session_id} not found")
        raise ValueError(f"Session {session_id} not found")

    if not session.document:
        logger.error(f"docx_extract_template_structure failed: Document not found in session")
        raise ValueError("Document not found in session")

    parser = TemplateParser()
    try:
        structure = parser.extract_structure(session.document)
        element_count = len(structure.get('document_structure', []))
        logger.debug(f"docx_extract_template_structure success: extracted {element_count} elements")
        return json.dumps(structure, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"docx_extract_template_structure failed: {e}")
        raise


def register_tools(mcp: FastMCP):
    """Register content reading and search tools"""
    mcp.tool()(docx_read_content)
    mcp.tool()(docx_find_paragraphs)
    mcp.tool()(docx_list_files)
    mcp.tool()(docx_extract_template_structure)