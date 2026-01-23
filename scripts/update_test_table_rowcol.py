#!/usr/bin/env python3
"""Script to batch update test_table_rowcol_tools.py to use Markdown extractors."""

import re
from pathlib import Path


def update_test_table_rowcol_tools():
    """Update test_table_rowcol_tools.py file."""
    file_path = Path(__file__).parent.parent / 'tests' / 'unit' / 'test_table_rowcol_tools.py'

    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False

    content = file_path.read_text()
    original_content = content

    # Pattern 1: Replace session_id = docx_create()
    pattern1 = r'(\s+)(session_id\s*=\s*docx_create\(\))'
    replacement1 = r'\1session_response = docx_create()\n\1session_id = extract_session_id(session_response)'
    content = re.sub(pattern1, replacement1, content)

    # Pattern 2: Replace table creation and ID extraction
    # From:
    #   result = docx_insert_table(session_id, 3, 3, "end:document_body")
    #   data = json.loads(result)
    #   table_id = data["data"]["element_id"]
    # To:
    #   result = docx_insert_table(session_id, 3, 3, "end:document_body")
    #   table_id = extract_element_id(result)
    pattern2 = r'(\s+)(result\s*=\s*docx_insert_table\([^)]+\))\n\s+data\s*=\s*json\.loads\(result\)\n\s+table_id\s*=\s*data\["data"\]\["element_id"\]'
    replacement2 = r'\1\2\n\1table_id = extract_element_id(result)'
    content = re.sub(pattern2, replacement2, content)

    # Pattern 3: Replace result parsing and assertions
    # From:
    #   result = docx_insert_row_at(...)
    #   data = json.loads(result)
    #
    #   assert data["status"] == "success"
    #   assert data["data"]["new_row_count"] == 4
    # To:
    #   result = docx_insert_row_at(...)
    #
    #   assert is_success(result)
    #   assert extract_metadata_field(result, "new_row_count") == 4

    # First, remove data = json.loads(result) lines after tool calls
    pattern3a = r'(\s+)(result\s*=\s*docx_(?:insert_row_at|insert_col_at|delete_row|delete_col)\([^)]+\))\n\s+data\s*=\s*json\.loads\(result\)\n'
    replacement3a = r'\1\2\n'
    content = re.sub(pattern3a, replacement3a, content)

    # Replace assert data["status"] == "success"
    pattern3b = r'assert\s+data\["status"\]\s*==\s*"success"'
    replacement3b = r'assert is_success(result)'
    content = re.sub(pattern3b, replacement3b, content)

    # Replace assert data["status"] == "error"
    pattern3c = r'assert\s+data\["status"\]\s*==\s*"error"'
    replacement3c = r'assert is_error(result)'
    content = re.sub(pattern3c, replacement3c, content)

    # Replace assert data["data"]["field_name"] == value
    # This is more complex, need to handle various field names
    fields = [
        'new_row_count', 'new_col_count', 'inserted_at', 'copy_format',
        'error_type', 'deleted_row_index', 'deleted_col_index',
        'new_row_count', 'cleaned_cell_ids'
    ]

    for field in fields:
        # Pattern for == comparison
        pattern = rf'assert\s+data\["data"\]\["{field}"\]\s*==\s*([^\n]+)'
        replacement = rf'assert extract_metadata_field(result, "{field}") == \1'
        content = re.sub(pattern, replacement, content)

        # Pattern for is comparison (for booleans)
        pattern = rf'assert\s+data\["data"\]\["{field}"\]\s+is\s+([^\n]+)'
        replacement = rf'assert extract_metadata_field(result, "{field}") is \1'
        content = re.sub(pattern, replacement, content)

        # Pattern for > comparison
        pattern = rf'assert\s+data\["data"\]\["{field}"\]\s*>\s*([^\n]+)'
        replacement = rf'assert extract_metadata_field(result, "{field}") > \1'
        content = re.sub(pattern, replacement, content)

    if content != original_content:
        file_path.write_text(content)
        print(f"✅ Updated {file_path.name}")
        return True
    else:
        print(f"⏭️  {file_path.name} - no changes needed")
        return False


if __name__ == '__main__':
    update_test_table_rowcol_tools()
