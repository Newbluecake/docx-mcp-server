"""
History tracking tools for document change management.

This module provides tools for viewing and managing document history.
"""

import logging
from mcp.server.fastmcp import FastMCP
from docx_mcp_server.core.response import (
    create_success_response,
    create_error_response
)

logger = logging.getLogger(__name__)


def docx_log(session_id: str, limit: int = 10) -> str:
    """
    Get commit history log.

    Args:
        session_id: Session ID
        limit: Maximum number of commits to return (default: 10)

    Returns:
        JSON response with commit list
    """
    from docx_mcp_server.server import session_manager

    session = session_manager.get_session(session_id)
    if not session:
        return create_error_response(
            f"Session {session_id} not found",
            error_type="SessionNotFound"
        )

    try:
        commits = session.get_commit_log(limit=limit)

        return create_success_response(
            message=f"Retrieved {len(commits)} commit(s)",
            commits=commits,
            total_commits=len(session.history_stack),
            current_index=session.current_commit_index
        )
    except Exception as e:
        logger.exception(f"Failed to get commit log: {e}")
        return create_error_response(
            f"Failed to get commit log: {str(e)}",
            error_type="LogError"
        )


def docx_rollback(session_id: str, commit_id: str = None) -> str:
    """
    Rollback to specified commit or previous commit.

    Args:
        session_id: Session ID
        commit_id: Target commit ID (None = rollback to previous)

    Returns:
        JSON response with rollback details
    """
    from docx_mcp_server.server import session_manager

    session = session_manager.get_session(session_id)
    if not session:
        return create_error_response(
            f"Session {session_id} not found",
            error_type="SessionNotFound"
        )

    try:
        rollback_info = session.rollback(commit_id)

        return create_success_response(
            message="Rollback completed successfully",
            rolled_back_commits=rollback_info["rolled_back_commits"],
            restored_elements=rollback_info["restored_elements"],
            current_index=session.current_commit_index
        )
    except ValueError as e:
        return create_error_response(str(e), error_type="RollbackError")
    except Exception as e:
        logger.exception(f"Rollback failed: {e}")
        return create_error_response(
            f"Rollback failed: {str(e)}",
            error_type="RollbackError"
        )


def docx_checkout(session_id: str, commit_id: str) -> str:
    """
    Checkout to specified commit state.

    Args:
        session_id: Session ID
        commit_id: Target commit ID

    Returns:
        JSON response with checkout details
    """
    from docx_mcp_server.server import session_manager

    session = session_manager.get_session(session_id)
    if not session:
        return create_error_response(
            f"Session {session_id} not found",
            error_type="SessionNotFound"
        )

    try:
        checkout_info = session.checkout(commit_id)

        return create_success_response(
            message="Checkout completed successfully",
            target_commit=checkout_info["target_commit"],
            applied_commits=checkout_info["applied_commits"],
            current_index=session.current_commit_index
        )
    except ValueError as e:
        return create_error_response(str(e), error_type="CheckoutError")
    except Exception as e:
        logger.exception(f"Checkout failed: {e}")
        return create_error_response(
            f"Checkout failed: {str(e)}",
            error_type="CheckoutError"
        )


def register_tools(mcp: FastMCP):
    """Register history tracking tools"""
    mcp.tool()(docx_log)
    mcp.tool()(docx_rollback)
    mcp.tool()(docx_checkout)
