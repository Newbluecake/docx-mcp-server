"""
Integration tests for launcher CLI logging enhancement.

Tests the interaction between ServerManager, CLILauncher, and MainWindow
with the new logging and CLI parameter features.
"""

import pytest
import json
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from docx_server_launcher.gui.main_window import MainWindow
from docx_server_launcher.core.config_manager import ConfigManager


@pytest.fixture
def app(qtbot):
    """Create QApplication instance."""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def main_window(qtbot, app):
    """Create MainWindow instance."""
    window = MainWindow()
    qtbot.addWidget(window)
    return window


class TestCLIParamsPersistence:
    """Test CLI parameters persistence across sessions."""

    def test_save_and_load_cli_params(self, main_window, qtbot):
        """Test that CLI parameters are saved and loaded correctly."""
        # Set CLI parameters
        main_window.model_checkbox.setChecked(True)
        main_window.model_combo.setCurrentText("opus")
        main_window.agent_checkbox.setChecked(True)
        main_window.agent_input.setText("reviewer")
        main_window.verbose_checkbox.setChecked(True)
        main_window.debug_checkbox.setChecked(False)

        # Save settings
        main_window.save_cli_params()

        # Create new window to test loading
        new_window = MainWindow()
        qtbot.addWidget(new_window)
        new_window.load_cli_params()

        # Verify parameters were loaded
        assert new_window.model_checkbox.isChecked()
        assert new_window.model_combo.currentText() == "opus"
        assert new_window.agent_checkbox.isChecked()
        assert new_window.agent_input.text() == "reviewer"
        assert new_window.verbose_checkbox.isChecked()
        assert not new_window.debug_checkbox.isChecked()

        # Cleanup
        new_window.config_manager.clear_cli_params()

    def test_build_cli_params_from_checkboxes(self, main_window):
        """Test building CLI parameters string from checkboxes."""
        # Set some parameters
        main_window.model_checkbox.setChecked(True)
        main_window.model_combo.setCurrentText("opus")
        main_window.verbose_checkbox.setChecked(True)

        # Build params string
        params = main_window.build_cli_params_from_checkboxes()

        # Verify
        assert "--model opus" in params
        assert "--verbose" in params
        assert "--agent" not in params  # Not checked

    def test_checkbox_enables_input(self, main_window, qtbot):
        """Test that checking a checkbox enables its input widget."""
        # Initially disabled
        assert not main_window.model_combo.isEnabled()
        assert not main_window.agent_input.isEnabled()

        # Check model checkbox
        main_window.model_checkbox.setChecked(True)
        qtbot.wait(10)  # Wait for signal processing
        assert main_window.model_combo.isEnabled()

        # Check agent checkbox
        main_window.agent_checkbox.setChecked(True)
        qtbot.wait(10)
        assert main_window.agent_input.isEnabled()


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
