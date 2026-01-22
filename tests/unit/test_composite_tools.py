"""Unit tests for composite tools"""
import json
import pytest
from docx_mcp_server.tools.composite_tools import (
    docx_insert_formatted_paragraph,
    docx_quick_edit,
    docx_get_structure_summary,
    docx_smart_fill_table,
    docx_format_range
)
from docx_mcp_server.tools.session_tools import docx_create, docx_close
from docx_mcp_server.tools.paragraph_tools import docx_insert_paragraph
from docx_mcp_server.tools.table_tools import docx_insert_table


def test_add_formatted_paragraph():
    """Test creating formatted paragraph in one step"""
    session_id = docx_create()

    try:
        # Create formatted paragraph
        para_id = docx_insert_formatted_paragraph(
            session_id,
            "Test Text",
            position="end:document_body",
            bold=True,
            size=14,
            color_hex="FF0000",
            alignment="center"
        )

        assert para_id.startswith("para_")

    finally:
        docx_close(session_id)


def test_quick_edit():
    """Test quick edit functionality"""
    session_id = docx_create()

    try:
        # Add some paragraphs
        docx_insert_paragraph(session_id, "This is a test paragraph", position="end:document_body")
        docx_insert_paragraph(session_id, "Another test paragraph", position="end:document_body")

        # Quick edit
        result_json = docx_quick_edit(
            session_id,
            "test",
            new_text="modified",
            bold=True
        )

        result = json.loads(result_json)
        assert result["modified_count"] == 2
        assert len(result["paragraph_ids"]) == 2

    finally:
        docx_close(session_id)


def test_get_structure_summary():
    """Test lightweight structure extraction"""
    session_id = docx_create()

    try:
        # Add some content
        docx_insert_paragraph(session_id, "Test", position="end:document_body", style="Heading 1")
        docx_insert_paragraph(session_id, "Body text", position="end:document_body")
        docx_insert_table(session_id, 2, 2, position="end:document_body")

        # Get summary
        summary_json = docx_get_structure_summary(
            session_id,
            max_headings=10,
            max_tables=5,
            max_paragraphs=0
        )

        summary = json.loads(summary_json)
        assert "headings" in summary
        assert "tables" in summary
        assert summary["summary"]["total_headings"] >= 1
        assert summary["summary"]["total_tables"] >= 1

    finally:
        docx_close(session_id)


def test_smart_fill_table():
    """Test smart table filling"""
    session_id = docx_create()

    try:
        # Create table
        docx_insert_table(session_id, 2, 3, position="end:document_body")

        # Fill with data
        data = json.dumps([
            ["Name", "Age", "City"],
            ["Alice", "30", "NYC"],
            ["Bob", "25", "LA"]
        ])

        result_json = docx_smart_fill_table(
            session_id,
            "0",  # First table
            data,
            has_header=True,
            auto_resize=True
        )

        result = json.loads(result_json)
        assert result["status"] == "success"
        assert result["rows_filled"] == 3

    finally:
        docx_close(session_id)


def test_format_range():
    """Test formatting a range of paragraphs"""
    session_id = docx_create()

    try:
        # Add paragraphs
        docx_insert_paragraph(session_id, "Start marker", position="end:document_body")
        docx_insert_paragraph(session_id, "Middle content", position="end:document_body")
        docx_insert_paragraph(session_id, "End marker", position="end:document_body")

        # Format range
        result_json = docx_format_range(
            session_id,
            "Start marker",
            "End marker",
            bold=True,
            size=14
        )

        result = json.loads(result_json)
        assert result["formatted_count"] == 3

    finally:
        docx_close(session_id)


def test_quick_edit_no_matches():
    """Test quick edit with no matches"""
    session_id = docx_create()

    try:
        docx_insert_paragraph(session_id, "Test paragraph", position="end:document_body")

        result_json = docx_quick_edit(
            session_id,
            "nonexistent",
            new_text="modified"
        )

        result = json.loads(result_json)
        assert result["modified_count"] == 0

    finally:
        docx_close(session_id)
