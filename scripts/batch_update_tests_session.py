#!/usr/bin/env python3
"""Batch update test files for session simplification (v4.0).

This script updates test files to:
1. Remove docx_create import
2. Replace docx_create() with setup_active_session()
3. Remove session_id parameter from tool calls
4. Add teardown_active_session() cleanup
"""

import os
import re
import sys
from pathlib import Path

# Tool functions that had session_id removed
TOOLS_WITHOUT_SESSION_ID = [
    # session_tools (except docx_switch_session)
    'docx_close',
    'docx_save',
    'docx_get_context',
    'docx_get_current_session',
    'docx_list_sessions',
    'docx_cleanup_sessions',
    # paragraph_tools
    'docx_insert_paragraph',
    'docx_insert_heading',
    'docx_update_paragraph_text',
    'docx_copy_paragraph',
    'docx_delete',
    'docx_insert_page_break',
    # run_tools
    'docx_insert_run',
    'docx_update_run_text',
    'docx_set_font',
    # table_tools
    'docx_insert_table',
    'docx_get_table',
    'docx_list_tables',
    'docx_find_table',
    'docx_get_table_structure',
    'docx_get_cell',
    'docx_insert_paragraph_to_cell',
    'docx_insert_table_row',
    'docx_insert_table_col',
    'docx_insert_row_at',
    'docx_insert_col_at',
    'docx_delete_row',
    'docx_delete_col',
    'docx_fill_table',
    'docx_copy_table',
    # format_tools
    'docx_set_alignment',
    'docx_set_properties',
    'docx_format_copy',
    'docx_set_margins',
    'docx_extract_format_template',
    'docx_apply_format_template',
    # advanced_tools
    'docx_replace_text',
    'docx_batch_replace_text',
    'docx_insert_image',
    # cursor_tools
    'docx_cursor_get',
    'docx_cursor_move',
    # copy_tools
    'docx_get_element_source',
    'docx_copy_elements_range',
    # content_tools
    'docx_read_content',
    'docx_find_paragraphs',
    'docx_extract_template_structure',
    # composite_tools
    'docx_insert_formatted_paragraph',
    'docx_quick_edit',
    'docx_get_structure_summary',
    'docx_smart_fill_table',
    'docx_format_range',
    # history_tools
    'docx_log',
    'docx_rollback',
    'docx_checkout',
]


def update_imports(content: str) -> str:
    """Update import statements."""
    # Remove docx_create from session_tools imports
    # Pattern: from docx_mcp_server.tools.session_tools import docx_create, docx_close
    content = re.sub(
        r'from docx_mcp_server\.tools\.session_tools import docx_create, docx_close',
        'from docx_mcp_server.tools.session_tools import docx_close',
        content
    )
    content = re.sub(
        r'from docx_mcp_server\.tools\.session_tools import docx_create',
        '# docx_create removed in v4.0',
        content
    )
    # Remove standalone docx_create import if in a list
    content = re.sub(
        r',\s*docx_create',
        '',
        content
    )
    content = re.sub(
        r'docx_create,\s*',
        '',
        content
    )

    # Add setup_active_session import if not present
    if 'setup_active_session' not in content and 'docx_create' in content:
        # Find a good place to add the import
        if 'from tests.helpers' in content:
            # Already has helpers import, add to it
            pass
        elif 'from helpers import' in content:
            # Has local helpers import, add after
            content = re.sub(
                r'(from helpers import[^)]+\))',
                r'\1\nfrom tests.helpers.session_helpers import setup_active_session, teardown_active_session',
                content,
                count=1
            )
        else:
            # Add after other imports
            lines = content.split('\n')
            import_end = 0
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    import_end = i
            if import_end > 0:
                lines.insert(import_end + 1, 'from tests.helpers.session_helpers import setup_active_session, teardown_active_session')
                content = '\n'.join(lines)

    return content


