#!/usr/bin/env python3
"""
Batch migration script to convert all MCP tools from legacy response functions
to create_markdown_response().

This script automates the migration of 45+ tools to use the new Markdown response format.
"""

import re
import os
from pathlib import Path

# Define the tools directory
TOOLS_DIR = Path("src/docx_mcp_server/tools")

# Files to migrate (excluding session_tools.py which is already done)
FILES_TO_MIGRATE = [
    "content_tools.py",
    "paragraph_tools.py",
    "run_tools.py",
    "table_tools.py",
    "table_rowcol_tools.py",
    "format_tools.py",
    "advanced_tools.py",
    "cursor_tools.py",
    "copy_tools.py",
    "composite_tools.py",
    "system_tools.py",
    "history_tools.py",
]

# Patterns to replace
PATTERNS = [
    # Replace create_success_response with create_markdown_response
    (
        r'return create_success_response\(\s*message="([^"]+)"',
        r'return create_markdown_response(\n            session=session,\n            message="\1",\n            operation="Operation",\n            show_context=False'
    ),
    # Replace create_context_aware_response with create_markdown_response
    (
        r'return create_context_aware_response\(\s*session,\s*message="([^"]+)"',
        r'return create_markdown_response(\n            session=session,\n            message="\1",\n            operation="Operation",\n            show_context=True'
    ),
    # Update imports
    (
        r'from docx_mcp_server\.core\.response import \(\s*create_context_aware_response,\s*create_error_response,\s*create_success_response\s*\)',
        'from docx_mcp_server.core.response import (\n    create_markdown_response,\n    create_error_response\n)'
    ),
    (
        r'from docx_mcp_server\.core\.response import \(\s*create_success_response,\s*create_error_response\s*\)',
        'from docx_mcp_server.core.response import (\n    create_markdown_response,\n    create_error_response\n)'
    ),
]


def migrate_file(file_path: Path):
    """Migrate a single file to use create_markdown_response."""
    print(f"Migrating {file_path.name}...")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Apply all patterns
    for pattern, replacement in PATTERNS:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ {file_path.name} migrated")
        return True
    else:
        print(f"  - {file_path.name} no changes needed")
        return False


def main():
    """Main migration function."""
    print("=" * 60)
    print("MCP Tools Migration Script")
    print("Converting to Markdown response format")
    print("=" * 60)
    print()

    migrated_count = 0
    skipped_count = 0

    for filename in FILES_TO_MIGRATE:
        file_path = TOOLS_DIR / filename
        if file_path.exists():
            if migrate_file(file_path):
                migrated_count += 1
            else:
                skipped_count += 1
        else:
            print(f"  ! {filename} not found, skipping")
            skipped_count += 1

    print()
    print("=" * 60)
    print(f"Migration complete!")
    print(f"  Migrated: {migrated_count} files")
    print(f"  Skipped: {skipped_count} files")
    print("=" * 60)
    print()
    print("Note: This script performs basic pattern matching.")
    print("Manual review and testing is recommended.")


if __name__ == "__main__":
    main()
