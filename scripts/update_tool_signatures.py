#!/usr/bin/env python3
"""
Script to update tool function signatures to remove session_id parameter
and use get_active_session() helper instead.

This script automates the Phase 2 updates for the session-simplification feature.
"""

import re
import sys
from pathlib import Path

def update_function_signature(content: str, func_name: str) -> str:
    """Remove session_id parameter from function signature."""
    # Pattern to match function definition with session_id as first parameter
    pattern = rf'(def {func_name}\()session_id:\s*str,\s*'
    replacement = r'\1'
    return re.sub(pattern, replacement, content)

def update_session_access(content: str) -> str:
    """Replace session_manager.get_session() with get_active_session()."""
    # Replace import
    content = re.sub(
        r'from docx_mcp_server\.server import session_manager',
        'from docx_mcp_server.utils.session_helpers import get_active_session',
        content
    )

    # Replace session access pattern
    # Pattern 1: session = session_manager.get_session(session_id)
    #            if not session:
    #                return create_error_response(...)
    pattern1 = r'session = session_manager\.get_session\(session_id\)\s+if not session:\s+(?:logger\.error\([^)]+\)\s+)?return create_error_response\([^)]+\)'
    replacement1 = '''session, error = get_active_session()
    if error:
        return error'''
    content = re.sub(pattern1, replacement1, content, flags=re.MULTILINE | re.DOTALL)

    return content

def update_docstring_args(content: str) -> str:
    """Update docstring Args section to remove session_id."""
    # Remove session_id from Args section
    pattern = r'(\s+Args:\s*\n)\s+session_id \(str\):[^\n]+\n(?:\s+[^\n]+\n)*'

    def replacer(match):
        # Keep the "Args:" line, remove session_id and its description
        return match.group(1)

    return re.sub(pattern, replacer, content, flags=re.MULTILINE)

def update_docstring_examples(content: str) -> str:
    """Update docstring examples to remove session_id parameter."""
    # Remove session_id = docx_create() lines
    content = re.sub(
        r'>>>\s*session_id\s*=\s*docx_create\(\)\s*\n',
        '',
        content
    )

    # Remove session_id parameter from function calls
    # Pattern: function_name(session_id, ...
    content = re.sub(
        r'(docx_\w+)\(session_id,\s*',
        r'\1(',
        content
    )

    # Remove standalone session_id parameters
    content = re.sub(
        r',\s*session_id\s*\)',
        ')',
        content
    )

    return content

def update_logger_debug(content: str) -> str:
    """Remove session_id from logger.debug() calls."""
    # Remove session_id= from logger.debug
    content = re.sub(
        r'logger\.debug\(f"([^"]+):\s*session_id=\{session_id\},\s*',
        r'logger.debug(f"\1: ',
        content
    )

    return content

def update_file(file_path: Path) -> bool:
    """Update a single tool file."""
    print(f"Processing {file_path}...")

    try:
        content = file_path.read_text()
        original_content = content

        # Apply all transformations
        content = update_session_access(content)
        content = update_docstring_args(content)
        content = update_docstring_examples(content)
        content = update_logger_debug(content)

        # Check if anything changed
        if content != original_content:
            file_path.write_text(content)
            print(f"  ✓ Updated {file_path.name}")
            return True
        else:
            print(f"  - No changes needed for {file_path.name}")
            return False

    except Exception as e:
        print(f"  ✗ Error processing {file_path}: {e}")
        return False

def main():
    """Main entry point."""
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    tools_dir = project_root / "src" / "docx_mcp_server" / "tools"

    # Files to update (Phase 2 remaining tasks)
    files_to_update = [
        "table_tools.py",
        "table_rowcol_tools.py",
        "format_tools.py",
        "advanced_tools.py",
        "cursor_tools.py",
        "copy_tools.py",
        "content_tools.py",
        "composite_tools.py",
    ]

    updated_count = 0
    for filename in files_to_update:
        file_path = tools_dir / filename
        if file_path.exists():
            if update_file(file_path):
                updated_count += 1
        else:
            print(f"  ✗ File not found: {file_path}")

    print(f"\n✓ Updated {updated_count} files")
    return 0

if __name__ == "__main__":
    sys.exit(main())
