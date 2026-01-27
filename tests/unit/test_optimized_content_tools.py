"""Unit tests for optimized content tools"""
import json
import pytest
from docx_mcp_server.tools.content_tools import (
    docx_read_content,
    docx_find_paragraphs,
    docx_extract_template_structure
)
from docx_mcp_server.tools.session_tools import docx_create, docx_close
from docx_mcp_server.tools.paragraph_tools import docx_insert_paragraph, docx_insert_heading
from docx_mcp_server.tools.table_tools import docx_insert_table

# Add parent directory to path for helpers import
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from helpers import (
    extract_session_id,
    extract_element_id,
    extract_metadata_field,
    is_success,
    is_error
)


def test_read_content_with_pagination():
    """Test reading content with pagination"""
    session_response = docx_create()

    session_id = extract_session_id(session_response)

    try:
        # Add multiple paragraphs
        for i in range(20):
            docx_insert_paragraph(session_id, f"Paragraph {i}", position="end:document_body")

        # Read enough paragraphs to cover defaults + our content
        content = docx_read_content(session_id, max_paragraphs=30)
        lines = content.strip().split("\n")

        # Remove empty lines if any
        lines = [line for line in lines if line.strip()]

        # Filter to only include lines created by this test (robust against default content)
        lines = [line for line in lines if "Paragraph " in line]

        # Take the first 5 of our inserted paragraphs
        lines = lines[:5]

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
    session_response = docx_create()

    session_id = extract_session_id(session_response)

    try:
        # Add many matching paragraphs
        for i in range(20):
            docx_insert_paragraph(session_id, f"Test paragraph {i}", position="end:document_body")

        # Find with limit
        matches_json = docx_find_paragraphs(session_id, "Test", max_results=5)
        matches = json.loads(matches_json)

        assert len(matches) == 5

    finally:
        docx_close(session_id)


def test_extract_template_structure_with_limits():
    """Test extracting structure with item limits"""
    session_response = docx_create()

    session_id = extract_session_id(session_response)

    try:
        # Add content
        for i in range(5):
            docx_insert_heading(session_id, f"Heading {i}", position="end:document_body", level=1)
            docx_insert_paragraph(session_id, f"Content {i}", position="end:document_body")

        docx_insert_table(session_id, 2, 2, position="end:document_body")

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
    session_response = docx_create()

    session_id = extract_session_id(session_response)

    try:
        docx_insert_heading(session_id, "Test Heading", position="end:document_body", level=1)
        docx_insert_paragraph(session_id, "Long paragraph content" * 100, position="end:document_body")

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
