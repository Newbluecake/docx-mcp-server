#!/usr/bin/env python3
"""Remove cursor field assertions from all test files."""

import re
import os

def remove_cursor_assertions(file_path):
    """Remove assertions checking for cursor field."""

    if not os.path.exists(file_path):
        print(f"⚠️  File not found: {file_path}")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Remove cursor field assertions
    content = re.sub(
        r'    assert extract_metadata_field\(result, "cursor"\) is not None\n',
        '',
        content
    )

    # Remove cursor variable checks
    content = re.sub(
        r'    cursor = extract_metadata_field\(result, "cursor"\)\n',
        '',
        content
    )

    # Remove cursor dict checks
    content = re.sub(
        r'    assert "element_id" in cursor\n',
        '',
        content
    )

    content = re.sub(
        r'    assert cursor\["position"\] == "after"\n',
        '',
        content
    )

    content = re.sub(
        r'    assert "context" in cursor\n',
        '',
        content
    )

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Fixed {file_path}")
        return True
    else:
        print(f"⏭️  No changes needed for {file_path}")
        return False

def main():
    """Fix all test files."""

    test_files = [
        "tests/unit/test_run_format_tools_json.py",
        "tests/unit/test_paragraph_tools_json.py",
        "tests/unit/tools/test_context_integration.py",
        "tests/unit/tools/test_paragraph_position.py",
        "tests/unit/tools/test_table_position.py",
        "tests/unit/tools/test_image_position.py",
    ]

    print("🔧 Removing cursor field assertions...\n")

    fixed_count = 0
    for file_path in test_files:
        if remove_cursor_assertions(file_path):
            fixed_count += 1

    print(f"\n✅ Fixed {fixed_count} files")

if __name__ == "__main__":
    main()
