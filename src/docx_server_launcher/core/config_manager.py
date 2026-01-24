"""
Configuration management utilities using QSettings.

This module provides a type-safe interface for saving and loading
CLI parameters and other application settings.
"""

from typing import Any, Dict, Optional
from PyQt6.QtCore import QSettings


class ConfigManager:
    """
    Manages application configuration using QSettings.

    Provides type-safe methods for saving and loading CLI parameters
    with default value fallback.
    """

    def __init__(self, organization: str = "docx-mcp-server", application: str = "launcher"):
        """
        Initialize the configuration manager.

        Args:
            organization: Organization name for QSettings
            application: Application name for QSettings
        """
        self.settings = QSettings(organization, application)

    def save_cli_param(self, key: str, value: Any) -> None:
        """
        Save a CLI parameter to settings.

        Args:
            key: Setting key (e.g., "cli/model_enabled")
            value: Setting value (bool, str, int, etc.)
        """
        self.settings.setValue(key, value)
        self.settings.sync()

    def load_cli_param(self, key: str, default: Any = None, value_type: type = None) -> Any:
        """
        Load a CLI parameter from settings.

        Args:
            key: Setting key
            default: Default value if key doesn't exist
            value_type: Expected type for type conversion (bool, str, int)

        Returns:
            The setting value or default if not found
        """
        if value_type is not None:
            return self.settings.value(key, default, value_type)
        return self.settings.value(key, default)

    def get_all_cli_params(self) -> Dict[str, Any]:
        """
        Get all CLI parameters from settings.

        Returns:
            Dictionary of all CLI parameters with their values
        """
        params = {}
        self.settings.beginGroup("cli")
        for key in self.settings.allKeys():
            params[key] = self.settings.value(key)
        self.settings.endGroup()
        return params

    def clear_cli_params(self) -> None:
        """
        Clear all CLI parameters from settings.
        """
        self.settings.beginGroup("cli")
        self.settings.remove("")
        self.settings.endGroup()
        self.settings.sync()

    def has_cli_param(self, key: str) -> bool:
        """
        Check if a CLI parameter exists in settings.

        Args:
            key: Setting key

        Returns:
            True if the key exists, False otherwise
        """
        return self.settings.contains(key)
