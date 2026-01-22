import pytest
import os
import json
from unittest.mock import MagicMock, patch
from docx_mcp_server.core.replacer import replace_text_in_paragraph
from docx_mcp_server.server import docx_replace_text, docx_create, session_manager, docx_insert_image, docx_delete, docx_get_context


def _extract_element_id(response):
    """Extract element_id from JSON response or return as-is if plain string."""
    try:
        data = json.loads(response)
        if isinstance(data, dict) and "data" in data and "element_id" in data["data"]:
            return data["data"]["element_id"]
        return response
    except (json.JSONDecodeError, KeyError):
        return response

def test_replace_text_single_run():
    # Setup
    mock_para = MagicMock()
    mock_run = MagicMock()
    mock_run.text = "Hello {{name}}!"
    mock_para.runs = [mock_run]
    mock_para.text = "Hello {{name}}!"

    # Action
    replace_text_in_paragraph(mock_para, "{{name}}", "Claude")

    # Assert
    assert mock_run.text == "Hello Claude!"

def test_replace_text_split_runs():
    # Setup: "{{name}}" split across runs
    mock_para = MagicMock()
    run1 = MagicMock()
    run1.text = "Hello {{"
    run2 = MagicMock()
    run2.text = "name}}!"

    mock_para.runs = [run1, run2]
    mock_para.text = "Hello {{name}}!"

    # Mock clear and add_run for fallback
    mock_para.clear = MagicMock()
    new_run = MagicMock()
    mock_para.add_run = MagicMock(return_value=new_run)

    # Action
    replace_text_in_paragraph(mock_para, "{{name}}", "Claude")

    # Assert fallback triggered
    mock_para.clear.assert_called_once()
    mock_para.add_run.assert_called_with("Hello Claude!")

def test_docx_insert_image():
    with patch("os.path.exists", return_value=True):
        sid = docx_create()
        # Mock add_picture on run
        with patch("docx.text.run.Run.add_picture") as mock_add_pic:
             # Insert
             r_response = docx_insert_image(sid, "/tmp/image.png", width=2.0, position="end:document_body")
             r_id = _extract_element_id(r_response)

             assert r_id.startswith("run_") or r_id.startswith("para_") # Our implementation returns para_id by default if parent not specified

             # Verify session update
             session = session_manager.get_session(sid)
             clean_id = r_id.strip().split()[0]
             assert session.last_created_id == clean_id

def test_context_and_delete():
    sid = docx_create()
    session = session_manager.get_session(sid)

    # Check context
    ctx = docx_get_context(sid)
    assert "last_created_id" in ctx

    # Delete something
    # Mock an object with _element for deletion logic
    mock_obj = MagicMock()
    mock_xml = MagicMock()
    mock_parent = MagicMock()
    mock_xml.getparent.return_value = mock_parent
    mock_obj._element = mock_xml

    session.object_registry["obj_1"] = mock_obj

    docx_delete(sid, "obj_1")

    # Verify removal
    mock_parent.remove.assert_called_with(mock_xml)
    assert "obj_1" not in session.object_registry
