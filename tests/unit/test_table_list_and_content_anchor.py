import json

from docx_mcp_server.tools.session_tools import docx_create, docx_close
from docx_mcp_server.tools.paragraph_tools import docx_insert_paragraph
from docx_mcp_server.tools.table_tools import docx_insert_table, docx_list_tables
from docx_mcp_server.tools.content_tools import docx_read_content


def test_list_tables_with_start_element_and_max_results():
    sid = docx_create()
    try:
        # Add paragraphs and tables
        p1 = docx_insert_paragraph(sid, "before tables", position="end:document_body")
        t1 = docx_insert_table(sid, rows=1, cols=1, position="end:document_body")
        p2 = docx_insert_paragraph(sid, "middle", position="end:document_body")
        t2 = docx_insert_table(sid, rows=2, cols=2, position="end:document_body")
        t3 = docx_insert_table(sid, rows=3, cols=1, position="end:document_body")

        # Start listing after t1
        t1_id = json.loads(t1)["data"]["element_id"] if isinstance(t1, str) else t1
        resp = json.loads(docx_list_tables(sid, max_results=1, start_element_id=t1_id))
        assert resp["status"] == "success"
        assert resp["data"]["count"] == 1
        first = resp["data"]["tables"][0]
        assert first["rows"] == 2 and first["cols"] == 2

    finally:
        docx_close(sid)


def test_read_content_start_element_id_skips_prior_blocks():
    sid = docx_create()
    try:
        docx_insert_paragraph(sid, "p0", position="end:document_body")
        anchor = docx_insert_paragraph(sid, "anchor", position="end:document_body")
        docx_insert_paragraph(sid, "p1", position="end:document_body")
        docx_insert_paragraph(sid, "p2", position="end:document_body")

        anchor_id = json.loads(anchor)["data"]["element_id"] if isinstance(anchor, str) else anchor
        result = json.loads(docx_read_content(sid, start_element_id=anchor_id, return_json=True))
        texts = [e["text"] for e in result["data"]]
        assert texts[0] == "p1"
        assert len(texts) == 2
    finally:
        docx_close(sid)
