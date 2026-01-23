import json
import logging

from docx_mcp_server.tools.system_tools import (
    docx_get_log_level,
    docx_set_log_level,
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


def test_set_log_level_updates_root():
    result = docx_set_log_level("DEBUG")
    assert is_success(result)
    assert extract_metadata_field(result, "level") == "DEBUG"
    assert logging.getLogger().getEffectiveLevel() == logging.DEBUG


def test_set_log_level_rejects_invalid():
    result = docx_set_log_level("NOPE")
    assert is_error(result)
    assert extract_metadata_field(result, "error_type") == "ValidationError"


def test_get_log_level_matches_root():
    logging.getLogger().setLevel(logging.ERROR)
    result = docx_get_log_level()
    assert is_success(result)
    assert extract_metadata_field(result, "level") == "ERROR"
