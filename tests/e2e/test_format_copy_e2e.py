import pytest
import json
import os
from docx_mcp_server.server import (
    docx_create, docx_save, docx_close,
    docx_add_heading, docx_add_paragraph, docx_add_run, docx_set_font,
    docx_copy_paragraph, docx_copy_elements_range,
    docx_extract_format_template, docx_apply_format_template,
    docx_batch_replace_text, docx_read_content
)

def _extract(response):
    data = json.loads(response)
    if data["status"] == "error":
        raise ValueError(f"Tool failed: {data['message']}")
    return data["data"]

def test_format_copy_system_workflow(tmp_path):
    """
    E2E scenario:
    1. Create a "Template" section with specific styling.
    2. Extract formatting from the template.
    3. Copy the template section (Range Copy).
    4. Apply extracted formatting to a new raw paragraph.
    5. Batch replace placeholders in the copied section.
    """
    # 1. Setup
    output_file = tmp_path / "e2e_format_copy.docx"
    session_id = docx_create()

    # --- Step 1: Create Template Content ---
    # Heading 1
    h1_resp = docx_add_heading(session_id, "Template Section", level=1)
    h1_id = _extract(h1_resp)["element_id"]

    # Styled Paragraph
    p_resp = docx_add_paragraph(session_id, "")
    p_id = _extract(p_resp)["element_id"]

    run_resp = docx_add_run(session_id, "Key: ", paragraph_id=p_id)
    run_id = _extract(run_resp)["element_id"]
    docx_set_font(session_id, run_id, bold=True, color_hex="0000FF") # Blue bold label

    val_run_resp = docx_add_run(session_id, "{VALUE}", paragraph_id=p_id)
    val_run_id = _extract(val_run_resp)["element_id"]
    docx_set_font(session_id, val_run_id, italic=True) # Italic placeholder

    # End marker for range
    end_p_resp = docx_add_paragraph(session_id, "--- End Template ---")
    end_p_id = _extract(end_p_resp)["element_id"]

    # --- Step 2: Extract Formatting Template ---
    # Extract the blue bold style from the first run
    template_resp = docx_extract_format_template(session_id, run_id)
    template_data = _extract(template_resp)
    template_json = json.dumps(template_data["template"])

    assert "0000FF" in template_json
    assert "bold" in template_json

    # --- Step 3: Range Copy ---
    # Copy from Heading to End Marker
    # We expect 3 elements: Heading, Styled Para, End Marker
    new_ids_resp = docx_copy_elements_range(session_id, h1_id, end_p_id)
    new_ids = json.loads(new_ids_resp)  # This tool returns a plain JSON array

    assert len(new_ids) == 3

    # --- Step 4: Apply Formatting Template ---
    # Create a raw paragraph
    raw_p_resp = docx_add_paragraph(session_id, "")
    raw_p_id = _extract(raw_p_resp)["element_id"]

    raw_run_resp = docx_add_run(session_id, "Applied Style Text", paragraph_id=raw_p_id)
    raw_run_id = _extract(raw_run_resp)["element_id"]

    # Apply the blue bold template
    docx_apply_format_template(session_id, raw_run_id, template_json)

    # --- Step 5: Batch Replace ---
    # Replace {VALUE} with "Actual Data" globally (should affect original and copy)
    replacements = {
        "{VALUE}": "Actual Data",
        "Template Section": "Generated Section"
    }
    docx_batch_replace_text(session_id, json.dumps(replacements))

    # --- Verification ---
    content_resp = docx_read_content(session_id)
    content = content_resp  # This tool returns plain text

    print(f"Document Content:\n{content}")

    # Check replacements
    assert "Key: Actual Data" in content # Replaced value
    assert "Generated Section" in content # Replaced heading

    # Check that we have the copied section (it appears twice now, effectively)
    # Original: Generated Section ... Key: Actual Data ... --- End Template ---
    # Copy: Generated Section ... Key: Actual Data ... --- End Template ---
    assert content.count("Generated Section") >= 2
    assert content.count("Key: Actual Data") >= 2

    # Save
    docx_save(session_id, str(output_file))
    docx_close(session_id)

    assert os.path.exists(output_file)
