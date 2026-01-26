import pytest
import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from unittest.mock import patch, MagicMock
from docx_server_launcher.gui.main_window import MainWindow

# Skip GUI tests if running in headless environment without display
# (Though xvfb/offscreen platform plugin handles this usually)

@pytest.fixture
def app(qtbot):
    """Create the main window for testing."""
    # Ensure QApplication exists
    if not QApplication.instance():
        qapp = QApplication(sys.argv)

    with patch("docx_server_launcher.gui.main_window.QSettings") as mock_settings:
        # Mock settings to avoid file I/O during tests
        settings_instance = MagicMock()
        mock_settings.return_value = settings_instance

        # Configure side_effect to return defaults based on key
        def get_setting(key, default=None, type=None):
            return default

        settings_instance.value.side_effect = get_setting

        window = MainWindow()
        qtbot.addWidget(window)
        return window

def test_command_display_initial_state(app):
    """Test the initial state of the command display."""
    # Force update since it's debounced in __init__
    app._update_timer.stop()
    app._do_update_command_display()

    # Should display default command
    cmd = app.command_display.text()
    assert "claude" in cmd
    assert "127.0.0.1" in cmd  # Default host
    assert "8000" in cmd       # Default port
    assert app.command_display.isReadOnly()
    assert app.copy_btn.isEnabled()
    assert app.copy_btn.text() == "Copy Command"

def test_command_update_on_port_change(app, qtbot):
    """Test that command updates when port changes."""
    # Change port
    app.port_input.setValue(9000)

    # Trigger debounce immediately
    app._update_timer.stop()
    app._do_update_command_display()

    cmd = app.command_display.text()
    assert "9000" in cmd
    assert "8000" not in cmd

def test_command_update_on_lan_change(app, qtbot):
    """Test that command updates when LAN checkbox changes."""
    # Check LAN (host becomes 0.0.0.0)
    app.lan_checkbox.setChecked(True)

    # Trigger debounce immediately
    app._update_timer.stop()
    app._do_update_command_display()

    cmd = app.command_display.text()
    assert "0.0.0.0" in cmd
    assert "127.0.0.1" not in cmd

def test_command_update_on_extra_params(app, qtbot):
    """Test that command updates when extra params change."""
    params = "--dangerously-skip-permission"
    app.cli_params_input.setText(params)

    # Trigger debounce immediately
    app._update_timer.stop()
    app._do_update_command_display()

    cmd = app.command_display.text()
    assert params in cmd

def test_copy_command(app, qtbot):
    """Test copy button functionality."""
    # Mock clipboard
    with patch.object(QApplication, "clipboard") as mock_clipboard:
        clipboard_instance = MagicMock()
        mock_clipboard.return_value = clipboard_instance

        # Click copy button
        qtbot.mouseClick(app.copy_btn, Qt.MouseButton.LeftButton)

        # Check clipboard text set
        cmd = app.command_display.text()
        clipboard_instance.setText.assert_called_with(cmd)

        # Check visual feedback
        assert app.copy_btn.text() == "Copied!"
        assert not app.copy_btn.isEnabled()

def test_copy_button_reset(app, qtbot):
    """Test that copy button resets after timeout."""
    # Set to copied state
    app.copy_btn.setText("Copied!")
    app.copy_btn.setEnabled(False)

    # Call reset directly
    app._reset_copy_button("Copy Command")

    assert app.copy_btn.text() == "Copy Command"
    assert app.copy_btn.isEnabled()
