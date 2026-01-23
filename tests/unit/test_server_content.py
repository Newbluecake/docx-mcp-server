import unittest
import json
from docx_mcp_server.server import (
    docx_create,
    docx_insert_paragraph,
    docx_insert_heading,
    docx_insert_run,
    session_manager
)

# Add parent directory to path for helpers import
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from helpers import (
    extract_session_id,
    extract_element_id,
    extract_metadata_field,
    is_success,
    is_error
)

