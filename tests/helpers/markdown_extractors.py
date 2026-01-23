"""Helper functions for extracting data from Markdown responses.

These helpers are used across all test files to extract structured data
from Markdown-formatted tool responses.
"""

import re
import json
from typing import Optional, Dict, Any


def extract_session_id(response: str) -> Optional[str]:
    """Extract session_id from Markdown response.

    Args:
        response: Markdown response string

    Returns:
        Session ID string or None if not found

    Example:
        >>> response = "**Session ID**: abc123\\n..."
        >>> extract_session_id(response)
        'abc123'
    """
    # Try to extract from Markdown format: **Session ID**: xxx
    match = re.search(r'\*\*Session ID\*\*:\s*(\S+)', response)
    if match:
        return match.group(1)

    # Legacy/Fallback: try **Session Id** (case insensitive)
    match = re.search(r'\*\*Session Id\*\*:\s*(\S+)', response, re.IGNORECASE)
    if match:
        return match.group(1)

    # Fallback: return as-is if it looks like a session ID (short alphanumeric string)
    if isinstance(response, str) and len(response) < 100 and '\n' not in response:
        return response.strip()

    return None


def extract_element_id(response: str) -> Optional[str]:
    """Extract element_id from Markdown response.

    Args:
        response: Markdown response string

    Returns:
        Element ID string or None if not found

    Example:
        >>> response = "**Element ID**: para_abc123\\n..."
        >>> extract_element_id(response)
        'para_abc123'
    """
    # Try to extract from Markdown format: **Element ID**: para_xxx
    match = re.search(r'\*\*Element ID\*\*:\s*(\w+)', response)
    if match:
        return match.group(1)

    # Fallback: try JSON format (legacy compatibility)
    try:
        data = json.loads(response)
        if isinstance(data, dict) and "data" in data and "element_id" in data["data"]:
            return data["data"]["element_id"]
    except (json.JSONDecodeError, KeyError, TypeError):
        pass

    return response if isinstance(response, str) and response.startswith(('para_', 'run_', 'table_', 'cell_')) else None


def extract_status(response: str) -> str:
    """Extract status from Markdown response.

    Args:
        response: Markdown response string

    Returns:
        "success" or "error"

    Example:
        >>> response = "**Status**: ✅ Success\\n..."
        >>> extract_status(response)
        'success'
    """
    # Try Markdown format
    if '✅ Success' in response or '**Status**: success' in response.lower():
        return 'success'
    if '❌ Error' in response or '**Status**: error' in response.lower():
        return 'error'

    # Fallback: try JSON format
    try:
        data = json.loads(response)
        if isinstance(data, dict) and "status" in data:
            return data["status"]
    except (json.JSONDecodeError, KeyError, TypeError):
        pass

    return 'unknown'


def _snake_to_title_case(snake_str: str) -> str:
    """Convert snake_case to Title Case, preserving acronyms.

    Args:
        snake_str: Snake case string (e.g., "element_id", "new_row_count")

    Returns:
        Title case string with acronyms preserved (e.g., "Element ID", "New Row Count")
    """
    # Special cases for acronyms that should stay uppercase
    acronyms = {'id': 'ID', 'url': 'URL', 'html': 'HTML', 'xml': 'XML', 'api': 'API'}

    words = snake_str.split('_')
    title_words = []
    for word in words:
        if word.lower() in acronyms:
            title_words.append(acronyms[word.lower()])
        else:
            title_words.append(word.capitalize())

    return ' '.join(title_words)


def extract_metadata_field(response: str, field_name: str) -> Optional[Any]:
    """Extract a specific metadata field from Markdown response.

    Args:
        response: Markdown response string
        field_name: Field name to extract (e.g., "new_row_count", "inserted_at", "element_id")

    Returns:
        Field value or None if not found

    Example:
        >>> response = "**New Row Count**: 4\\n..."
        >>> extract_metadata_field(response, "new_row_count")
        '4'
        >>> response = "**Element ID**: para_123\\n..."
        >>> extract_metadata_field(response, "element_id")
        'para_123'
    """
    # Convert snake_case to Title Case for Markdown format
    display_name = _snake_to_title_case(field_name)

    # Try to extract from Markdown format: **Field Name**: value
    pattern = rf'\*\*{re.escape(display_name)}\*\*:\s*(.+?)(?:\n|$)'
    match = re.search(pattern, response)
    if match:
        value = match.group(1).strip()
        # Try to convert to appropriate type
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value

    # Fallback: try JSON format
    try:
        data = json.loads(response)
        if isinstance(data, dict) and "data" in data and field_name in data["data"]:
            return data["data"][field_name]
    except (json.JSONDecodeError, KeyError, TypeError):
        pass

    return None


def extract_all_metadata(response: str) -> Dict[str, Any]:
    """Extract all metadata fields from Markdown response.

    Args:
        response: Markdown response string

    Returns:
        Dictionary of all metadata fields

    Example:
        >>> response = "**Element ID**: para_123\\n**New Row Count**: 4\\n..."
        >>> extract_all_metadata(response)
        {'element_id': 'para_123', 'new_row_count': 4}
    """
    metadata = {}

    # Extract common fields
    element_id = extract_element_id(response)
    if element_id:
        metadata['element_id'] = element_id

    session_id = extract_session_id(response)
    if session_id:
        metadata['session_id'] = session_id

    # Extract all **Field**: value patterns
    pattern = r'\*\*([^*]+)\*\*:\s*(.+?)(?:\n|$)'
    for match in re.finditer(pattern, response):
        field_name = match.group(1).strip()
        value = match.group(2).strip()

        # Convert field name to snake_case
        key = field_name.lower().replace(' ', '_')

        # Skip already extracted fields
        if key in ('element_id', 'session_id', 'status', 'operation'):
            continue

        # Try to convert to appropriate type
        if value.lower() in ('true', 'false'):
            metadata[key] = value.lower() == 'true'
        else:
            try:
                metadata[key] = int(value)
            except ValueError:
                try:
                    metadata[key] = float(value)
                except ValueError:
                    metadata[key] = value

    return metadata


def is_success(response: str) -> bool:
    """Check if response indicates success.

    Args:
        response: Markdown response string

    Returns:
        True if success, False otherwise
    """
    return extract_status(response) == 'success'


def is_error(response: str) -> bool:
    """Check if response indicates error.

    Args:
        response: Markdown response string

    Returns:
        True if error, False otherwise
    """
    return extract_status(response) == 'error'


def extract_error_message(response: str) -> Optional[str]:
    """Extract error message from Markdown response.

    Args:
        response: Markdown response string

    Returns:
        Error message or None if not found
    """
    # Try Markdown format: **Message**: error text
    match = re.search(r'\*\*Message\*\*:\s*(.+?)(?:\n|$)', response)
    if match:
        return match.group(1).strip()

    # Fallback: try JSON format
    try:
        data = json.loads(response)
        if isinstance(data, dict) and "message" in data:
            return data["message"]
    except (json.JSONDecodeError, KeyError, TypeError):
        pass

    return None


def has_metadata_field(response: str, field_name: str) -> bool:
    """Check if a metadata field exists in Markdown response.

    Args:
        response: Markdown response string
        field_name: Field name to check

    Returns:
        True if field exists, False otherwise
    """
    return extract_metadata_field(response, field_name) is not None
