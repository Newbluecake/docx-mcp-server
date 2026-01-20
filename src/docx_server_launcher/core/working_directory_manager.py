import os
from pathlib import Path
from typing import List, Tuple
from PyQt6.QtCore import QSettings

class WorkingDirectoryManager:
    """Core logic for managing working directory switching"""

    MAX_HISTORY = 10

    def __init__(self, settings: QSettings):
        """
        Args:
            settings: QSettings instance for configuration persistence
        """
        self.settings = settings
        self._history_cache: List[str] = []
        self.load_settings()

    def validate_directory(self, path: str) -> Tuple[bool, str]:
        """
        Validate if the directory is valid

        Args:
            path: Directory path

        Returns:
            (is_valid, error_message)
            - (True, "") if valid
            - (False, error_message) if invalid
        """
        if not path:
            return False, "Directory path is empty"

        p = Path(path)

        if not p.exists():
            return False, f"Directory does not exist: {path}"

        if not p.is_dir():
            return False, f"Path is not a directory: {path}"

        # Check read and write permissions
        if not os.access(path, os.R_OK | os.W_OK):
            return False, f"Insufficient permissions to access: {path}"

        return True, ""

    def add_to_history(self, path: str):
        """
        Add directory to history

        Args:
            path: Directory path (must be validated first)
        """
        # Normalize path
        normalized = str(Path(path).resolve())

        # Deduplication: remove if exists
        if normalized in self._history_cache:
            self._history_cache.remove(normalized)

        # Insert at the beginning
        self._history_cache.insert(0, normalized)

        # Limit length
        self._history_cache = self._history_cache[:self.MAX_HISTORY]

        # Save immediately
        self.save_settings()

    def get_history(self) -> List[str]:
        """Get history list (newest first)"""
        return self._history_cache.copy()

    def save_settings(self):
        """Save configuration to QSettings"""
        self.settings.setValue("cwd_history", self._history_cache)

    def load_settings(self):
        """Load configuration from QSettings"""
        history = self.settings.value("cwd_history", [])
        # QSettings might return None or other types
        if isinstance(history, list):
            # Ensure all items are strings
            self._history_cache = [str(item) for item in history]
        else:
            self._history_cache = []
