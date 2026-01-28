import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Force offscreen platform before creating QApplication
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# CRITICAL FIX: Mock QMessageBox BEFORE importing MainWindow
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QTimer

QMessageBox.information = MagicMock(return_value=QMessageBox.StandardButton.Ok)
QMessageBox.critical = MagicMock(return_value=QMessageBox.StandardButton.Ok)
QMessageBox.warning = MagicMock(return_value=QMessageBox.StandardButton.Ok)

from docx_server_launcher.gui.main_window import MainWindow

# Skip GUI tests if running in headless environment without display
# (Though xvfb/offscreen platform plugin handles this usually)

@pytest.fixture
def app(qtbot, request):
    """Create the main window for testing."""
    # Ensure QApplication exists
    qapp = QApplication.instance()
    if not qapp:
        qapp = QApplication(sys.argv)

    # Start the patch
    patcher = patch("docx_server_launcher.gui.main_window.QSettings")
    mock_settings = patcher.start()

    # Mock settings to avoid file I/O during tests
    settings_instance = MagicMock()
    mock_settings.return_value = settings_instance

    # Configure side_effect to return defaults based on key
    def get_setting(key, default=None, type=None):
        return default

    settings_instance.value.side_effect = get_setting

    window = MainWindow()

    # CRITICAL FIX: Mock wait methods to prevent QEventLoop blocking
    window._wait_for_server_stop = MagicMock(return_value=True)
    window._wait_for_server_start = MagicMock(return_value=True)

    qtbot.addWidget(window)

    # Add explicit cleanup
    def cleanup():
        try:
            window.close()
            window.deleteLater()
            qapp.processEvents()
        finally:
            patcher.stop()

    request.addfinalizer(cleanup)

    return window

def test_command_display_initial_state(app):
    """Test the initial state of the command display."""
    # Force update since it's debounced in __init__
    app._update_timer.stop()
    app._do_update_command_display()

    # Should display default command
    cmd = app.command_display.text()
    assert "claude" in cmd
    assert "mcp" in cmd
    assert "add" in cmd
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
    # Check LAN (host becomes actual LAN IP)
    app.lan_checkbox.setChecked(True)

    # Trigger debounce immediately
    app._update_timer.stop()
    app._do_update_command_display()

    cmd = app.command_display.text()
    # Should not contain localhost
    assert "127.0.0.1" not in cmd
    # Should contain some IP (could be actual LAN IP or fallback)
    assert "http://" in cmd

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
    # Force update command display first
    app._update_timer.stop()
    app._do_update_command_display()

    # Mock clipboard, QTimer, and QMessageBox
    with patch.object(QApplication, "clipboard") as mock_clipboard, \
         patch("docx_server_launcher.gui.main_window.QTimer") as mock_timer, \
         patch("docx_server_launcher.gui.main_window.QMessageBox") as mock_msgbox:
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

        # Verify QTimer.singleShot was called
        assert mock_timer.singleShot.called

def test_copy_button_reset(app, qtbot):
    """Test that copy button resets after timeout."""
    # Set to copied state
    app.copy_btn.setText("Copied!")
    app.copy_btn.setEnabled(False)

    # Call reset directly
    app._reset_copy_button("Copy Command")

    assert app.copy_btn.text() == "Copy Command"
    assert app.copy_btn.isEnabled()
