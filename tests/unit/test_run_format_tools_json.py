"""Unit tests for refactored run and format tools with JSON responses."""

import json
import pytest
from docx_mcp_server.tools.run_tools import (
    docx_insert_run,
    docx_update_run_text,
    docx_set_font
)
from docx_mcp_server.tools.format_tools import (
    docx_set_alignment,
    docx_set_properties,
    docx_format_copy,
    docx_set_margins,
    docx_extract_format_template,
    docx_apply_format_template
)
from docx_mcp_server.tools.paragraph_tools import docx_insert_paragraph
from docx_mcp_server.tools.session_tools import docx_create, docx_close


def test_add_run_returns_json():
    """Test that docx_insert_run returns valid JSON."""
    session_id = docx_create()
    para_id = json.loads(docx_insert_paragraph(session_id, "", position="end:document_body"))["data"]["element_id"]

    result = docx_insert_run(session_id, "Test Run", position=f"inside:{para_id}")
    data = json.loads(result)

    assert data["status"] == "success"
    assert "element_id" in data["data"]
    assert data["data"]["element_id"].startswith("run_")
    assert "cursor" in data["data"]

    docx_close(session_id)


def test_update_run_text_returns_json():
    """Test that docx_update_run_text returns valid JSON."""
    session_id = docx_create()
    para_id = json.loads(docx_insert_paragraph(session_id, "", position="end:document_body"))["data"]["element_id"]
    run_id = json.loads(docx_insert_run(session_id, "Old", position=f"inside:{para_id}"))["data"]["element_id"]

    result = docx_update_run_text(session_id, run_id, "New")
    data = json.loads(result)

    assert data["status"] == "success"
    assert data["data"]["element_id"] == run_id
    assert "changed_fields" in data["data"]

    docx_close(session_id)


def test_set_font_returns_json():
    """Test that docx_set_font returns valid JSON."""
    session_id = docx_create()
    para_id = json.loads(docx_insert_paragraph(session_id, "", position="end:document_body"))["data"]["element_id"]
    run_id = json.loads(docx_insert_run(session_id, "Text", position=f"inside:{para_id}"))["data"]["element_id"]

    result = docx_set_font(session_id, run_id, bold=True, size=12, color_hex="FF0000")
    data = json.loads(result)

    assert data["status"] == "success"
    assert data["data"]["element_id"] == run_id
    assert "changed_properties" in data["data"]
    assert "bold" in data["data"]["changed_properties"]
    assert "color" in data["data"]["changed_properties"]

    docx_close(session_id)


def test_set_alignment_returns_json():
    """Test that docx_set_alignment returns valid JSON."""
    session_id = docx_create()
    para_id = json.loads(docx_insert_paragraph(session_id, "Text", position="end:document_body"))["data"]["element_id"]

    result = docx_set_alignment(session_id, para_id, "center")
    data = json.loads(result)

    assert data["status"] == "success"
    assert data["data"]["element_id"] == para_id
    assert data["data"]["alignment"] == "center"

    docx_close(session_id)


def test_set_properties_returns_json():
    """Test that docx_set_properties returns valid JSON."""
    session_id = docx_create()
    para_id = json.loads(docx_insert_paragraph(session_id, "Text", position="end:document_body"))["data"]["element_id"]

    props = json.dumps({"font": {"bold": True}})
    # set_properties usually works on runs or paragraphs. For paragraphs it sets para props.
    # But usually font props are on runs.
    # Let's add a run to test font props or use paragraph_format for paragraph.

    props = json.dumps({"paragraph_format": {"alignment": "center"}})
    result = docx_set_properties(session_id, props, element_id=para_id)
    data = json.loads(result)

    assert data["status"] == "success"
    assert data["data"]["element_id"] == para_id

    docx_close(session_id)


def test_format_copy_returns_json():
    """Test that docx_format_copy returns valid JSON."""
    session_id = docx_create()
    para1_id = json.loads(docx_insert_paragraph(session_id, "Source", position="end:document_body"))["data"]["element_id"]
    para2_id = json.loads(docx_insert_paragraph(session_id, "Target", position="end:document_body"))["data"]["element_id"]

    result = docx_format_copy(session_id, para1_id, para2_id)
    data = json.loads(result)

    assert data["status"] == "success"
    assert data["data"]["element_id"] == para2_id
    assert data["data"]["source_id"] == para1_id

    docx_close(session_id)


def test_set_margins_returns_json():
    """Test that docx_set_margins returns valid JSON."""
    session_id = docx_create()

    result = docx_set_margins(session_id, top=1.0)
    data = json.loads(result)

    assert data["status"] == "success"
    assert "margins" in data["data"]
    assert data["data"]["margins"]["top"] == 1.0

    docx_close(session_id)


def test_template_operations_return_json():
    """Test extract and apply template return JSON."""
    session_id = docx_create()
    para_id = json.loads(docx_insert_paragraph(session_id, "Template", position="end:document_body"))["data"]["element_id"]
    docx_set_alignment(session_id, para_id, "right")

    # Extract
    extract_result = docx_extract_format_template(session_id, para_id)
    extract_data = json.loads(extract_result)
    assert extract_data["status"] == "success"
    assert "template" in extract_data["data"]

    template_obj = extract_data["data"]["template"]

    # Apply
    para2_id = json.loads(docx_insert_paragraph(session_id, "Apply", position="end:document_body"))["data"]["element_id"]

    # Note: apply takes the raw JSON string of the template usually,
    # but our new extract returns a wrapped JSON response.
    # The tool signature says template_json: str.
    # Agent would parse the response, get data.template, dump it to string and pass it.
    # Or pass the raw internal string if available?
    # Our extract implementation puts the dict in data["template"].

    template_json_str = json.dumps(template_obj)

    apply_result = docx_apply_format_template(session_id, para2_id, template_json_str)
    apply_data = json.loads(apply_result)

    assert apply_data["status"] == "success"
    assert apply_data["data"]["element_id"] == para2_id

    docx_close(session_id)
