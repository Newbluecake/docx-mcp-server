import pytest
import os
from docx_mcp_server.server import docx_create, docx_save, docx_read_content, docx_add_paragraph, docx_find_paragraphs
from docx import Document
import json

class TestLoadExisting:
    def test_create_with_existing_file(self, tmp_path):
        # Setup: Create a real docx file
        file_path = tmp_path / "test_existing.docx"
        doc = Document()
        doc.add_paragraph("Existing Content")
        doc.save(str(file_path))

        # Test: Load it via docx_create
        session_id = docx_create(file_path=str(file_path))
        assert session_id is not None

        # Verify content can be read (using our new tool later, or just save and check)
        # For now, let's verify we can add to it and save
        docx_add_paragraph(session_id, "New Content")

        output_path = tmp_path / "test_existing_modified.docx"
        docx_save(session_id, str(output_path))

        # Verify output
        doc2 = Document(str(output_path))
        texts = [p.text for p in doc2.paragraphs]
        assert "Existing Content" in texts
        assert "New Content" in texts

    def test_create_with_nonexistent_file(self):
        with pytest.raises(ValueError, match="not found"):
            docx_create(file_path="/non/existent/path.docx")

    def test_read_content(self, tmp_path):
        # Setup
        file_path = tmp_path / "test_read.docx"
        doc = Document()
        doc.add_paragraph("Line 1")
        doc.add_paragraph("Line 2")
        doc.save(str(file_path))

        session_id = docx_create(file_path=str(file_path))

        # Test read
        content = docx_read_content(session_id)
        assert "Line 1" in content
        assert "Line 2" in content

    def test_find_paragraphs(self, tmp_path):
        # Setup
        file_path = tmp_path / "test_find.docx"
        doc = Document()
        doc.add_paragraph("First paragraph")
        doc.add_paragraph("Target paragraph here")
        doc.add_paragraph("Last paragraph")
        doc.save(str(file_path))

        session_id = docx_create(file_path=str(file_path))

        # Test find
        result_json = docx_find_paragraphs(session_id, "Target")
        matches = json.loads(result_json)

        assert len(matches) == 1
        assert matches[0]["text"] == "Target paragraph here"
        assert matches[0]["id"].startswith("para_")

        # Test find - no match
        result_json = docx_find_paragraphs(session_id, "Nonexistent")
        matches = json.loads(result_json)
        assert len(matches) == 0

        # Test case insensitivity
        result_json = docx_find_paragraphs(session_id, "target")
        matches = json.loads(result_json)
        assert len(matches) == 1
