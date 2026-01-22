"""Content reading and search tools"""
import json
import logging
from mcp.server.fastmcp import FastMCP
from typing import Optional
from docx_mcp_server.core.finder import Finder, list_docx_files
from docx_mcp_server.core.template_parser import TemplateParser

logger = logging.getLogger(__name__)


def docx_read_content(
    session_id: str,
    max_paragraphs: Optional[int] = None,
    start_from: int = 0,
    include_tables: bool = False,
    return_json: bool = False,
    include_ids: bool = False
) -> str:
    """
    Read and extract text content from the document with pagination support.

    Extracts text from paragraphs in the document body, preserving order
    but not formatting. Supports limiting output to reduce token usage.

    Typical Use Cases:
        - Preview document content before modification
        - Extract text for analysis or indexing
        - Verify document content after generation
        - Read large documents in chunks

    Args:
        session_id (str): Active session ID returned by docx_create().
        max_paragraphs (int, optional): Maximum paragraphs to return. None = all.
        start_from (int, optional): Start from paragraph N (0-based). Defaults to 0.
        include_tables (bool, optional): Include table content. Defaults to False.

    Returns:
        str: Newline-separated text content of paragraphs.
            Returns "[Empty Document]" if document has no content.

    Raises:
        ValueError: If session_id is invalid or session has expired.

    Examples:
        Read all content:
        >>> content = docx_read_content(session_id)

        Read first 10 paragraphs:
        >>> content = docx_read_content(session_id, max_paragraphs=10)

        Read paragraphs 10-20:
        >>> content = docx_read_content(session_id, max_paragraphs=10, start_from=10)

    Notes:
        - Only extracts text, formatting information is not included
        - Empty paragraphs are skipped
        - Use max_paragraphs to limit token usage on large documents

    See Also:
        - docx_find_paragraphs: Search for specific text in paragraphs
        - docx_get_structure_summary: Get lightweight structure overview
    """
    from docx_mcp_server.server import session_manager

    logger.debug(f"docx_read_content called: session_id={session_id}, max={max_paragraphs}, start={start_from}")

    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"docx_read_content failed: Session {session_id} not found")
        raise ValueError(f"Session {session_id} not found")

    entries = []
    for p in session.document.paragraphs:
        if not p.text.strip():
            continue
        entry = {"text": p.text}
        if include_ids:
            entry["id"] = session._get_element_id(p, auto_register=True)
        entries.append(entry)

    # Apply pagination
    if start_from > 0:
        entries = entries[start_from:]
    if max_paragraphs is not None:
        entries = entries[:max_paragraphs]

    logger.debug(f"docx_read_content success: extracted {len(entries)} paragraphs")

    if return_json:
        return json.dumps({
            "status": "success",
            "count": len(entries),
            "data": entries
        }, ensure_ascii=False)

    result = "\n".join([e["text"] for e in entries]) if entries else "[Empty Document]"
    return result

def docx_find_paragraphs(
    session_id: str,
    query: str,
    max_results: int = 10,
    return_context: bool = False,
    case_sensitive: bool = False,
    context_span: int = 0
) -> str:
    """
    Find paragraphs containing specific text with result limiting.

    Searches through all paragraphs in the document and returns those containing
    the query text. Limits results to reduce token usage.

    Typical Use Cases:
        - Find placeholders to replace (e.g., "{{NAME}}")
        - Locate paragraphs for modification
        - Search document content programmatically

    Args:
        session_id (str): Active session ID returned by docx_create().
        query (str): Text to search for (case-insensitive substring match).
        max_results (int, optional): Maximum results to return. Defaults to 10.
        return_context (bool, optional): Include surrounding context. Defaults to False.

    Returns:
        str: JSON array of objects with paragraph IDs and text:
            [{"id": "para_xxx", "text": "paragraph content"}, ...]

    Raises:
        ValueError: If session_id is invalid or session has expired.

    Examples:
        Find placeholders (limited):
        >>> matches = docx_find_paragraphs(session_id, "{{NAME}}", max_results=5)

        Find all matches:
        >>> matches = docx_find_paragraphs(session_id, "important", max_results=999)

    Notes:
        - Search is case-insensitive
        - Results are limited to max_results to save tokens
        - Paragraphs are automatically registered for subsequent operations
        - Empty paragraphs are not searched

    See Also:
        - docx_update_paragraph_text: Modify found paragraphs
        - docx_quick_edit: Find and edit in one step
        - docx_replace_text: Replace text globally
    """
    from docx_mcp_server.server import session_manager

    logger.debug(f"docx_find_paragraphs called: session_id={session_id}, query='{query}', max={max_results}")

    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"docx_find_paragraphs failed: Session {session_id} not found")
        raise ValueError(f"Session {session_id} not found")

    matches = []
    paras = list(session.document.paragraphs)
    lowered_query = query if case_sensitive else query.lower()

    for idx, p in enumerate(paras):
        text = p.text
        hay = text if case_sensitive else text.lower()
        if lowered_query in hay:
            p_id = session.register_object(p, "para")
            entry = {"id": p_id, "text": text}

            if return_context and context_span > 0:
                before = []
                after = []
                for i in range(max(0, idx - context_span), idx):
                    before.append(paras[i].text)
                for i in range(idx + 1, min(len(paras), idx + 1 + context_span)):
                    after.append(paras[i].text)
                entry["context_before"] = before
                entry["context_after"] = after

            matches.append(entry)

            if len(matches) >= max_results:
                break

    logger.debug(f"docx_find_paragraphs success: found {len(matches)} matches (limited to {max_results})")
    return json.dumps(matches, ensure_ascii=False)

