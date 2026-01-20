import uuid
import time
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

    def touch(self):
        self.last_accessed = time.time()

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

    def create_session(self, file_path: Optional[str] = None) -> str:
        """Create a new session, optionally loading a file."""
        session_id = str(uuid.uuid4())

        if file_path:
            doc = Document(file_path)
        else:
            doc = Document()

        session = Session(
            session_id=session_id,
            document=doc,
            file_path=file_path
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
