import os
import sys
import logging
import time
from typing import Optional, Any
from .base import PreviewController

# Setup logger
logger = logging.getLogger(__name__)

# Try to import pywin32, but don't fail if missing (handled by PreviewManager)
try:
    import win32com.client
    import pywintypes
    HAS_PYWIN32 = True
except ImportError:
    HAS_PYWIN32 = False
    # Mock for type hinting if needed or just ignore
    win32com = None

class Win32PreviewController(PreviewController):
    """
    Windows implementation using COM to control Word/WPS.
    """

    def __init__(self):
        if not HAS_PYWIN32:
            raise ImportError("pywin32 is required for Win32PreviewController")

        self.app_prog_ids = ["Word.Application", "KWPS.Application"]
        self.last_app_used = None
        self._was_open_cache = {} # Cache state between prepare and refresh: {path: (app_instance, was_visible)}

    def _get_active_app(self) -> Optional[Any]:
        """Try to get a running instance of Word or WPS."""
        for prog_id in self.app_prog_ids:
            try:
                app = win32com.client.GetActiveObject(prog_id)
                self.last_app_used = prog_id
                return app
            except Exception:
                continue
        return None

    def _normalize_path(self, path: str) -> str:
        """Normalize path for string comparison."""
        return os.path.normpath(os.path.abspath(path)).lower()

    def _find_document(self, app: Any, file_path: str) -> Optional[Any]:
        """Find the document object in the given app instance."""
        target_path = self._normalize_path(file_path)
        try:
            # Word documents collection is 1-based, but iteration works
            for doc in app.Documents:
                try:
                    # doc.FullName might be empty for new unsaved docs
                    if self._normalize_path(doc.FullName) == target_path:
                        return doc
                except Exception:
                    continue
        except Exception:
            pass
        return None

    def prepare_for_save(self, file_path: str) -> bool:
        """
        Check if file is open in Word/WPS. If so, close it to release the lock.
        """
        app = self._get_active_app()
        if not app:
            return False

        doc = self._find_document(app, file_path)
        if doc:
            try:
                logger.info(f"Closing document '{file_path}' in Word for saving...")
                # Remember state
                self._was_open_cache[file_path] = (app, app.Visible)

                # Close without saving changes (we are about to overwrite it anyway)
                # SaveChanges=False (wdDoNotSaveChanges = 0)
                doc.Close(SaveChanges=False)

                # Wait a tiny bit for the file lock to be released
                time.sleep(0.2)
                return True
            except Exception as e:
                logger.error(f"Failed to close document via COM: {e}")
                return False

        return False

    def refresh(self, file_path: str) -> bool:
        """
        Re-open the document if we closed it.
        """
        if file_path in self._was_open_cache:
            app, was_visible = self._was_open_cache.pop(file_path)
            try:
                logger.info(f"Re-opening document '{file_path}' in Word...")

                # Ensure app is still valid
                try:
                    # Simple check if app is alive
                    _ = app.Version
                except:
                    # App might have closed or crashed, try to get it again
                    app = self._get_active_app()
                    if not app:
                        logger.warning("Word application disappeared, cannot re-open document.")
                        return False

                # Open the document
                app.Documents.Open(os.path.abspath(file_path))

                # Restore visibility if needed (usually stays visible)
                if was_visible and not app.Visible:
                    app.Visible = True
                    app.Activate()

                return True
            except Exception as e:
                logger.error(f"Failed to re-open document via COM: {e}")
                return False

        return False
