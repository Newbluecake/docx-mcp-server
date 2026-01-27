"""Integration tests for special position IDs.

Tests the integration of special IDs with PositionResolver and various tools.
"""

import pytest
from docx import Document
from docx_mcp_server.core.session import Session
from docx_mcp_server.services.navigation import PositionResolver
from docx_mcp_server.tools.paragraph_tools import (
    docx_insert_paragraph,
    docx_update_paragraph_text
)
from docx_mcp_server.tools.run_tools import docx_insert_run, docx_set_font
from docx_mcp_server.tools.format_tools import docx_set_alignment, docx_format_copy
from tests.helpers.markdown_extractors import extract_element_id, is_success, is_error


@pytest.fixture
def session_id():
    """Create a test session using the global session_manager."""
    from docx_mcp_server.server import session_manager
    sid = session_manager.create_session()
    yield sid
    # Cleanup
    session_manager.close_session(sid)


@pytest.fixture
def session(session_id):
    """Get the session object."""
    from docx_mcp_server.server import session_manager
    return session_manager.get_session(session_id)


class TestPositionResolverIntegration:
    """Test PositionResolver integration with special IDs."""

    def test_resolve_position_with_last_insert(self, session):
        """Test PositionResolver with position='after:last_insert'."""
        # Create a paragraph
        para = session.document.add_paragraph("First")
        para_id = session.register_object(para, "para")
        session.update_context(para_id, action="create")

        # Resolve position using last_insert
        resolver = PositionResolver(session)
        parent, ref, mode = resolver.resolve("after:last_insert")

        assert ref is para
        assert mode == "after"

    def test_resolve_position_with_cursor(self, session):
        """Test PositionResolver with position='inside:cursor'."""
        # Create a paragraph and set cursor
        para = session.document.add_paragraph("Test")
        para_id = session.register_object(para, "para")
        session.cursor.element_id = para_id

        # Resolve position using cursor
        resolver = PositionResolver(session)
        parent, ref, mode = resolver.resolve("inside:cursor")

        assert parent is para
        assert mode == "append"

    def test_resolve_position_special_id_not_available(self, session):
        """Test PositionResolver error when special ID not available."""
        resolver = PositionResolver(session)

        with pytest.raises(ValueError) as exc_info:
            resolver.resolve("after:last_insert")

        assert "position resolution failed" in str(exc_info.value).lower()
        assert "last_insert" in str(exc_info.value).lower()


class TestToolIntegration:
    """Test tool integration with special IDs."""

    def test_insert_run_with_last_insert(self, session_id):
        """Test docx_insert_run with position='inside:last_insert'."""
        # Create a paragraph first
        result = docx_insert_paragraph("Test paragraph", position="end:document_body")
        assert is_success(result)

        # Insert run using last_insert
        result = docx_insert_run("Bold text", position="inside:last_insert")
        assert is_success(result)

        run_id = extract_element_id(result)
        assert run_id is not None
        assert run_id.startswith("run_")

    def test_update_paragraph_with_last_insert(self, session_id):
        """Test docx_update_paragraph_text with last_insert."""
        # Create a paragraph
        result = docx_insert_paragraph("Original text", position="end:document_body")
        assert is_success(result)

        # Update using last_insert
        result = docx_update_paragraph_text("last_insert", "Updated text")
        assert is_success(result)

    def test_set_alignment_with_last_update(self, session_id):
        """Test docx_set_alignment with last_update."""
        # Create and update a paragraph
        result = docx_insert_paragraph("Test", position="end:document_body")
        para_id = extract_element_id(result)

        result = docx_update_paragraph_text(para_id, "Updated")
        assert is_success(result)

        # Set alignment using last_update
        result = docx_set_alignment("last_update", "center")
        assert is_success(result)

    def test_format_copy_with_special_ids(self, session_id):
        """Test docx_format_copy with last_insert and last_update."""
        # Create source paragraph
        result = docx_insert_paragraph("Source", position="end:document_body")
        source_id = extract_element_id(result)

        # Create and update target paragraph
        result = docx_insert_paragraph("Target", position="end:document_body")
        target_id = extract_element_id(result)

        result = docx_update_paragraph_text(target_id, "Updated target")
        assert is_success(result)

        # Copy format from source (last_insert) to target (last_update)
        # Note: last_insert should be target_id (most recent insert)
        # and last_update should be target_id (most recent update)
        result = docx_format_copy(source_id, "last_update")
        assert is_success(result)

    def test_special_id_not_available_error(self, session_id):
        """Test error when special ID is not available."""
        # Try to use last_insert without creating anything
        result = docx_update_paragraph_text("last_insert", "Text")
        assert is_error(result)
        assert "SpecialIDNotAvailable" in result or "not available" in result.lower()

    def test_case_insensitive_special_ids(self, session_id):
        """Test case-insensitive special ID usage."""
        # Create a paragraph
        result = docx_insert_paragraph("Test", position="end:document_body")
        assert is_success(result)

        # Use uppercase special ID to update
        result = docx_update_paragraph_text("LAST_INSERT", "Updated")
        assert is_success(result)

        # Now last_update should be set, use mixed case to update again
        result = docx_update_paragraph_text("Last_Update", "Updated again")
        assert is_success(result)

        # Verify we can still use LAST_UPDATE
        result = docx_update_paragraph_text("LAST_UPDATE", "Final update")
        assert is_success(result)


class TestMultipleSpecialIDs:
    """Test using multiple special IDs in sequence."""

    def test_last_insert_and_last_update_tracking(self, session_id, session):
        """Test that last_insert and last_update track independently."""
        # Create first paragraph
        result = docx_insert_paragraph("Para 1", position="end:document_body")
        para1_id = extract_element_id(result)

        # Create second paragraph
        result = docx_insert_paragraph("Para 2", position="end:document_body")
        para2_id = extract_element_id(result)

        # Update first paragraph
        result = docx_update_paragraph_text(para1_id, "Para 1 updated")
        assert is_success(result)

        # Verify last_insert points to para2 and last_update points to para1
        assert session.last_insert_id == para2_id
        assert session.last_update_id == para1_id

    def test_cursor_with_last_insert(self, session_id, session):
        """Test using cursor and last_insert together."""
        # Create a paragraph
        result = docx_insert_paragraph("Para 1", position="end:document_body")
        para1_id = extract_element_id(result)

        # Move cursor
        session.cursor.element_id = para1_id

        # Insert after cursor (should be same as last_insert)
        result = docx_insert_paragraph("Para 2", position="after:cursor")
        assert is_success(result)

        # Verify both cursor and last_insert work
        result = docx_insert_paragraph("Para 3", position="after:last_insert")
        assert is_success(result)


class TestEdgeCases:
    """Test edge cases in integration."""

    def test_element_deleted_after_special_id_set(self, session_id, session):
        """Test behavior when element is deleted after special ID is set."""
        # Create a paragraph
        result = docx_insert_paragraph("Test", position="end:document_body")
        para_id = extract_element_id(result)
        assert para_id is not None

        # Delete from registry
        del session.object_registry[para_id]

        # Try to use last_insert - should resolve but get_object returns None
        result = docx_update_paragraph_text("last_insert", "Updated")
        assert is_error(result)
        assert "not found" in result.lower()

    def test_position_with_document_body(self, session_id):
        """Test using document_body special ID in position."""
        result = docx_insert_paragraph("Test", position="end:document_body")
        assert is_success(result)

        # Verify paragraph was created
        para_id = extract_element_id(result)
        assert para_id is not None
