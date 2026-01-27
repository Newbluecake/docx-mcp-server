"""
Unit tests for MainWindow UI changes (T-008).
"""

import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PyQt6.QtWidgets import QApplication, QLineEdit, QPushButton, QLabel
except ImportError as exc:  # pragma: no cover - environment-specific
    pytest.skip(
        f"PyQt6 not available ({exc})",
        allow_module_level=True,
    )
from docx_server_launcher.gui.main_window import MainWindow


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestMainWindowUI:
    """Test MainWindow UI modifications."""

    def test_cli_launcher_initialized(self, qapp):
        """Test that CLILauncher is initialized."""
        window = MainWindow()
        assert hasattr(window, "cli_launcher")
        assert window.cli_launcher is not None

    def test_cli_params_input_exists(self, qapp):
        """Test that CLI params input field exists."""
        window = MainWindow()
        assert hasattr(window, "cli_params_input")
        assert isinstance(window.cli_params_input, QLineEdit)
        assert window.cli_params_input.placeholderText() != ""

    def test_command_display_exists(self, qapp):
        """Test that command display field exists."""
        window = MainWindow()
        assert hasattr(window, "command_display")
        assert isinstance(window.command_display, QLineEdit)
        assert window.command_display.isReadOnly()

    def test_copy_button_exists(self, qapp):
        """Test that copy button exists."""
        window = MainWindow()
        assert hasattr(window, "copy_btn")
        assert isinstance(window.copy_btn, QPushButton)

    def test_copy_button_connected(self, qapp):
        """Test that copy button is connected to copy_command method."""
        window = MainWindow()
        assert window.copy_btn.receivers(window.copy_btn.clicked) > 0

    def test_update_command_display_exists(self, qapp):
        """Test that update_command_display method exists."""
        window = MainWindow()
        assert hasattr(window, "update_command_display")
        assert callable(window.update_command_display)

    def test_settings_persistence(self, qapp, tmp_path):
        """Test that CLI params are saved and loaded."""
        from PyQt6.QtCore import QSettings

        # Use temp settings file
        settings_file = str(tmp_path / "test_settings.ini")
        QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path))

        window = MainWindow()
        window.settings = QSettings(settings_file, QSettings.Format.IniFormat)

        # Set CLI params
        test_params = "--model opus --agent reviewer"
        window.cli_params_input.setText(test_params)
        window.save_settings()

        # Create new window and load settings
        window2 = MainWindow()
        window2.settings = QSettings(settings_file, QSettings.Format.IniFormat)
        window2.load_settings()

        # Verify params were loaded
        assert window2.cli_params_input.text() == test_params

    def test_copy_button_connected(self, qapp):
        """Test that copy button is connected to copy_command method."""
        window = MainWindow()

        # Check that the button has signal connections
        assert window.copy_btn.receivers(window.copy_btn.clicked) > 0