def update_docx_create_calls(content: str) -> str:
    """Replace docx_create() calls with setup_active_session()."""
    # Pattern: session_response = docx_create()
    content = re.sub(
        r'session_response\s*=\s*docx_create\(\)',
        'setup_active_session()',
        content
    )
    # Pattern: result = docx_create()
    content = re.sub(
        r'(\w+)\s*=\s*docx_create\(\)',
        'setup_active_session()',
        content
    )
    # Pattern: docx_create() standalone
    content = re.sub(
        r'^\s*docx_create\(\)\s*$',
        '    setup_active_session()',
        content,
        flags=re.MULTILINE
    )
    return content


def update_tool_calls(content: str) -> str:
    """Remove session_id parameter from tool calls."""
    for tool in TOOLS_WITHOUT_SESSION_ID:
        # Pattern: tool(session_id, other_args)
        # We need to be careful to match the session_id variable
        patterns = [
            # tool(session_id, "text", ...) -> tool("text", ...)
            (rf'{tool}\(session_id,\s*', f'{tool}('),
            # tool(session_id) -> tool()
            (rf'{tool}\(session_id\)', f'{tool}()'),
        ]
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
    return content


def update_docx_close_calls(content: str) -> str:
    """Update docx_close calls and add teardown."""
    # Pattern: docx_close(session_id) -> teardown_active_session()
    content = re.sub(
        r'docx_close\(session_id\)',
        'teardown_active_session()',
        content
    )
    # Also handle docx_close() without args (already updated)
    return content


def remove_session_id_extraction(content: str) -> str:
    """Remove session_id extraction lines."""
    # Pattern: session_id = extract_session_id(session_response)
    content = re.sub(
        r'\n\s*session_id\s*=\s*extract_session_id\(session_response\)\s*\n',
        '\n',
        content
    )
    content = re.sub(
        r'\n\s*session_id\s*=\s*extract_session_id\([^)]+\)\s*\n',
        '\n',
        content
    )
    return content


def update_test_file(filepath: Path, dry_run: bool = False) -> tuple[bool, list[str]]:
    """Update a single test file.

    Returns:
        tuple: (was_modified, list of changes made)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        original_content = f.read()

    content = original_content
    changes = []

    # Skip if already updated
    if 'setup_active_session' in content and 'docx_create' not in content:
        return False, ['Already updated']

    # Skip if no docx_create
    if 'docx_create' not in content:
        return False, ['No docx_create found']

    # Apply transformations
    new_content = update_imports(content)
    if new_content != content:
        changes.append('Updated imports')
        content = new_content

    new_content = update_docx_create_calls(content)
    if new_content != content:
        changes.append('Replaced docx_create() calls')
        content = new_content

    new_content = remove_session_id_extraction(content)
    if new_content != content:
        changes.append('Removed session_id extraction')
        content = new_content

    new_content = update_tool_calls(content)
    if new_content != content:
        changes.append('Removed session_id from tool calls')
        content = new_content

    new_content = update_docx_close_calls(content)
    if new_content != content:
        changes.append('Updated docx_close to teardown_active_session')
        content = new_content

    if content != original_content:
        if not dry_run:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        return True, changes

    return False, ['No changes needed']


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Update test files for session simplification')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without applying')
    parser.add_argument('--file', type=str, help='Update a single file')
    args = parser.parse_args()

    tests_dir = Path(__file__).parent.parent / 'tests'

    if args.file:
        files = [Path(args.file)]
    else:
        files = list(tests_dir.rglob('*.py'))

    modified_count = 0
    skipped_count = 0

    for filepath in sorted(files):
        if '__pycache__' in str(filepath):
            continue

        modified, changes = update_test_file(filepath, dry_run=args.dry_run)

        if modified:
            modified_count += 1
            print(f"✅ {filepath.relative_to(tests_dir.parent)}")
            for change in changes:
                print(f"   - {change}")
        else:
            skipped_count += 1
            if args.dry_run:
                print(f"⏭️  {filepath.relative_to(tests_dir.parent)}: {', '.join(changes)}")

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Summary:")
    print(f"  Modified: {modified_count}")
    print(f"  Skipped: {skipped_count}")


if __name__ == '__main__':
    main()
