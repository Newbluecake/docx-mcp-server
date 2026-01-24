#!/usr/bin/env python3
"""
Script to add special ID error handling to all tool files.

This script wraps session.get_object() calls with try-except blocks
to catch ValueError from special ID resolution failures.
"""

import re
import sys
from pathlib import Path

# Pattern to match session.get_object() calls
PATTERN = r'(\s+)(\w+)\s*=\s*session\.get_object\(([^)]+)\)\s*\n(\s+)if not \2:'

# Replacement template
REPLACEMENT = r'''\1try:
\1    \2 = session.get_object(\3)
\1except ValueError as e:
\1    if "Special ID" in str(e) or "not available" in str(e):
\1        return create_error_response(str(e), error_type="SpecialIDNotAvailable")
\1    raise

\4if not \2:'''

def process_file(file_path):
    """Process a single file to add error handling."""
    print(f"Processing {file_path}...")

    with open(file_path, 'r') as f:
        content = f.read()

    # Count matches
    matches = list(re.finditer(PATTERN, content))
    if not matches:
        print(f"  No patterns found in {file_path}")
        return 0

    print(f"  Found {len(matches)} patterns to update")

    # Apply replacement
    new_content = re.sub(PATTERN, REPLACEMENT, content)

    # Write back
    with open(file_path, 'w') as f:
        f.write(new_content)

    print(f"  Updated {file_path}")
    return len(matches)

def main():
    # List of tool files to process
    tool_files = [
        "src/docx_mcp_server/tools/format_tools.py",
        "src/docx_mcp_server/tools/table_tools.py",
        "src/docx_mcp_server/tools/table_rowcol_tools.py",
        "src/docx_mcp_server/tools/advanced_tools.py",
        "src/docx_mcp_server/tools/copy_tools.py",
        "src/docx_mcp_server/tools/cursor_tools.py",
        "src/docx_mcp_server/tools/composite_tools.py",
        "src/docx_mcp_server/tools/content_tools.py",
    ]

    total_updates = 0
    for file_path in tool_files:
        path = Path(file_path)
        if path.exists():
            updates = process_file(path)
            total_updates += updates
        else:
            print(f"Warning: {file_path} not found")

    print(f"\nTotal updates: {total_updates}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
