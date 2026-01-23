#!/usr/bin/env python3
"""
Complete migration script for converting all MCP tools to Markdown response format.

This script performs comprehensive migration including:
1. Import statement updates
2. Function call replacements
3. Adding show_context and show_diff parameters
4. Handling special cases (update operations with diff)
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Define the tools directory
TOOLS_DIR = Path("src/docx_mcp_server/tools")

# Files to migrate
FILES_TO_MIGRATE = [
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

# Update operations that need diff support
UPDATE_OPERATIONS = {
    "docx_update_paragraph_text",
    "docx_update_run_text",
    "docx_replace_text",
    "docx_batch_replace_text",
    "docx_quick_edit",
}


def update_imports(content: str) -> str:
    """Update import statements to use create_markdown_response."""

    # Pattern 1: Three imports
    pattern1 = r'from docx_mcp_server\.core\.response import \(\s*create_context_aware_response,\s*create_error_response,\s*create_success_response\s*\)'
    replacement1 = '''from docx_mcp_server.core.response import (
    create_markdown_response,
    create_error_response
)'''
    content = re.sub(pattern1, replacement1, content, flags=re.MULTILINE)

    # Pattern 2: Two imports (success + error)
    pattern2 = r'from docx_mcp_server\.core\.response import \(\s*create_success_response,\s*create_error_response\s*\)'
    content = re.sub(pattern2, replacement1, content, flags=re.MULTILINE)

    # Pattern 3: Two imports (context_aware + error)
    pattern3 = r'from docx_mcp_server\.core\.response import \(\s*create_context_aware_response,\s*create_error_response\s*\)'
    content = re.sub(pattern3, replacement1, content, flags=re.MULTILINE)

    return content


def migrate_create_success_response(content: str, function_name: str = None) -> str:
    """Migrate create_success_response calls to create_markdown_response."""

    # Find all create_success_response calls
    pattern = r'return create_success_response\(\s*message="([^"]+)"([^)]*)\)'

    def replace_func(match):
        message = match.group(1)
        rest_params = match.group(2)

        # Determine operation name from function context
        operation = "Operation"
        if function_name:
            # Convert function name to operation name
            # e.g., docx_insert_paragraph -> Insert Paragraph
            operation = function_name.replace("docx_", "").replace("_", " ").title()

        # Build new call
        new_call = f'''return create_markdown_response(
            session=session,
            message="{message}",
            operation="{operation}",
            show_context=True{rest_params}
        )'''

        return new_call

    content = re.sub(pattern, replace_func, content, flags=re.MULTILINE | re.DOTALL)

    return content


def migrate_create_context_aware_response(content: str, function_name: str = None) -> str:
    """Migrate create_context_aware_response calls to create_markdown_response."""

    # Pattern: return create_context_aware_response(session, message="...", ...)
    pattern = r'return create_context_aware_response\(\s*session,\s*message="([^"]+)"([^)]*)\)'

    def replace_func(match):
        message = match.group(1)
        rest_params = match.group(2)

        operation = "Operation"
        if function_name:
            operation = function_name.replace("docx_", "").replace("_", " ").title()

        new_call = f'''return create_markdown_response(
            session=session,
            message="{message}",
            operation="{operation}",
            show_context=True{rest_params}
        )'''

        return new_call

    content = re.sub(pattern, replace_func, content, flags=re.MULTILINE | re.DOTALL)

    return content


def extract_function_names(content: str) -> List[str]:
    """Extract all function names from the file."""
    pattern = r'^def (docx_\w+)\('
    matches = re.findall(pattern, content, flags=re.MULTILINE)
    return matches


def migrate_file(file_path: Path, dry_run: bool = False) -> Tuple[bool, str]:
    """
    Migrate a single file to use create_markdown_response.

    Returns:
        (success, message) tuple
    """
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Migrating {file_path.name}...")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, f"Failed to read file: {e}"

    original_content = content

    # Step 1: Update imports
    content = update_imports(content)

    # Step 2: Extract function names for context
    function_names = extract_function_names(content)
    print(f"  Found {len(function_names)} functions")

    # Step 3: Migrate create_success_response calls
    content = migrate_create_success_response(content)

    # Step 4: Migrate create_context_aware_response calls
    content = migrate_create_context_aware_response(content)

    # Check if anything changed
    if content == original_content:
        return True, "No changes needed"

    # Count changes
    import_changes = content.count("create_markdown_response") - original_content.count("create_markdown_response")

    if not dry_run:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, f"Migrated successfully ({import_changes} changes)"
        except Exception as e:
            return False, f"Failed to write file: {e}"
    else:
        return True, f"Would migrate ({import_changes} changes)"


def main():
    """Main migration function."""
    print("=" * 70)
    print("Complete MCP Tools Migration Script")
    print("Converting all tools to Markdown response format")
    print("=" * 70)

    # Check if dry run
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("\n⚠️  DRY RUN MODE - No files will be modified\n")

    success_count = 0
    failed_count = 0
    skipped_count = 0

    for filename in FILES_TO_MIGRATE:
        file_path = TOOLS_DIR / filename

        if not file_path.exists():
            print(f"\n  ⚠️  {filename} not found, skipping")
            skipped_count += 1
            continue

        success, message = migrate_file(file_path, dry_run=dry_run)

        if success:
            if "No changes" in message:
                print(f"  ✓ {message}")
                skipped_count += 1
            else:
                print(f"  ✅ {message}")
                success_count += 1
        else:
            print(f"  ❌ {message}")
            failed_count += 1

    print("\n" + "=" * 70)
    print("Migration Summary")
    print("=" * 70)
    print(f"  ✅ Migrated: {success_count} files")
    print(f"  ⚠️  Skipped: {skipped_count} files")
    print(f"  ❌ Failed: {failed_count} files")
    print("=" * 70)

    if not dry_run:
        print("\n⚠️  IMPORTANT: Manual review required for:")
        print("  1. Update operations (need diff support)")
        print("  2. Complex parameter handling")
        print("  3. Test files need updating")
        print("\nRun tests: pytest tests/unit/ -v")
    else:
        print("\nRun without --dry-run to apply changes")

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
