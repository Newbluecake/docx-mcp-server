import pytest
from docx import Document
from docx_mcp_server.core.template_parser import TemplateParser


def test_template_parser_init():
    """Test TemplateParser initialization."""
    parser = TemplateParser()
    assert parser is not None


def test_extract_structure_empty_document():
    """Test extracting structure from empty document."""
    doc = Document()
    parser = TemplateParser()
    result = parser.extract_structure(doc)

    assert "metadata" in result
    assert "document_structure" in result
    assert isinstance(result["document_structure"], list)
    assert len(result["document_structure"]) == 0
