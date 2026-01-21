import os
import pytest
from PyQt6.QtCore import QSettings, QCoreApplication
from docx_server_launcher.core.language_manager import LanguageManager

class TestLanguageManager:
    @pytest.fixture
    def manager(self, qapp, tmp_path):
        """Fixture to provide a clean LanguageManager instance using a temp config file."""
        config_path = str(tmp_path / "test_config.ini")
        # Initialize settings with IniFormat at specific path
        settings = QSettings(config_path, QSettings.Format.IniFormat)
        settings.clear()

        # Monkey patch the LanguageManager to use our test settings
        # Or better, update LanguageManager to accept a QSettings instance or path
        # But for now, let's subclass or patch.
        # Actually, let's just make LanguageManager accept a settings object in constructor for DI

        # We need to modify LanguageManager to allow dependency injection of settings
        # But first let's see if we can just patch it.
        manager = LanguageManager(settings_prefix="DocxMCP_Test")
        manager.settings = settings # Swap the settings object
        manager.current_locale = manager.settings.value("language", "en_US")

        yield manager

    def test_initial_state(self, manager):
        """Test the initial state of the manager."""
        assert manager.current_locale is not None
        assert isinstance(manager.current_locale, str)

    def test_load_language_persistence(self, manager):
        """Test that loading a language saves it to settings."""
        manager.load_language("zh_CN")

        # Check if saved to persistence
        # Re-read from the same settings object or same file
        assert manager.settings.value("language") == "zh_CN"
        assert manager.current_locale == "zh_CN"

    def test_get_available_languages(self, manager):
        """Test retrieval of available languages."""
        langs = manager.get_available_languages()
        assert "en_US" in langs
        assert "zh_CN" in langs
        assert langs["zh_CN"] == "简体中文"
        assert langs["en_US"] == "English"
