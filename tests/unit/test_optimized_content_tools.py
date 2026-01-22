"""Unit tests for optimized content tools"""
import json
import pytest
from docx_mcp_server.tools.content_tools import (
    docx_read_content,
    docx_find_paragraphs,
    docx_extract_template_structure
)
from docx_mcp_server.tools.session_tools import docx_create, docx_close
from docx_mcp_server.tools.paragraph_tools import docx_add_paragraph, docx_add_heading
from docx_mcp_server.tools.table_tools import docx_add_table


def test_read_content_with_pagination():
    """Test reading content with pagination"""
    session_id = docx_create()

    try:
        # Add multiple paragraphs
        for i in range(20):
            docx_add_paragraph(session_id, f"Paragraph {i}")

        # Read first 5
        content = docx_read_content(session_id, max_paragraphs=5)
        lines = content.split("\n")
        assert len(lines) == 5
        assert "Paragraph 0" in lines[0]

        # Read paragraphs 5-10
        content = docx_read_content(session_id, max_paragraphs=5, start_from=5)
        lines = content.split("\n")
        assert len(lines) == 5
        assert "Paragraph 5" in lines[0]

    finally:
        docx_close(session_id)


def test_find_paragraphs_with_limit():
    """Test finding paragraphs with result limit"""
    session_id = docx_create()

    try:
        # Add many matching paragraphs
        for i in range(20):
            docx_add_paragraph(session_id, f"Test paragraph {i}")

        # Find with limit
        matches_json = docx_find_paragraphs(session_id, "Test", max_results=5)
        matches = json.loads(matches_json)

        assert len(matches) == 5

    finally:
        docx_close(session_id)


def test_extract_template_structure_with_limits():
    """Test extracting structure with item limits"""
    session_id = docx_create()

    try:
        # Add content
        for i in range(5):
            docx_add_heading(session_id, f"Heading {i}", level=1)
            docx_add_paragraph(session_id, f"Content {i}")

        docx_add_table(session_id, 2, 2)

        # Extract with limits
        limits = json.dumps({"headings": 2, "paragraphs": 0, "tables": 1})
        structure_json = docx_extract_template_structure(
            session_id,
            max_items_per_type=limits,
            include_content=False
        )

        structure = json.loads(structure_json)
        doc_structure = structure["document_structure"]

        # Count by type
        headings = [e for e in doc_structure if e["type"] == "heading"]
        paragraphs = [e for e in doc_structure if e["type"] == "paragraph"]
        tables = [e for e in doc_structure if e["type"] == "table"]

        assert len(headings) <= 2
        assert len(paragraphs) == 0
        assert len(tables) <= 1

    finally:
        docx_close(session_id)


def test_extract_template_structure_no_content():
    """Test extracting structure without content"""
    session_id = docx_create()

    try:
        docx_add_heading(session_id, "Test Heading", level=1)
        docx_add_paragraph(session_id, "Long paragraph content" * 100)

        structure_json = docx_extract_template_structure(
            session_id,
            include_content=False
        )

        structure = json.loads(structure_json)
        doc_structure = structure["document_structure"]

        # Check that text is truncated
        for item in doc_structure:
            if "text" in item:
                assert "[" in item["text"] and "chars]" in item["text"]

    finally:
        docx_close(session_id)
