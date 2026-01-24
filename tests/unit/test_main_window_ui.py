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

    def test_launch_button_exists(self, qapp):
        """Test that launch button exists."""
        window = MainWindow()
        assert hasattr(window, "launch_btn")
        assert isinstance(window.launch_btn, QPushButton)

    def test_old_inject_button_removed(self, qapp):
        """Test that old inject button is removed."""
        window = MainWindow()
        # Should not have inject_btn attribute anymore
        # (launch_btn replaced it)
        assert not hasattr(window, "inject_btn")

    def test_launch_claude_method_exists(self, qapp):
        """Test that launch_claude method exists."""
        window = MainWindow()
        assert hasattr(window, "launch_claude")
        assert callable(window.launch_claude)

    def test_show_cli_not_found_dialog_exists(self, qapp):
        """Test that show_cli_not_found_dialog method exists."""
        window = MainWindow()
        assert hasattr(window, "show_cli_not_found_dialog")
        assert callable(window.show_cli_not_found_dialog)

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

    def test_launch_button_connected(self, qapp):
        """Test that launch button is connected to launch_claude method."""
        window = MainWindow()

        # Check that the button has signal connections
        # (We can't easily test the exact connection without triggering it)
        assert window.launch_btn.receivers(window.launch_btn.clicked) > 0
