#!/usr/bin/env python3
"""Batch update remaining priority test files."""

import re
import sys
from pathlib import Path


def update_imports(content):
    """Add helpers import to test file."""
    if 'from helpers import' in content or 'from tests.helpers import' in content:
        return content, False

    # Find the last import statement
    import_lines = []
    other_lines = []
    in_imports = True

    for line in content.split('\n'):
        if in_imports and (line.startswith('import ') or line.startswith('from ')):
            import_lines.append(line)
        elif in_imports and line.strip() == '':
            import_lines.append(line)
        else:
            in_imports = False
            other_lines.append(line)

    # Add sys.path and helpers import
    new_imports = import_lines + [
        '',
        '# Add parent directory to path for helpers import',
        'import sys',
        'import os',
        'sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), \'..\')))',
        '',
        'from helpers import (',
        '    extract_session_id,',
        '    extract_element_id,',
        '    extract_metadata_field,',
        '    is_success,',
        '    is_error',
        ')',
    ]

    return '\n'.join(new_imports + other_lines), True


def update_test_file(file_path: Path) -> bool:
    """Update a test file to use Markdown extractors."""
    if not file_path.exists():
        print(f"  ❌ {file_path.name} not found")
        return False

    content = file_path.read_text()
    original_content = content

    # Update imports
    content, modified = update_imports(content)

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

    # Pattern 8: Replace local _extract_element_id function
    content = re.sub(
        r'def _extract_element_id\(response\):.*?return response',
        '',
        content,
        flags=re.DOTALL
    )

    # Pattern 9: Replace _extract_element_id calls
    content = re.sub(r'_extract_element_id\(', r'extract_element_id(', content)

    if content != original_content:
        file_path.write_text(content)
        print(f"  ✅ Updated {file_path.name}")
        return True
    else:
        print(f"  ⏭️  {file_path.name} - no changes needed")
        return False


def main():
    """Main function."""
    test_dir = Path(__file__).parent.parent / 'tests'

    # Priority files to update
    files = [
        test_dir / 'unit' / 'tools' / 'test_context_integration.py',
        test_dir / 'unit' / 'test_paragraph_tools_json.py',
        test_dir / 'unit' / 'test_run_format_tools_json.py',
    ]

    print("🔧 Batch updating test files...")
    print()

    updated_count = 0
    for file_path in files:
        if update_test_file(file_path):
            updated_count += 1

    print()
    print(f"✅ Updated {updated_count}/{len(files)} files")


if __name__ == '__main__':
    main()
