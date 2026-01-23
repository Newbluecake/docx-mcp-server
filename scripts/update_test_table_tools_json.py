#!/usr/bin/env python3
"""Script to update test_table_tools_json.py to use Markdown extractors."""

import re
from pathlib import Path


def update_test_table_tools_json():
    """Update test_table_tools_json.py file."""
    file_path = Path(__file__).parent.parent / 'tests' / 'unit' / 'test_table_tools_json.py'

    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False

    content = file_path.read_text()
    original_content = content

    # Add imports
    import_section = """import json
import pytest
import sys
import os

# Add parent directory to path for helpers import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from docx_mcp_server.tools.table_tools import (
    docx_insert_table,
    docx_get_table,
    docx_find_table,
    docx_get_cell,
    docx_insert_paragraph_to_cell,
    docx_insert_table_row,
    docx_insert_table_col,
    docx_fill_table,
    docx_copy_table
)
from docx_mcp_server.tools.session_tools import docx_create, docx_close
from helpers import (
    extract_session_id,
    extract_element_id,
    extract_metadata_field,
    is_success,
    is_error
)"""

    # Replace import section
    old_import = re.search(r'^""".*?""".*?from docx_mcp_server\.tools\.session_tools import.*?\n', content, re.DOTALL)
    if old_import:
        content = content[:old_import.start()] + import_section + '\n' + content[old_import.end():]

    # Pattern 1: session_id = docx_create()
    content = re.sub(
        r'(\s+)(session_id\s*=\s*docx_create\(\))',
        r'\1session_response = docx_create()\n\1session_id = extract_session_id(session_response)',
        content
    )

    # Pattern 2: Extract element_id from nested json.loads
    # table_id = json.loads(docx_insert_table(...))[\"data\"][\"element_id\"]
    content = re.sub(
        r'(\w+)\s*=\s*json\.loads\((docx_\w+\([^)]+\))\)\["data"\]\["element_id"\]',
        r'\1 = extract_element_id(\2)',
        content
    )

    # Pattern 3: result = ...; data = json.loads(result)
    content = re.sub(
        r'(\s+)(result\s*=\s*docx_\w+\([^)]+\))\n\s+data\s*=\s*json\.loads\(result\)\n',
        r'\1\2\n',
        content
    )

    # Pattern 4: assert data["status"] == "success"
    content = re.sub(
        r'assert\s+data\["status"\]\s*==\s*"success"',
        r'assert is_success(result)',
        content
    )

    # Pattern 5: assert data["status"] == "error"
    content = re.sub(
        r'assert\s+data\["status"\]\s*==\s*"error"',
        r'assert is_error(result)',
        content
    )

    # Pattern 6: assert "field" in data["data"]
    content = re.sub(
        r'assert\s+"(\w+)"\s+in\s+data\["data"\]',
        r'assert extract_metadata_field(result, "\1") is not None',
        content
    )

    # Pattern 7: assert data["data"]["field"] == value
    content = re.sub(
        r'assert\s+data\["data"\]\["(\w+)"\]\s*==\s*([^\n]+)',
        r'assert extract_metadata_field(result, "\1") == \2',
        content
    )

    # Pattern 8: assert data["data"]["field"].startswith(...)
    content = re.sub(
        r'assert\s+data\["data"\]\["(\w+)"\]\.startswith\(([^)]+)\)',
        r'assert extract_metadata_field(result, "\1").startswith(\2)',
        content
    )

    if content != original_content:
        file_path.write_text(content)
        print(f"✅ Updated {file_path.name}")
        return True
    else:
        print(f"⏭️  {file_path.name} - no changes needed")
        return False


if __name__ == '__main__':
    update_test_table_tools_json()
