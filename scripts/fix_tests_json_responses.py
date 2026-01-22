#!/usr/bin/env python3
"""
Script to fix test files to handle JSON responses from refactored tools.
Adds helper function and updates test assertions.
"""
import re
import sys
from pathlib import Path

HELPER_FUNCTION = '''
def _extract_element_id(response):
    """Extract element_id from JSON response or return as-is if plain string."""
    try:
        data = json.loads(response)
        if isinstance(data, dict) and "data" in data and "element_id" in data["data"]:
            return data["data"]["element_id"]
        return response
    except (json.JSONDecodeError, KeyError):
        return response
'''

def add_json_import(content):
    """Add json import if not present."""
    if 'import json' not in content:
        # Add after other imports
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                continue
            else:
                lines.insert(i, 'import json')
                break
        content = '\n'.join(lines)
    return content

def add_helper_function(content):
    """Add helper function if not present."""
    if '_extract_element_id' not in content:
        # Add after imports, before first function
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('def '):
                lines.insert(i, HELPER_FUNCTION)
                break
        content = '\n'.join(lines)
    return content

def wrap_tool_calls(content):
    """Wrap tool calls that return element IDs with _extract_element_id."""
    # Pattern: variable = docx_insert_paragraph(...) or similar
    patterns = [
        (r'(\w+_id)\s*=\s*(docx_insert_paragraph\([^)]+\))', r'\1 = _extract_element_id(\2)'),
        (r'(\w+_id)\s*=\s*(docx_insert_run\([^)]+\))', r'\1 = _extract_element_id(\2)'),
        (r'(\w+_id)\s*=\s*(docx_insert_table\([^)]+\))', r'\1 = _extract_element_id(\2)'),
        (r'(\w+_id)\s*=\s*(docx_get_cell\([^)]+\))', r'\1 = _extract_element_id(\2)'),
        (r'(\w+_id)\s*=\s*(docx_get_table\([^)]+\))', r'\1 = _extract_element_id(\2)'),
        (r'(\w+_id)\s*=\s*(docx_find_table\([^)]+\))', r'\1 = _extract_element_id(\2)'),
        (r'(\w+_id)\s*=\s*(docx_copy_paragraph\([^)]+\))', r'\1 = _extract_element_id(\2)'),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    return content

def fix_error_assertions(content):
    """Fix error handling assertions to work with JSON responses."""
    # Replace try/except ValueError patterns with JSON error checking
    old_pattern = r'try:\s+(\w+)\([^)]+\)\s+assert False[^\n]+\s+except ValueError as e:\s+assert "([^"]+)" in str\(e\)'

    def replacement(match):
        call = match.group(0).split('\n')[1].strip()
        error_text = match.group(2)
        return f'''result = {call}
    try:
        data = json.loads(result)
        assert data["status"] == "error"
        assert "{error_text}" in data["message"].lower()
    except (json.JSONDecodeError, KeyError):
        assert "{error_text}" in result.lower()'''

    content = re.sub(old_pattern, replacement, content, flags=re.MULTILINE)
    return content

def main():
    test_files = [
        'tests/unit/test_copy_paragraph.py',
        'tests/unit/test_server_content.py',
        'tests/unit/test_server_core_refactor.py',
        'tests/unit/test_server_formatting.py',
        'tests/unit/test_server_tables.py',
        'tests/unit/test_tables_navigation.py',
        'tests/unit/test_replacer_image.py',
        'tests/unit/tools/test_copy_tools.py',
        'tests/unit/tools/test_context_integration.py',
        'tests/unit/tools/test_range_copy_tool.py',
    ]

    repo_root = Path(__file__).parent.parent

    for test_file in test_files:
        file_path = repo_root / test_file
        if not file_path.exists():
            print(f"Skipping {test_file} - not found")
            continue

        print(f"Processing {test_file}...")
        content = file_path.read_text()

        # Apply fixes
        content = add_json_import(content)
        content = add_helper_function(content)
        content = wrap_tool_calls(content)
        content = fix_error_assertions(content)

        # Write back
        file_path.write_text(content)
        print(f"  ✓ Fixed {test_file}")

    print("\nDone! Run tests to verify fixes.")

if __name__ == '__main__':
    main()
