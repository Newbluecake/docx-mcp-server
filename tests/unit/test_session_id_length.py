from docx_mcp_server.tools.session_tools import docx_create, docx_close


def test_session_id_short_length():
    sid = docx_create()
    assert len(sid) <= 12
    docx_close(sid)
