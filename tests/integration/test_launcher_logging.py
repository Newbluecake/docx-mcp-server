"""
Integration tests for launcher CLI logging enhancement.

Tests the interaction between ServerManager, CLILauncher, and MainWindow
with the new logging and CLI parameter features.
"""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import MagicMock

# Force offscreen platform before creating QApplication
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# CRITICAL FIX: Mock QMessageBox BEFORE importing MainWindow
from PyQt6.QtWidgets import QApplication, QMessageBox

QMessageBox.information = MagicMock(return_value=QMessageBox.StandardButton.Ok)
QMessageBox.critical = MagicMock(return_value=QMessageBox.StandardButton.Ok)
QMessageBox.warning = MagicMock(return_value=QMessageBox.StandardButton.Ok)

from docx_server_launcher.gui.main_window import MainWindow
from docx_server_launcher.core.config_manager import ConfigManager


@pytest.fixture
def app(qtbot):
    """Create QApplication instance."""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def main_window(qtbot, app, request):
    """Create MainWindow instance."""
    window = MainWindow()

    # CRITICAL FIX: Mock wait methods to prevent QEventLoop blocking
    window._wait_for_server_stop = MagicMock(return_value=True)
    window._wait_for_server_start = MagicMock(return_value=True)

    qtbot.addWidget(window)

    # Add explicit cleanup
    def cleanup():
        window.close()
        window.deleteLater()
        app.processEvents()

    request.addfinalizer(cleanup)

    return window


# NOTE: TestCLIParamsPersistence tests removed as the CLI parameter checkbox
# features (model_checkbox, agent_checkbox, etc.) were removed from MainWindow
# in favor of a simpler command-line interface. These features are no longer
# part of the GUI and the tests are obsolete.


class TestErrorDialogCopy:
    """Test error dialog with copy button."""

    def test_show_error_dialog_has_copy_button(self, main_window, qtbot, monkeypatch):
        """Test that error dialog includes a copy button."""
        # Mock QMessageBox.exec to avoid blocking
        dialog_shown = []

        def mock_exec(self):
            dialog_shown.append(self)
            return 0

        monkeypatch.setattr("PyQt6.QtWidgets.QMessageBox.exec", mock_exec)

        # Show error dialog
        main_window.show_error_dialog("Test Error", "This is a test error message")

        # Verify dialog was shown
        assert len(dialog_shown) == 1
        dialog = dialog_shown[0]

        # Verify copy button exists
        buttons = dialog.buttons()
        button_texts = [btn.text() for btn in buttons]
        assert any("Copy" in text for text in button_texts)


class TestConfigManager:
    """Test ConfigManager integration."""

    def test_config_manager_integration(self, tmp_path):
        """Test ConfigManager saves and loads correctly."""
        manager = ConfigManager("test-launcher", "test-app")

        # Save some parameters
        manager.save_cli_param("cli/model_enabled", True)
        manager.save_cli_param("cli/model_value", "opus")

        # Load them back
        assert manager.load_cli_param("cli/model_enabled", False, bool) is True
        assert manager.load_cli_param("cli/model_value", "", str) == "opus"

        # Cleanup
        manager.clear_cli_params()
