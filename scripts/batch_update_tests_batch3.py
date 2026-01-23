#!/usr/bin/env python3
"""Batch update script for third batch of test files."""

import re
import sys
from pathlib import Path


def clean_orphaned_code(content):
    """Remove orphaned code fragments."""
    # Remove orphaned except blocks
    content = re.sub(r'\n\s+except \(json\.JSONDecodeError, KeyError\):\s+return response\s*\n', '\n', content)

    # Remove empty function definitions
    content = re.sub(r'\ndef _extract_element_id\(response\):.*?(?=\ndef |\Z)', '', content, flags=re.DOTALL)
    content = re.sub(r'\ndef _extract_id\(response\):.*?(?=\ndef |\Z)', '', content, flags=re.DOTALL)

    return content


def update_imports(content, file_path):
    """Add helpers import to test file."""
    if 'from helpers import' in content:
        return content, False

    # Determine correct path based on location
    is_tools_subdir = '/tools/' in str(file_path)

    # Find import section
    lines = content.split('\n')
    import_end = 0
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            import_end = i + 1
        elif import_end > 0 and line.strip() == '':
            continue
        elif import_end > 0:
            break

    # Determine correct path based on location
    if is_tools_subdir:
        path_insert = "sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))"
    else:
        path_insert = "sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))"

    # Insert helpers import
    helper_imports = [
        '',
        '# Add parent directory to path for helpers import',
        'import sys',
        'import os',
        path_insert,
        '',
        'from helpers import (',
        '    extract_session_id,',
        '    extract_element_id,',
        '    extract_metadata_field,',
        '    is_success,',
        '    is_error',
        ')',
    ]

    new_lines = lines[:import_end] + helper_imports + lines[import_end:]
    return '\n'.join(new_lines), True


def update_test_file(file_path: Path) -> tuple[bool, str]:
    """Update a test file to use Markdown extractors."""
    if not file_path.exists():
        return False, f"File not found: {file_path.name}"

    content = file_path.read_text()
    original_content = content

    # Update imports
    content, modified = update_imports(content, file_path)

    # Pattern 1: session_id = docx_create()
    content = re.sub(
        r'(\s+)(session_id\s*=\s*docx_create\(\))',
        r'\1session_response = docx_create()\n\1session_id = extract_session_id(session_response)',
        content
    )

    # Pattern 2: Extract element_id from nested json.loads
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

    # Pattern 4: para_id = json.loads(...)["data"]["element_id"]
    content = re.sub(
        r'(\w+_id)\s*=\s*json\.loads\(([^)]+)\)\["data"\]\["element_id"\]',
        r'\1 = extract_element_id(\2)',
        content
    )

    # Pattern 5: assert data["status"] == "success"
    content = re.sub(
        r'assert\s+data\["status"\]\s*==\s*"success"',
        r'assert is_success(result)',
        content
    )

    # Pattern 6: assert data["status"] == "error"
    content = re.sub(
        r'assert\s+data\["status"\]\s*==\s*"error"',
        r'assert is_error(result)',
        content
    )

    # Pattern 7: assert "field" in data["data"]
    content = re.sub(
        r'assert\s+"(\w+)"\s+in\s+data\["data"\]',
        r'assert extract_metadata_field(result, "\1") is not None',
        content
    )

    # Pattern 8: assert data["data"]["field"] == value
    content = re.sub(
        r'assert\s+data\["data"\]\["(\w+)"\]\s*==\s*([^\n]+)',
        r'assert extract_metadata_field(result, "\1") == \2',
        content
    )

    # Pattern 9: assert data["data"]["field"].startswith(...)
    content = re.sub(
        r'assert\s+data\["data"\]\["(\w+)"\]\.startswith\(([^)]+)\)',
        r'assert extract_metadata_field(result, "\1").startswith(\2)',
        content
    )

    # Pattern 10: Replace _extract_element_id calls
    content = re.sub(r'_extract_element_id\(', r'extract_element_id(', content)
    content = re.sub(r'_extract_id\(', r'extract_element_id(', content)

    # Pattern 11: assert result.startswith("para_")
    content = re.sub(
        r'assert\s+result\.startswith\("(\w+)_"\)',
        r'assert extract_element_id(result).startswith("\1_")',
        content
    )

    # Pattern 12: assert "para_" in result
    content = re.sub(
        r'assert\s+"(\w+)_"\s+in\s+result',
        r'assert "\1_" in extract_element_id(result)',
        content
    )

    # Clean up orphaned code
    content = clean_orphaned_code(content)

    if content != original_content:
        file_path.write_text(content)
        return True, f"Updated {file_path.name}"
    else:
        return False, f"No changes needed for {file_path.name}"


def main():
    """Main function."""
    test_dir = Path(__file__).parent.parent / 'tests'

    # Third batch files - prioritize likely quick wins
    files = [
        test_dir / 'unit' / 'test_composite_tools.py',
        test_dir / 'unit' / 'test_copy_paragraph.py',
        test_dir / 'unit' / 'test_load_existing.py',
        test_dir / 'unit' / 'test_server_content.py',
        test_dir / 'unit' / 'test_server_formatting.py',
        test_dir / 'unit' / 'test_server_tables.py',
        test_dir / 'unit' / 'tools' / 'test_batch_replace_tool.py',
        test_dir / 'unit' / 'tools' / 'test_range_copy_tool.py',
    ]

    print("🔧 Batch updating third batch of test files...")
    print()

    results = []
    for file_path in files:
        success, message = update_test_file(file_path)
        results.append((file_path.name, success, message))
        if success:
            print(f"  ✅ {message}")
        else:
            print(f"  ⏭️  {message}")

    print()
    updated_count = sum(1 for _, success, _ in results if success)
    print(f"✅ Updated {updated_count}/{len(files)} files")

    return updated_count


if __name__ == '__main__':
    sys.exit(0 if main() > 0 else 1)
