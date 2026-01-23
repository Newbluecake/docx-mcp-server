#!/usr/bin/env python3
"""Fix CI test failures after Markdown migration."""

import re
import os
from pathlib import Path

def fix_test_content_tools_extended():
    """Fix test_content_tools_extended.py to extract session_id."""
    file_path = "tests/unit/test_content_tools_extended.py"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix: sid = docx_create() -> sid = extract_session_id(docx_create())
    content = re.sub(
        r'(\s+)sid = docx_create\(\)',
        r'\1sid = extract_session_id(docx_create())',
        content
    )

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ Fixed {file_path}")

def fix_log_level_tools():
    """Add missing import to log_level_tools.py."""
    file_path = "src/docx_mcp_server/tools/log_level_tools.py"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if import already exists
    if 'from docx_mcp_server.core.response import' in content:
        print(f"⏭️  {file_path} already has imports")
        return

    # Add import after other imports
    import_line = "from docx_mcp_server.core.response import create_markdown_response, create_error_response\n"

    # Find the last import line
    lines = content.split('\n')
    last_import_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            last_import_idx = i

    lines.insert(last_import_idx + 1, import_line)
    content = '\n'.join(lines)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ Fixed {file_path}")

def fix_paragraph_tools_heading():
    """Fix docx_insert_heading in paragraph_tools.py."""
    file_path = "src/docx_mcp_server/tools/paragraph_tools.py"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace create_success_response with create_markdown_response in docx_insert_heading
    content = re.sub(
        r'(def docx_insert_heading.*?)(create_success_response\()',
        lambda m: m.group(1) + 'create_markdown_response(\n        session=session,\n        ',
        content,
        flags=re.DOTALL
    )

    # Fix the parameters
    content = re.sub(
        r'create_markdown_response\(\s*session=session,\s*message="Heading created successfully",\s*element_id=h_id\)',
        '''create_markdown_response(
        session=session,
        message="Heading created successfully",
        element_id=h_id,
        operation="Insert Heading",
        show_context=True,
        level=level
    )''',
        content
    )

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ Fixed {file_path}")

def main():
    """Run all fixes."""
    print("🔧 Fixing CI failures...")
    print()

    try:
        fix_test_content_tools_extended()
        fix_log_level_tools()
        fix_paragraph_tools_heading()

        print()
        print("✅ All fixes applied successfully!")
        print()
        print("Next steps:")
        print("1. Run tests locally: pytest tests/unit/ -v")
        print("2. Commit and push: git add . && git commit -m 'fix: CI test failures' && git push")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
