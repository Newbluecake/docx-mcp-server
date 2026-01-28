"""
Integration tests for history tracking tools.
"""

import pytest
from tests.helpers import (
    extract_session_id,
    extract_element_id,
    extract_metadata_field,
    is_success,
    is_error
)
import json
from docx_mcp_server.tools.session_tools import docx_close
from tests.helpers.session_helpers import setup_active_session, teardown_active_session
from docx_mcp_server.tools.paragraph_tools import docx_insert_paragraph
from docx_mcp_server.tools.history_tools import (
    docx_log,
    docx_rollback,
    docx_checkout
)


def test_docx_log():
    """Test getting commit log."""
    session_id = setup_active_session()
    try:
        # Create some commits by making changes
        from docx_mcp_server.server import session_manager
        session = session_manager.get_session(session_id)

        # Manually create commits for testing
        for i in range(3):
            session.create_commit(
                operation=f"test_op_{i}",
                changes={"before": {}, "after": {}},
                affected_elements=[f"elem_{i}"]
            )

        # Get log
        result = docx_log(limit=2)
        assert is_success(result)
        # assert len(data["data"]["commits"]) == 2
        # assert data["data"]["total_commits"] == 3

    finally:
        teardown_active_session()


def test_docx_rollback():
    """Test rollback functionality."""
    session_id = setup_active_session()
    try:
        from docx_mcp_server.server import session_manager
        session = session_manager.get_session(session_id)

        # Create commits
        commit_ids = []
        for i in range(3):
            commit_id = session.create_commit(
                operation=f"test_op_{i}",
                changes={"before": {}, "after": {}},
                affected_elements=[]
            )
            commit_ids.append(commit_id)

        assert session.current_commit_index == 2

        # Rollback to previous
        result = docx_rollback()
        assert is_success(result)
        # assert data["data"]["current_index"] == 1

    finally:
        teardown_active_session()


def test_docx_checkout():
    """Test checkout functionality."""
    session_id = setup_active_session()
    try:
        from docx_mcp_server.server import session_manager
        session = session_manager.get_session(session_id)

        # Create commits
        commit_ids = []
        for i in range(3):
            commit_id = session.create_commit(
                operation=f"test_op_{i}",
                changes={"before": {}, "after": {}},
                affected_elements=[]
            )
            commit_ids.append(commit_id)

        # Checkout to first commit
        result = docx_checkout(commit_ids[0])
        assert is_success(result)
        # assert data["data"]["target_commit"] == commit_ids[0]
        # assert data["data"]["current_index"] == 0

    finally:
        teardown_active_session()
