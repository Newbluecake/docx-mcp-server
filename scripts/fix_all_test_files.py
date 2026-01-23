#!/usr/bin/env python3
"""Fix all test files to work with Markdown responses."""

import re
import os
from pathlib import Path

def fix_common_patterns(content):
    """Apply common fixes to test file content."""

    # Fix: sid = docx_create() -> sid = extract_session_id(docx_create())
    content = re.sub(
        r'(\s+)sid = docx_create\(\)',
        r'\1sid = extract_session_id(docx_create())',
        content
    )

    # Fix: session_id = docx_create() -> session_id = extract_session_id(docx_create())
    # But only if not already wrapped
    content = re.sub(
        r'(\s+)session_id = docx_create\((.*?)\)(?!\))',
        lambda m: f'{m.group(1)}session_id = extract_session_id(docx_create({m.group(2)}))',
        content
    )

    # Fix: result = json.loads(docx_...) -> result = docx_...
    content = re.sub(
        r'result = json\.loads\((docx_\w+\([^)]+\))\)',
        r'result = \1',
        content
    )

    # Fix: data = json.loads(result) followed by data["data"]["element_id"]
    # Replace with extract_element_id(result)
    content = re.sub(
        r'data = json\.loads\(result\)\s+(\w+)_id = data\["data"\]\["element_id"\]',
        r'\1_id = extract_element_id(result)',
        content
    )

    # Fix: para_id = data["data"]["element_id"] -> para_id = extract_element_id(result)
    content = re.sub(
        r'(\w+)_id = data\["data"\]\["element_id"\]',
        r'\1_id = extract_element_id(result)',
        content
    )

    # Fix: assert data["status"] == "success" -> assert is_success(result)
    content = re.sub(
        r'assert data\["status"\] == "success"',
        r'assert is_success(result)',
        content
    )

    # Fix: assert data["status"] == "error" -> assert is_error(result)
    content = re.sub(
        r'assert data\["status"\] == "error"',
        r'assert is_error(result)',
        content
    )

    # Fix: data["data"]["field"] -> extract_metadata_field(result, "field")
    content = re.sub(
        r'data\["data"\]\["(\w+)"\]',
        r'extract_metadata_field(result, "\1")',
        content
    )

    # Fix: assert "text" in result -> assert "text" in result (keep as is for string checks)
    # But fix: assert result["data"]["field"] -> assert extract_metadata_field(result, "field")
    content = re.sub(
        r'result\["data"\]\["(\w+)"\]',
        r'extract_metadata_field(result, "\1")',
        content
    )

    return content

def ensure_imports(content):
    """Ensure helper imports are present."""

    # Check if helpers import exists
    if 'from helpers import' not in content:
        # Add import after other imports
        import_block = '''
# Add parent directory to path for helpers import
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from helpers import (
    extract_session_id,
    extract_element_id,
    extract_metadata_field,
    extract_error_message,
    is_success,
    is_error
)
'''
        # Insert after first docstring or at beginning
        if '"""' in content:
            parts = content.split('"""', 2)
            if len(parts) >= 3:
                content = parts[0] + '"""' + parts[1] + '"""' + import_block + parts[2]
        else:
            content = import_block + content
    else:
        # Ensure all helpers are imported
        if 'extract_error_message' not in content:
            content = re.sub(
                r'from helpers import \((.*?)\)',
                lambda m: f'from helpers import ({m.group(1).rstrip()},\n    extract_error_message\n)',
                content,
                flags=re.DOTALL
            )

    return content

def fix_file(file_path):
    """Fix a single test file."""

    print(f"Processing {file_path}...")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Apply fixes
    content = ensure_imports(content)
    content = fix_common_patterns(content)

    # Only write if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ Fixed {file_path}")
        return True
    else:
        print(f"  ⏭️  No changes needed for {file_path}")
        return False

def main():
    """Fix all failing test files."""

    failing_files = [
        "tests/unit/test_cursor_advanced_tools_json.py",
        "tests/unit/test_element_id_enhancement.py",
        "tests/unit/test_replacer_image.py",
        "tests/unit/test_response_tracking.py",
        "tests/unit/test_run_format_tools_json.py",
        "tests/unit/test_session_id_length.py",
        "tests/unit/test_session_lifecycle.py",
        "tests/unit/test_table_list_and_content_anchor.py",
        "tests/unit/test_table_tools_json.py",
        "tests/unit/tools/test_batch_replace_tool.py",
        "tests/unit/tools/test_context_integration.py",
        "tests/unit/tools/test_image_position.py",
        "tests/unit/tools/test_paragraph_position.py",
        "tests/unit/tools/test_table_position.py",
    ]

    fixed_count = 0
    for file_path in failing_files:
        if os.path.exists(file_path):
            if fix_file(file_path):
                fixed_count += 1
        else:
            print(f"  ⚠️  File not found: {file_path}")

    print(f"\n✅ Fixed {fixed_count} files")

if __name__ == "__main__":
    main()
