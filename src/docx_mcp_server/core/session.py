import uuid
import time
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from docx import Document
from docx.document import Document as DocumentType

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
    last_created_id: Optional[str] = None
    last_accessed_id: Optional[str] = None
    auto_save: bool = False

    def touch(self):
        self.last_accessed = time.time()

    def update_context(self, element_id: str, action: str = "access"):
        """Update context pointers based on action type."""
        self.last_accessed_id = element_id
        if action == "create":
            self.last_created_id = element_id

        # Trigger auto-save if enabled
        if self.auto_save and self.file_path:
            try:
                self.document.save(self.file_path)
            except Exception:
                # We don't want to crash the session if save fails,
                # but maybe we should log it? For now silently ignore or print.
                pass

    def register_object(self, obj: Any, prefix: str = "obj") -> str:
        """Register a docx object and return its ID."""
        obj_id = f"{prefix}_{uuid.uuid4().hex[:8]}"
        self.object_registry[obj_id] = obj
        return obj_id

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
            if os.path.exists(file_path):
                try:
                    doc = Document(file_path)
                except Exception as e:
                    # If file exists but fails to load (e.g. locked, corrupt), raise error
                    # so user knows why instead of silently returning empty doc
                    raise RuntimeError(f"Failed to load existing file '{file_path}': {str(e)}")
            else:
                # File doesn't exist, create new empty doc (intended for new file creation)
                doc = Document()
        else:
            doc = Document()

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
            return None

        # Check expiry
        if time.time() - session.last_accessed > self.ttl_seconds:
            del self.sessions[session_id]
            return None

        session.touch()
        return session

    def close_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def cleanup_expired(self):
        now = time.time()
        expired = [
            sid for sid, s in self.sessions.items()
            if now - s.last_accessed > self.ttl_seconds
        ]
        for sid in expired:
            del self.sessions[sid]
