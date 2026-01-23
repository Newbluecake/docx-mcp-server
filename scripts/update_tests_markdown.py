#!/usr/bin/env python3
"""Script to update test files to use Markdown extractors."""

import re
import sys
from pathlib import Path


def update_test_file(file_path: Path) -> bool:
    """Update a test file to use Markdown extractors.

    Args:
        file_path: Path to test file

    Returns:
        True if file was modified, False otherwise
    """
    content = file_path.read_text()
    original_content = content
    modified = False

    # Check if file already uses helpers
    if 'from tests.helpers' in content or 'from helpers' in content:
        print(f"  ⏭️  {file_path.name} already uses helpers, skipping")
        return False

    # Add import statement after existing imports
    import_pattern = r'(import json\nimport pytest\n)'
    if re.search(import_pattern, content):
        replacement = r'\1from tests.helpers import (\n    extract_session_id,\n    extract_element_id,\n    extract_metadata_field,\n    is_success,\n    is_error\n)\n'
        content = re.sub(import_pattern, replacement, content)
        modified = True
    else:
        # Try alternative pattern
        import_pattern = r'(import pytest\n)'
        if re.search(import_pattern, content):
            replacement = r'\1from tests.helpers import (\n    extract_session_id,\n    extract_element_id,\n    extract_metadata_field,\n    is_success,\n    is_error\n)\n'
            content = re.sub(import_pattern, replacement, content)
            modified = True

    # Replace docx_create() calls to extract session_id
    # Pattern: session_id = docx_create()
    pattern1 = r'(\s+)(session_id\s*=\s*docx_create\(\))'
    replacement1 = r'\1session_response = docx_create()\n\1session_id = extract_session_id(session_response)'
    if re.search(pattern1, content):
        content = re.sub(pattern1, replacement1, content)
        modified = True

    # Replace JSON parsing patterns
    # Pattern: data = json.loads(result)
    #          table_id = data["data"]["element_id"]
    pattern2 = r'(\s+)result\s*=\s*docx_insert_table\([^)]+\)\n\s+data\s*=\s*json\.loads\(result\)\n\s+table_id\s*=\s*data\["data"\]\["element_id"\]'
    replacement2 = r'\1result = docx_insert_table(\2)\n\1table_id = extract_element_id(result)'
    # This is complex, let's do it step by step

    # Replace: data = json.loads(result)
    #          assert data["status"] == "success"
    # With: assert is_success(result)
    pattern3 = r'(\s+)data\s*=\s*json\.loads\(result\)\n\s+assert\s+data\["status"\]\s*==\s*"success"'
    replacement3 = r'\1assert is_success(result)'
    if re.search(pattern3, content):
        content = re.sub(pattern3, replacement3, content)
        modified = True

    # Replace: data["data"]["field_name"]
    # With: extract_metadata_field(result, "field_name")
    # This is tricky because we need to track the result variable

    if modified:
        file_path.write_text(content)
        print(f"  ✅ Updated {file_path.name}")
        return True
    else:
        print(f"  ⏭️  {file_path.name} - no patterns matched")
        return False


def main():
    """Main function."""
    if len(sys.argv) > 1:
        test_files = [Path(f) for f in sys.argv[1:]]
    else:
        # Default: update priority test files
        test_dir = Path(__file__).parent.parent / 'tests' / 'unit'
        test_files = [
            test_dir / 'test_table_rowcol_tools.py',
            test_dir / 'test_table_tools_json.py',
            test_dir / 'test_tables_navigation.py',
        ]

    print("🔧 Updating test files to use Markdown extractors...")
    print()

    updated_count = 0
    for file_path in test_files:
        if not file_path.exists():
            print(f"  ❌ {file_path.name} not found")
            continue

        if update_test_file(file_path):
            updated_count += 1

    print()
    print(f"✅ Updated {updated_count}/{len(test_files)} files")


if __name__ == '__main__':
    main()