def docx_list_files(directory: Optional[str] = None, recursive: bool = False, include_meta: bool = False) -> str:
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
        files = list_docx_files(directory, recursive=recursive, include_meta=include_meta)
        logger.debug(f"docx_list_files success: found {len(files)} files")
        return json.dumps(files)
    except Exception as e:
        logger.error(f"docx_list_files failed: {e}")
        raise ValueError(str(e))

def docx_extract_template_structure(
    session_id: str,
    max_depth: int = None,
    include_content: bool = True,
    max_items_per_type: str = None
) -> str:
    """
    Extract document structure with configurable detail level.

    Analyzes and returns a JSON representation of the document structure,
    including headings, tables, paragraphs, and their properties. Supports
    limiting output to reduce token usage.

    Typical Use Cases:
        - Analyze template structure before filling
        - Understand document layout programmatically
        - Generate documentation from templates
        - Validate template format

    Args:
        session_id (str): Active session ID returned by docx_create().
        max_depth (int, optional): Limit nesting depth. None = unlimited.
        include_content (bool, optional): Include text content. Defaults to True.
        max_items_per_type (str, optional): JSON dict limiting items per type.
            Example: '{"headings": 10, "tables": 5, "paragraphs": 0}'

    Returns:
        str: JSON string containing document structure with metadata.

    Raises:
        ValueError: If session_id is invalid or document is empty.

    Examples:
        Full structure:
        >>> structure = docx_extract_template_structure(session_id)

        Structure only (no content):
        >>> structure = docx_extract_template_structure(
        ...     session_id, include_content=False
        ... )

        Limited structure:
        >>> structure = docx_extract_template_structure(
        ...     session_id,
        ...     max_items_per_type='{"headings": 10, "tables": 5, "paragraphs": 0}'
        ... )

    Notes:
        - Use max_items_per_type to significantly reduce token usage
        - include_content=False returns only structure metadata
        - Automatically detects table headers (bold or colored background)

    See Also:
        - docx_get_structure_summary: Lightweight alternative
        - docx_read_content: Simple text extraction
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
        doc_structure = structure.get('document_structure', [])

        # Apply filters if specified
        if max_items_per_type or not include_content:
            limits = json.loads(max_items_per_type) if max_items_per_type else {}

            # Count by type
            type_counts = {}
            filtered_structure = []

            for item in doc_structure:
                item_type = item.get('type')
                type_counts[item_type] = type_counts.get(item_type, 0) + 1

                # Check limit (convert 'heading' to 'headings' for lookup)
                limit_key = item_type + 's' if not item_type.endswith('s') else item_type
                limit = limits.get(limit_key, float('inf'))

                if type_counts[item_type] <= limit:
                    # Remove content if requested
                    if not include_content and 'text' in item:
                        item = item.copy()
                        item['text'] = f"[{len(item['text'])} chars]"
                    filtered_structure.append(item)

            structure['document_structure'] = filtered_structure

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
