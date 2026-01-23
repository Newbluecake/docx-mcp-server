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

        # Try to ensure COM cache exists to avoid "No such file or directory" errors
        self._ensure_com_cache()

        self.app_prog_ids = ["Word.Application", "KWPS.Application"]
        self.last_app_used = None
        self._was_open_cache = {} # Cache state between prepare and refresh: {path: (app_instance, was_visible)}

    def _ensure_com_cache(self):
        """Ensure pywin32 COM cache is generated to avoid attribute errors."""
        try:
            # The error "[Errno 2] No such file or directory: '...gen_py...'" happens
            # when win32com tries to access a non-existent cache directory.
            # Using EnsureDispatch forces the generation of this cache.
            from win32com.client import gencache
            # We don't keep the app open, just ensure the Python wrappers are generated
            # This might start Word momentarily, but it's a one-time cost per environment setup
            try:
                # Use EnsureDispatch to force cache generation
                _ = gencache.EnsureDispatch("Word.Application")
                logger.debug("Successfully verified/generated Word COM cache")
            except AttributeError:
                # Sometimes EnsureDispatch fails if cache is corrupt; try to clean it
                logger.warning("COM cache might be corrupt, attempting to rebuild...")
                import shutil
                try:
                    # gencache.is_readonly might be true for system installs
                    if not gencache.is_readonly:
                        gencache.Rebuild()
                        _ = gencache.EnsureDispatch("Word.Application")
                        logger.info("Rebuilt COM cache successfully")
                except Exception as rebuild_error:
                    logger.warning(f"Failed to rebuild COM cache: {rebuild_error}")

        except Exception as e:
            # It's okay if this fails (e.g. Word not installed), we'll just proceed
            # and _get_active_app will return None later.
            logger.debug(f"COM cache generation skipped/failed (non-critical): {e}")

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
                logger.exception(f"Failed to close document via COM: {e}")
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
                logger.exception(f"Failed to re-open document via COM: {e}")
                return False

        return False
