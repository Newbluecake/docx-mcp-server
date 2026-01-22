"""Response formatting utilities for MCP tools.

This module provides standardized JSON response structures for all tools,
enabling better context awareness and automation in Agent workflows.
"""

from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class CursorInfo:
    """Cursor position information."""
    element_id: Optional[str] = None
    position: str = "after"
    parent_id: Optional[str] = None
    context: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ToolResponse:
    """Standardized tool response structure.

    Attributes:
        status: Operation status ("success" or "error")
        message: Human-readable message
        data: Structured data containing operation results
    """
    status: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        try:
            return json.dumps(asdict(self), ensure_ascii=False, indent=2)
        except Exception as e:
            logger.exception(f"Failed to serialize response: {e}")
            # Fallback to simple error response
            return json.dumps({
                "status": "error",
                "message": f"Response serialization failed: {str(e)}",
                "data": {}
            })


def create_success_response(
    message: str,
    element_id: Optional[str] = None,
    cursor: Optional[CursorInfo] = None,
    **extra_data
) -> str:
    """Create a success response with optional element ID and cursor info.

    Args:
        message: Success message
        element_id: Created/modified element ID
        cursor: Cursor position information
        **extra_data: Additional data fields

    Returns:
        JSON string of ToolResponse
    """
    data = {}

    if element_id:
        data["element_id"] = element_id

    if cursor:
        if isinstance(cursor, dict):
            data["cursor"] = cursor
        elif hasattr(cursor, 'to_dict'):
            data["cursor"] = cursor.to_dict()
        else:
            # Fallback or raise? Let's just use as is or try __dict__
            data["cursor"] = getattr(cursor, '__dict__', str(cursor))

    # Add any extra data fields
    data.update(extra_data)

    response = ToolResponse(
        status="success",
        message=message,
        data=data
    )

    return response.to_json()


def create_error_response(message: str, error_type: Optional[str] = None) -> str:
    """Create an error response.

    Args:
        message: Error message
        error_type: Optional error type classification

    Returns:
        JSON string of ToolResponse
    """
    data = {}
    if error_type:
        data["error_type"] = error_type

    response = ToolResponse(
        status="error",
        message=message,
        data=data
    )

    return response.to_json()


def create_context_aware_response(
    session,
    message: str,
    element_id: Optional[str] = None,
    include_cursor: bool = True,
    **extra_data
) -> str:
    """Create a context-aware response with cursor information.

    This is a convenience function that automatically fetches cursor context
    from the session if available.

    Args:
        session: Session object
        message: Success message
        element_id: Created/modified element ID
        include_cursor: Whether to include cursor context
        **extra_data: Additional data fields

    Returns:
        JSON string of ToolResponse
    """
    cursor_info = None

    if include_cursor and hasattr(session, 'cursor'):
        try:
            cursor_context = session.get_cursor_context()
            cursor_info = CursorInfo(
                element_id=session.cursor.element_id,
                position=session.cursor.position,
                parent_id=session.cursor.parent_id,
                context=cursor_context
            )
        except Exception as e:
            logger.warning(f"Failed to get cursor context: {e}")

    return create_success_response(
        message=message,
        element_id=element_id,
        cursor=cursor_info,
        **extra_data
    )
