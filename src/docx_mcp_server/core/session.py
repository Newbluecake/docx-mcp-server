import uuid
import time
import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from docx import Document
from docx.document import Document as DocumentType
from docx_mcp_server.core.validators import validate_path_safety
from docx_mcp_server.core.cursor import Cursor
from docx_mcp_server.preview.manager import PreviewManager

logger = logging.getLogger(__name__)

@dataclass
class Session:
    session_id: str
    document: DocumentType
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    file_path: Optional[str] = None
    # Registry to map string IDs to internal python-docx objects
    # structure: { "para_123": <docx.text.paragraph.Paragraph>, "run_456": ... }
    object_registry: Dict[str, Any] = field(default_factory=dict)
    # Metadata registry to store additional info about objects (e.g., source info)
    element_metadata: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    last_created_id: Optional[str] = None
    last_accessed_id: Optional[str] = None
    auto_save: bool = False
    cursor: Cursor = field(default_factory=Cursor)

    # Preview controller for handling live updates
    preview_controller: Any = field(init=False)

    def __post_init__(self):
        self.preview_controller = PreviewManager.get_controller()

    def touch(self):
        self.last_accessed = time.time()

    def update_context(self, element_id: str, action: str = "access"):
        """Update context pointers based on action type."""
        self.last_accessed_id = element_id
        if action == "create":
            self.last_created_id = element_id
        logger.debug(f"Context updated: element_id={element_id}, action={action}")

        # Trigger auto-save if enabled
        if self.auto_save and self.file_path:
            try:
                self.document.save(self.file_path)
                logger.debug(f"Auto-save successful: {self.file_path}")
            except Exception as e:
                logger.warning(f"Auto-save failed for {self.file_path}: {e}")

    def register_object(self, obj: Any, prefix: str = "obj", metadata: Optional[Dict[str, Any]] = None) -> str:
        """Register a docx object and return its ID, optionally storing metadata."""
        obj_id = f"{prefix}_{uuid.uuid4().hex[:8]}"
        self.object_registry[obj_id] = obj

        if metadata:
            self.element_metadata[obj_id] = metadata

        logger.debug(f"Object registered: {obj_id} (type={type(obj).__name__})")
        return obj_id

    def get_metadata(self, obj_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve metadata for a registered object."""
        return self.element_metadata.get(obj_id)

    def get_object(self, obj_id: str) -> Optional[Any]:
        return self.object_registry.get(obj_id)

class SessionManager:
    def __init__(self, ttl_seconds: int = 3600):
        self.sessions: Dict[str, Session] = {}
        self.ttl_seconds = ttl_seconds

    def create_session(self, file_path: Optional[str] = None, auto_save: bool = False) -> str:
        """Create a new session, optionally loading a file."""
        session_id = str(uuid.uuid4())

        if file_path:
            # 1. Validate cross-OS path safety
            validate_path_safety(file_path)

            if os.path.exists(file_path):
                try:
                    doc = Document(file_path)
                    logger.info(f"Session created: {session_id}, loaded file: {file_path}, auto_save={auto_save}")
                except Exception as e:
                    # If file exists but fails to load (e.g. locked, corrupt), raise error
                    # so user knows why instead of silently returning empty doc
                    logger.exception(f"Failed to load file '{file_path}': {e}")
                    raise RuntimeError(f"Failed to load existing file '{file_path}': {str(e)}")
            else:
                # File doesn't exist.
                # Validate that the parent directory exists so we can save later.
                # We use abspath to ensure we check the correct directory even for relative paths.
                parent_dir = os.path.dirname(os.path.abspath(file_path))
                if not os.path.exists(parent_dir):
                    logger.error(f"Parent directory does not exist: {parent_dir}")
                    raise ValueError(f"Parent directory does not exist: {parent_dir}")

                # Create new empty doc (intended for new file creation)
                doc = Document()
                logger.info(f"Session created: {session_id}, new file: {file_path}, auto_save={auto_save}")
        else:
            doc = Document()
            logger.info(f"Session created: {session_id}, in-memory document")

        session = Session(
            session_id=session_id,
            document=doc,
            file_path=file_path,
            auto_save=auto_save
        )
        self.sessions[session_id] = session
        return session_id

    def get_session(self, session_id: str) -> Optional[Session]:
        session = self.sessions.get(session_id)
        if not session:
            logger.debug(f"Session not found: {session_id}")
            return None

        # Check expiry
        if time.time() - session.last_accessed > self.ttl_seconds:
            logger.warning(f"Session expired: {session_id}")
            del self.sessions[session_id]
            return None

        session.touch()
        return session

    def close_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Session closed: {session_id}")
            return True
        logger.debug(f"Close session failed - not found: {session_id}")
        return False

    def cleanup_expired(self):
        now = time.time()
        expired = [
            sid for sid, s in self.sessions.items()
            if now - s.last_accessed > self.ttl_seconds
        ]
        for sid in expired:
            del self.sessions[sid]
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
