"""Test helper utilities for docx-mcp-server tests."""

from .markdown_extractors import (
    extract_session_id,
    extract_element_id,
    extract_status,
    extract_metadata_field,
    extract_all_metadata,
    is_success,
    is_error,
    extract_error_message,
    has_metadata_field,
)
from .session_helpers import (
    create_session_with_file,
    clear_active_file,
    setup_active_session,
    teardown_active_session,
)

__all__ = [
    'extract_session_id',
    'extract_element_id',
    'extract_status',
    'extract_metadata_field',
    'extract_all_metadata',
    'is_success',
    'is_error',
    'extract_error_message',
    'has_metadata_field',
    'create_session_with_file',
    'clear_active_file',
    'setup_active_session',
    'teardown_active_session',
]
