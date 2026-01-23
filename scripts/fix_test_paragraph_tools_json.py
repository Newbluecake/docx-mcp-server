#!/usr/bin/env python3
"""Fix test_paragraph_tools_json.py to work with Markdown responses."""

import re

def fix_file():
    file_path = "tests/unit/test_paragraph_tools_json.py"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove cursor assertion (line 41)
    content = re.sub(
        r'    assert extract_metadata_field\(result, "cursor"\) is not None\n',
        '',
        content
    )

    # Fix line 105: para_id = data["data"]["element_id"]
    content = re.sub(
        r'    para_id = data\["data"\]\["element_id"\]',
        '    para_id = extract_element_id(result)',
        content
    )

    # Fix line 138: original_id = data["data"]["element_id"]
    content = re.sub(
        r'    original_id = data\["data"\]\["element_id"\]',
        '    original_id = extract_element_id(result)',
        content
    )

    # Fix line 146: assert data["data"]["element_id"] != original_id
    content = re.sub(
        r'    assert data\["data"\]\["element_id"\] != original_id',
        '    assert extract_element_id(result) != original_id',
        content
    )

    # Fix line 160: para_id = data["data"]["element_id"]
    content = re.sub(
        r'    # Create paragraph\n    result = docx_insert_paragraph\(session_id, "To be deleted", position="end:document_body"\)\n    para_id = data\["data"\]\["element_id"\]',
        '    # Create paragraph\n    result = docx_insert_paragraph(session_id, "To be deleted", position="end:document_body")\n    para_id = extract_element_id(result)',
        content
    )

    # Fix line 180: para_id = data["data"]["element_id"]
    content = re.sub(
        r'    # Create paragraph \(sets context\)\n    result = docx_insert_paragraph\(session_id, "Context paragraph", position="end:document_body"\)\n    para_id = data\["data"\]\["element_id"\]',
        '    # Create paragraph (sets context)\n    result = docx_insert_paragraph(session_id, "Context paragraph", position="end:document_body")\n    para_id = extract_element_id(result)',
        content
    )

    # Fix test_cursor_context_in_response (lines 218-237)
    content = re.sub(
        r'def test_cursor_context_in_response\(\):.*?docx_close\(session_id\)',
        '''def test_cursor_context_in_response():
    """Test that cursor context is included in responses."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)

    # Add first paragraph
    docx_insert_paragraph(session_id, "First", position="end:document_body")

    # Add second paragraph
    result = docx_insert_paragraph(session_id, "Second", position="end:document_body")

    # Check that response includes document context (cursor is shown in context)
    assert is_success(result)
    assert "Document Context" in result or "CURSOR" in result

    docx_close(session_id)''',
        content,
        flags=re.DOTALL
    )

    # Fix test_json_response_structure (lines 240-260)
    content = re.sub(
        r'def test_json_response_structure\(\):.*?docx_close\(session_id\)',
        '''def test_json_response_structure():
    """Test that all responses follow the standard structure."""
    session_response = docx_create()

    session_id = extract_session_id(session_response)

    # Test various operations
    operations = [
        docx_insert_paragraph(session_id, "Test", position="end:document_body"),
        docx_insert_heading(session_id, "Heading", position="end:document_body", level=1),
        docx_insert_page_break(session_id, position="end:document_body")
    ]

    for result in operations:
        # All responses must be successful and have element_id
        assert is_success(result)
        assert extract_element_id(result) is not None

    docx_close(session_id)''',
        content,
        flags=re.DOTALL
    )

    # Fix test_error_response_structure (lines 263-271)
    content = re.sub(
        r'def test_error_response_structure\(\):.*?assert extract_metadata_field\(result, "error_type"\) is not None',
        '''def test_error_response_structure():
    """Test that error responses follow the standard structure."""
    # Test with invalid session
    result = docx_insert_paragraph("invalid", "Test", position="end:document_body")

    assert is_error(result)
    assert extract_error_message(result) is not None
    assert extract_metadata_field(result, "error_type") is not None''',
        content,
        flags=re.DOTALL
    )

    # Fix test_add_paragraph_to_parent (lines 274-299) - use helper functions
    content = re.sub(
        r'    # Create table\n    table_result = docx_insert_table\(session_id, 2, 2, position="end:document_body"\)\n    table_data = json\.loads\(table_result\)\n    table_id = table_data\["data"\]\["element_id"\]\n\n    # Get cell\n    cell_result = docx_get_cell\(session_id, table_id, 0, 0\)\n    cell_data = json\.loads\(cell_result\)\n    cell_id = cell_data\["data"\]\["element_id"\]',
        '''    # Create table
    table_result = docx_insert_table(session_id, 2, 2, position="end:document_body")
    table_id = extract_element_id(table_result)

    # Get cell
    cell_result = docx_get_cell(session_id, table_id, 0, 0)
    cell_id = extract_element_id(cell_result)''',
        content
    )

    # Add extract_error_message to imports
    content = re.sub(
        r'from helpers import \(\n    extract_session_id,\n    extract_element_id,\n    extract_metadata_field,\n    is_success,\n    is_error\n\)',
        '''from helpers import (
    extract_session_id,
    extract_element_id,
    extract_metadata_field,
    extract_error_message,
    is_success,
    is_error
)''',
        content
    )

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ Fixed {file_path}")

if __name__ == "__main__":
    fix_file()
