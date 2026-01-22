import pytest
import tempfile
import os
import json
from docx_mcp_server.server import docx_create, session_manager
from docx_mcp_server.tools.advanced_tools import docx_insert_image
from docx_mcp_server.tools.paragraph_tools import docx_insert_paragraph

# Minimal 1x1 PNG
PNG_DATA = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff\x3f\x03\x00\x08\xfc\x02\xfe\xa7\x9a\xa0\xa0\x00\x00\x00\x00IEND\xae\x42\x60\x82'

@pytest.fixture
def temp_image():
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(PNG_DATA)
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)

def _extract_id(response):
    data = json.loads(response)
    if data["status"] == "error":
        raise ValueError(f"Tool failed: {data['message']}")
    return data["data"]["element_id"]

def test_insert_image_position_after(temp_image):
    session_id = docx_create()

    # Create Anchor
    p1_resp = docx_insert_paragraph(session_id, "Anchor", position="end:document_body")
    p1_id = _extract_id(p1_resp)

    # Insert Image after Anchor
    # This creates a new paragraph containing the image
    img_resp = docx_insert_image(session_id, temp_image, position=f"after:{p1_id}")
    img_id = _extract_id(img_resp)

    session = session_manager.get_session(session_id)
    # Filter for paragraphs only (ignore sectPr)
    children = [c for c in session.document._body._element.iterchildren() if c.tag.endswith('p')]

    # Expect: Anchor (P), Image (P)
    assert len(children) == 2
    assert children[0].text == "Anchor"

    # Verify context
    data = json.loads(img_resp)["data"]
    assert "cursor" in data
    assert "visual" in data["cursor"]
    print(data["cursor"]["visual"])
    assert "Anchor" in data["cursor"]["visual"]

def test_insert_image_position_start(temp_image):
    session_id = docx_create()
    docx_insert_paragraph(session_id, "Existing", position="end:document_body")

    # Insert at start
    img_resp = docx_insert_image(session_id, temp_image, position="start:document_body")

    session = session_manager.get_session(session_id)
    # Filter for paragraphs only (ignore sectPr)
    children = [c for c in session.document._body._element.iterchildren() if c.tag.endswith('p')]

    # Expect: Image (P), Existing (P)
    assert len(children) == 2
    assert children[1].text == "Existing"

def test_insert_image_in_paragraph_error_handling(temp_image):
    # Test trying to insert into an incompatible parent or with invalid position
    session_id = docx_create()

    # Invalid position format
    resp = docx_insert_image(session_id, temp_image, position="invalid:format")
    data = json.loads(resp)
    assert data["status"] == "error"
    assert data["data"]["error_type"] == "ValidationError"
