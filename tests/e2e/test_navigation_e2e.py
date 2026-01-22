import pytest
import json
import tempfile
import os
from docx_mcp_server.server import docx_create, docx_save, docx_close, session_manager
from docx_mcp_server.tools.paragraph_tools import docx_insert_heading, docx_insert_paragraph
from docx_mcp_server.tools.table_tools import docx_insert_table
from docx_mcp_server.tools.advanced_tools import docx_insert_image

# Minimal 1x1 PNG for testing
PNG_DATA = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff\x3f\x03\x00\x08\xfc\x02\xfe\xa7\x9a\xa0\xa0\x00\x00\x00\x00IEND\xae\x42\x60\x82'

@pytest.fixture
def temp_image():
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(PNG_DATA)
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)

def _extract(response):
    data = json.loads(response)
    if data["status"] == "error":
        raise ValueError(f"Tool failed: {data['message']}")
    return data["data"]

def test_complex_navigation_scenario(temp_image):
    """
    Simulate a complex agent workflow:
    1. Create Document
    2. Add Intro Paragraph
    3. Add Conclusion Paragraph
    4. Insert Heading 'Chapter 1' BEFORE Intro
    5. Insert Table AFTER Heading
    6. Insert Image AT START of document

    Expected Order:
    [0] Image
    [1] Heading 'Chapter 1'
    [2] Table
    [3] Intro
    [4] Conclusion
    """
    session_id = docx_create()

    # 1. Add Intro
    intro_data = _extract(docx_insert_paragraph(session_id, "Intro Paragraph", position="end:document_body"))
    intro_id = intro_data["element_id"]

    # 2. Add Conclusion (appended)
    concl_data = _extract(docx_insert_paragraph(session_id, "Conclusion Paragraph", position="end:document_body"))

    # 3. Insert Heading BEFORE Intro
    head_data = _extract(docx_insert_heading(session_id, "Chapter 1", position=f"before:{intro_id}", level=1))
    head_id = head_data["element_id"]

    # 4. Insert Table AFTER Heading
    table_data = _extract(docx_insert_table(session_id, rows=2, cols=2, position=f"after:{head_id}"))

    # 5. Insert Image AT START
    img_data = _extract(docx_insert_image(session_id, temp_image, position="start:document_body"))

    # --- Verification ---
    session = session_manager.get_session(session_id)
    # Get all block-level elements (paragraphs and tables)
    body_elements = list(session.document._body._element.iterchildren())

    # Filter for relevant tags (w:p, w:tbl)
    blocks = [e for e in body_elements if e.tag.endswith(('p', 'tbl'))]

    assert len(blocks) == 5

    # [0] Image (Paragraph)
    assert blocks[0].tag.endswith('p')
    # Use XPath or check run content to verify it's the image, or trust the sequence for now

    # [1] Heading (Paragraph)
    assert blocks[1].tag.endswith('p')
    # Check text content of this paragraph
    # Note: We need to go from XML element back to python-docx object or check XML text
    xml_text = "".join([t.text for t in blocks[1].iter() if t.tag.endswith('t') and t.text])
    assert "Chapter 1" in xml_text

    # [2] Table
    assert blocks[2].tag.endswith('tbl')

    # [3] Intro
    assert blocks[3].tag.endswith('p')
    xml_text = "".join([t.text for t in blocks[3].iter() if t.tag.endswith('t') and t.text])
    assert "Intro Paragraph" in xml_text

    # [4] Conclusion
    assert blocks[4].tag.endswith('p')
    xml_text = "".join([t.text for t in blocks[4].iter() if t.tag.endswith('t') and t.text])
    assert "Conclusion Paragraph" in xml_text

    # --- Check Visual Context ---
    # The last operation was insert_image at start.
    # The context tree should show the Image at the top, and subsequent siblings.
    cursor = img_data["cursor"]
    visual = cursor["visual"]

    print("\nFinal Visual Context:")
    print(visual)

    # Assert structure in visual
    # Should see Image (Current), then Heading, etc.
    assert "<--- Current" in visual
    # Since Image is at top, we expect to see it first.
    # The visualizer shows siblings around the current element.
    # We should see at least the next sibling (Heading)
    assert "Chapter 1" in visual
