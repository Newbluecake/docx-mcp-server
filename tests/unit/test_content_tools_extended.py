import json
import os
import tempfile

from docx_mcp_server.tools.session_tools import docx_create, docx_close
from docx_mcp_server.tools.paragraph_tools import docx_insert_paragraph
from docx_mcp_server.tools.content_tools import (
    docx_read_content,
    docx_find_paragraphs,
    docx_list_files,
)


def test_read_content_return_json_and_ids():
    sid = docx_create()
    docx_insert_paragraph(sid, "alpha", position="end:document_body")
    docx_insert_paragraph(sid, "beta", position="end:document_body")

    result = json.loads(docx_read_content(sid, return_json=True, include_ids=True))

    assert result["status"] == "success"
    assert result["count"] == 2
    assert all("id" in entry and entry["text"] for entry in result["data"])

    docx_close(sid)


def test_find_paragraphs_with_context():
    sid = docx_create()
    docx_insert_paragraph(sid, "one", position="end:document_body")
    docx_insert_paragraph(sid, "two match", position="end:document_body")
    docx_insert_paragraph(sid, "three", position="end:document_body")

    matches = json.loads(docx_find_paragraphs(sid, "match", max_results=2, return_context=True, context_span=1))
    assert len(matches) == 1
    entry = matches[0]
    assert entry["text"] == "two match"
    assert entry["context_before"] == ["one"]
    assert entry["context_after"] == ["three"]

    docx_close(sid)


def test_list_files_with_meta(tmp_path):
    # create a dummy docx file
    fpath = tmp_path / "sample.docx"
    with open(fpath, "wb") as f:
        f.write(b"PK\x03\x04")  # minimal zip header

    listing = json.loads(docx_list_files(directory=str(tmp_path), include_meta=True))
    assert isinstance(listing, list)
    assert listing[0]["path"].endswith("sample.docx")
    assert "size" in listing[0]
