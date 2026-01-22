import unittest
import json
from docx_mcp_server.server import (
    docx_create,
    docx_insert_table,
    docx_get_cell,
    docx_insert_paragraph_to_cell,
    session_manager
)


def _extract_element_id(response):
    """Extract element_id from JSON response or return as-is if plain string."""
    try:
        data = json.loads(response)
        if isinstance(data, dict) and "data" in data and "element_id" in data["data"]:
            return data["data"]["element_id"]
        return response
    except (json.JSONDecodeError, KeyError):
        return response

class TestServerTables(unittest.TestCase):
    def setUp(self):
        session_manager.sessions.clear()
        self.session_id = docx_create()

    def test_add_table(self):
        table_response = docx_insert_table(self.session_id, rows=2, cols=3, position="end:document_body")
        table_id = _extract_element_id(table_response)
        self.assertTrue(table_id.startswith("table_"))

        session = session_manager.get_session(self.session_id)
        table = session.get_object(table_id)
        self.assertEqual(len(table.rows), 2)
        self.assertEqual(len(table.columns), 3)

    def test_get_cell(self):
        table_response = docx_insert_table(self.session_id, rows=2, cols=2, position="end:document_body")
        table_id = _extract_element_id(table_response)
        cell_response = docx_get_cell(self.session_id, table_id, 0, 1) # Row 0, Col 1
        cell_id = _extract_element_id(cell_response)
        self.assertTrue(cell_id.startswith("cell_"))

    def test_write_to_cell(self):
        table_response = docx_insert_table(self.session_id, rows=1, cols=1, position="end:document_body")
        table_id = _extract_element_id(table_response)
        cell_response = docx_get_cell(self.session_id, table_id, 0, 0)
        cell_id = _extract_element_id(cell_response)

        para_response = docx_insert_paragraph_to_cell(self.session_id, "Cell Content", position=f"inside:{cell_id}")
        para_id = _extract_element_id(para_response)
        self.assertTrue(para_id.startswith("para_"))

        session = session_manager.get_session(self.session_id)
        table = session.get_object(table_id)
        self.assertEqual(table.cell(0,0).text, "Cell Content")

    def test_cell_out_of_range(self):
        table_response = docx_insert_table(self.session_id, rows=1, cols=1, position="end:document_body")
        table_id = _extract_element_id(table_response)
        result = docx_get_cell(self.session_id, table_id, 5, 5)
        try:
            data = json.loads(result)
            self.assertEqual(data["status"], "error")
        except (json.JSONDecodeError, KeyError):
            self.assertIn("out of range", result.lower())

if __name__ == '__main__':
    unittest.main()
