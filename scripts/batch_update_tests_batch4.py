#!/usr/bin/env python3
"""Batch update script for fourth batch of test files."""

import ast
import re
import sys
from pathlib import Path
from typing import Tuple, Optional


def validate_syntax(content: str) -> Tuple[bool, Optional[str]]:
    """Validate Python syntax using AST parsing."""
    try:
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, f"Line {e.lineno}: {e.msg}"


def clean_orphaned_code(content: str) -> str:
    """Remove orphaned code fragments."""
    # Remove orphaned except blocks
    content = re.sub(r'\n\s+except \(json\.JSONDecodeError, KeyError\):\s+return response\s*\n', '\n', content)

    # Remove local extract functions
    content = re.sub(r'\ndef _extract_element_id\(response\):.*?(?=\ndef |\Z)', '', content, flags=re.DOTALL)
    content = re.sub(r'\ndef _extract_id\(response\):.*?(?=\ndef |\Z)', '', content, flags=re.DOTALL)
    content = re.sub(r'\ndef extract_element_id\(response\):.*?(?=\ndef |\Z)', '', content, flags=re.DOTALL)

    return content


def update_imports(content: str, file_path: Path) -> Tuple[str, bool]:
    """Add helpers import to test file."""
    if 'from helpers import' in content:
        return content, False

    # Determine correct path based on location
    is_tools_subdir = '/tools/' in str(file_path)

    # Find import section end using line-based detection with multi-line support
    lines = content.split('\n')
    import_end_line = 0
    in_multiline_import = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Check for multi-line import start
        if (stripped.startswith('import ') or stripped.startswith('from ')) and '(' in line and ')' not in line:
            in_multiline_import = True
            import_end_line = i + 1
        # Check for multi-line import end
        elif in_multiline_import and ')' in line:
            in_multiline_import = False
            import_end_line = i + 1
        # Single-line import
        elif (stripped.startswith('import ') or stripped.startswith('from ')) and not in_multiline_import:
            import_end_line = i + 1
        # Empty line in import section
        elif import_end_line > 0 and stripped == '':
            continue
        # Non-import line and not in multi-line import
        elif import_end_line > 0 and not in_multiline_import:
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

    new_lines = lines[:import_end_line] + helper_imports + lines[import_end_line:]
    return '\n'.join(new_lines), True


def apply_patterns(content: str) -> str:
    """Apply all regex patterns to update test code."""

    # Pattern 1: session_id = docx_create()
    content = re.sub(
        r'(\s+)(session_id\s*=\s*docx_create\(\))',
        r'\1session_response = docx_create()\n\1session_id = extract_session_id(session_response)',
        content
    )

    # Pattern 1b: session_id = docx_create(file_path=...)
    content = re.sub(
        r'(\s+)(session_id\s*=\s*docx_create\(file_path=[^)]+\))',
        r'\1session_response = docx_create(file_path=\2)\n\1session_id = extract_session_id(session_response)',
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

    # Pattern 4: para_id = json.loads(...)[\"data\"][\"element_id\"]
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

    # Pattern 13: data = json.loads(result) (standalone)
    content = re.sub(
        r'(\s+)data\s*=\s*json\.loads\(result\)\n',
        r'',
        content
    )

    # Pattern 14: Fix syntax warnings - missing comma before subscript
    content = re.sub(
        r'assert\s+extract_metadata_field\(result,\s*"(\w+)"\)\s+is\s+not\s+None\["(\w+)"\]',
        r'assert extract_metadata_field(result, "\1") is not None\nassert extract_metadata_field(result, "\2") is not None',
        content
    )

    return content


def update_test_file(file_path: Path) -> Tuple[bool, str]:
    """Update a test file to use Markdown extractors with validation."""
    if not file_path.exists():
        return False, f"File not found: {file_path.name}"

    content = file_path.read_text()
    original_content = content

    # Step 1: Update imports
    content, modified = update_imports(content, file_path)

    # Step 2: Apply patterns
    content = apply_patterns(content)

    # Step 3: Clean up orphaned code
    content = clean_orphaned_code(content)

    # Step 4: Validate syntax
    if content != original_content:
        is_valid, error_msg = validate_syntax(content)
        if not is_valid:
            return False, f"Syntax error in {file_path.name}: {error_msg}"

        # Write file
        file_path.write_text(content)
        return True, f"Updated {file_path.name}"
    else:
        return False, f"No changes needed for {file_path.name}"


def main():
    """Main function."""
    test_dir = Path(__file__).parent.parent / 'tests'

    # Fourth batch files - prioritize high-impact files
    files = [
        test_dir / 'unit' / 'test_paragraph_tools_json.py',
        test_dir / 'unit' / 'test_run_format_tools_json.py',
        test_dir / 'unit' / 'test_optimized_content_tools.py',
        test_dir / 'unit' / 'test_content_tools_extended.py',
        test_dir / 'unit' / 'test_element_id_enhancement.py',
        test_dir / 'unit' / 'test_extract_template_tool.py',
        test_dir / 'unit' / 'test_session_lifecycle.py',
        test_dir / 'unit' / 'test_server_lifecycle.py',
    ]

    print("Batch updating fourth batch of test files...")
    print()

    results = []
    for file_path in files:
        success, message = update_test_file(file_path)
        results.append((file_path.name, success, message))
        if success:
            print(f"  ✅ {message}")
        else:
            print(f"  ❌ {message}")

    print()
    updated_count = sum(1 for _, success, _ in results if success)
    print(f"Updated {updated_count}/{len(files)} files")

    return updated_count


if __name__ == '__main__':
    sys.exit(0 if main() > 0 else 1)
