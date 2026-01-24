"""
Unit tests for config_manager module.
"""

import pytest
from PyQt6.QtCore import QSettings
from docx_server_launcher.core.config_manager import ConfigManager


class TestConfigManager:
    """Test ConfigManager functionality."""

    @pytest.fixture
    def config_manager(self, tmp_path):
        """Create a ConfigManager with temporary settings."""
        # Use a unique organization/application name for testing
        manager = ConfigManager("test-org", "test-app")
        # Clear any existing settings
        manager.settings.clear()
        yield manager
        # Cleanup
        manager.settings.clear()

    def test_save_and_load_bool(self, config_manager):
        """Test saving and loading boolean values."""
        config_manager.save_cli_param("test/bool", True)
        result = config_manager.load_cli_param("test/bool", False, bool)
        assert result is True

    def test_save_and_load_string(self, config_manager):
        """Test saving and loading string values."""
        config_manager.save_cli_param("test/string", "hello")
        result = config_manager.load_cli_param("test/string", "", str)
        assert result == "hello"

    def test_load_with_default(self, config_manager):
        """Test loading non-existent key returns default."""
        result = config_manager.load_cli_param("nonexistent", "default", str)
        assert result == "default"

    def test_get_all_cli_params(self, config_manager):
        """Test getting all CLI parameters."""
        config_manager.save_cli_param("cli/model", "opus")
        config_manager.save_cli_param("cli/verbose", True)

        params = config_manager.get_all_cli_params()

        assert "model" in params
        assert "verbose" in params
        assert params["model"] == "opus"

    def test_clear_cli_params(self, config_manager):
        """Test clearing all CLI parameters."""
        config_manager.save_cli_param("cli/model", "opus")
        config_manager.save_cli_param("cli/verbose", True)

        config_manager.clear_cli_params()

        params = config_manager.get_all_cli_params()
        assert len(params) == 0

    def test_has_cli_param(self, config_manager):
        """Test checking if parameter exists."""
        assert not config_manager.has_cli_param("cli/model")

        config_manager.save_cli_param("cli/model", "opus")

        assert config_manager.has_cli_param("cli/model")

    def test_type_conversion(self, config_manager):
        """Test type conversion on load."""
        # Save as string, load as bool
        config_manager.save_cli_param("test/flag", "true")
        result = config_manager.load_cli_param("test/flag", False, bool)
        # QSettings converts "true" string to True boolean
        assert result is True
