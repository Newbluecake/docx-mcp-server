import unittest
from docx_mcp_server.server import (
    docx_create,
    docx_add_table,
    docx_get_cell,
    docx_add_paragraph_to_cell,
    session_manager
)

class TestServerTables(unittest.TestCase):
    def setUp(self):
        session_manager.sessions.clear()
        self.session_id = docx_create()

    def test_add_table(self):
        table_id = docx_add_table(self.session_id, rows=2, cols=3)
        self.assertTrue(table_id.startswith("table_"))

        session = session_manager.get_session(self.session_id)
        table = session.get_object(table_id)
        self.assertEqual(len(table.rows), 2)
        self.assertEqual(len(table.columns), 3)

    def test_get_cell(self):
        table_id = docx_add_table(self.session_id, rows=2, cols=2)
        cell_id = docx_get_cell(self.session_id, table_id, 0, 1) # Row 0, Col 1
        self.assertTrue(cell_id.startswith("cell_"))

    def test_write_to_cell(self):
        table_id = docx_add_table(self.session_id, rows=1, cols=1)
        cell_id = docx_get_cell(self.session_id, table_id, 0, 0)

        para_id = docx_add_paragraph_to_cell(self.session_id, cell_id, "Cell Content")
        self.assertTrue(para_id.startswith("para_"))

        session = session_manager.get_session(self.session_id)
        table = session.get_object(table_id)
        self.assertEqual(table.cell(0,0).text, "Cell Content")

    def test_cell_out_of_range(self):
        table_id = docx_add_table(self.session_id, rows=1, cols=1)
        with self.assertRaises(ValueError):
            docx_get_cell(self.session_id, table_id, 5, 5)

if __name__ == '__main__':
    unittest.main()
