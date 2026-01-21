import uuid
import time
import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from docx import Document
from docx.document import Document as DocumentType
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph
from docx.text.run import Run
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

    # Reverse ID mapping cache: id(element._element) -> element_id
    _element_id_cache: Dict[int, str] = field(default_factory=dict)

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

        # Update reverse cache for context lookup
        if hasattr(obj, '_element'):
            self._element_id_cache[id(obj._element)] = obj_id

        if metadata:
            self.element_metadata[obj_id] = metadata

        logger.debug(f"Object registered: {obj_id} (type={type(obj).__name__})")
        return obj_id

    def get_metadata(self, obj_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve metadata for a registered object."""
        return self.element_metadata.get(obj_id)

    def get_object(self, obj_id: str) -> Optional[Any]:
        return self.object_registry.get(obj_id)

    def _get_element_id(self, element: Any, auto_register: bool = True) -> Optional[str]:
        """Get element ID from cache, optionally auto-register if not found."""
        if not hasattr(element, '_element'):
            return None

        element_key = id(element._element)
        if element_key in self._element_id_cache:
            return self._element_id_cache[element_key]

        if auto_register:
            prefix = "para" if isinstance(element, Paragraph) else \
                     "table" if isinstance(element, Table) else \
                     "cell" if isinstance(element, _Cell) else \
                     "run" if isinstance(element, Run) else "obj"
            return self.register_object(element, prefix)

        return None

    def _get_siblings(self, parent: Any) -> List[Any]:
        """Get all child elements from parent container."""
        elements = []

        # For Document, use paragraphs and tables properties
        if hasattr(parent, 'paragraphs') and hasattr(parent, 'tables') and not isinstance(parent, _Cell):
            # Merge paragraphs and tables in document order
            para_list = list(parent.paragraphs)
            table_list = list(parent.tables)

            # Get all body elements in order
            for child in parent._element.body:
                if child.tag.endswith('p'):
                    # Find matching paragraph
                    for p in para_list:
                        if p._element is child:
                            elements.append(p)
                            break
                elif child.tag.endswith('tbl'):
                    # Find matching table
                    for t in table_list:
                        if t._element is child:
                            elements.append(t)
                            break
        # For Cell, use paragraphs and tables
        elif isinstance(parent, _Cell):
            para_list = list(parent.paragraphs)
            table_list = list(parent.tables)

            # Get all cell elements in order
            for child in parent._element:
                if child.tag.endswith('p'):
                    for p in para_list:
                        if p._element is child:
                            elements.append(p)
                            break
                elif child.tag.endswith('tbl'):
                    for t in table_list:
                        if t._element is child:
                            elements.append(t)
                            break

        # For Paragraph, use runs
        elif isinstance(parent, Paragraph):
            return list(parent.runs)

        return elements

    def _format_element_summary(self, element: Any) -> str:
        """Format element summary with truncation."""
        if isinstance(element, Paragraph):
            text = element.text.replace('\n', ' ')
            return f'"{text[:50]}{"..." if len(text) > 50 else ""}"'
        elif isinstance(element, Run):
            text = element.text.replace('\n', ' ')
            return f'Run: "{text[:50]}{"..." if len(text) > 50 else ""}"'
        elif isinstance(element, Table):
            rows = len(element.rows)
            cols = len(element.columns) if element.rows else 0
            return f"Table ({rows}x{cols})"
        return str(type(element).__name__)

    def get_cursor_context(self, num_before: int = 2, num_after: int = 2) -> str:
        """Generate cursor position context description."""
        try:
            # Handle empty document
            if not self.cursor.element_id:
                return "Cursor: at empty document start"

            current_element = self.get_object(self.cursor.element_id)
            if not current_element:
                return f"Cursor: after {self.cursor.element_id} (element not found)"

            # Get parent container
            if self.cursor.parent_id and self.cursor.parent_id != "document_body":
                parent = self.get_object(self.cursor.parent_id)
            else:
                parent = self.document

            # Get siblings
            siblings = self._get_siblings(parent)
            if not siblings:
                return f"Cursor: after {self.cursor.element_id}"

            # Find current index
            current_idx = None
            for i, sib in enumerate(siblings):
                if hasattr(sib, '_element') and hasattr(current_element, '_element'):
                    if sib._element is current_element._element:
                        current_idx = i
                        break

            if current_idx is None:
                return f"Cursor: after {self.cursor.element_id}"

            # Build context
            lines = [f"Cursor: after {type(current_element).__name__} {self.cursor.element_id}"]

            if self.cursor.parent_id and self.cursor.parent_id != "document_body":
                parent_obj = self.get_object(self.cursor.parent_id)
                if parent_obj:
                    lines.append(f"Parent: {type(parent_obj).__name__} {self.cursor.parent_id}")

            lines.append("Context:")

            # Before elements
            start = max(0, current_idx - num_before)
            for i in range(start, current_idx):
                elem = siblings[i]
                elem_id = self._get_element_id(elem, auto_register=True)
                summary = self._format_element_summary(elem)
                lines.append(f"  [{i - current_idx}] {type(elem).__name__} {elem_id}: {summary}")

            # Current element
            summary = self._format_element_summary(current_element)
            lines.append(f"  [Current] {type(current_element).__name__} {self.cursor.element_id}: {summary}")

            # After elements
            end = min(len(siblings), current_idx + 1 + num_after)
            for i in range(current_idx + 1, end):
                elem = siblings[i]
                elem_id = self._get_element_id(elem, auto_register=True)
                summary = self._format_element_summary(elem)
                lines.append(f"  [+{i - current_idx}] {type(elem).__name__} {elem_id}: {summary}")

            if current_idx + 1 >= len(siblings):
                lines.append("  [Document End]")

            return "\n".join(lines)

        except Exception as e:
            logger.warning(f"Failed to generate cursor context: {e}")
            return f"Cursor: after {self.cursor.element_id if self.cursor.element_id else 'unknown'}"

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
