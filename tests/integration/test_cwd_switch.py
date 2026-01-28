import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# Force offscreen platform before creating QApplication
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# CRITICAL FIX: Mock QMessageBox BEFORE importing MainWindow
# This prevents modal dialogs from blocking tests
from PyQt6.QtWidgets import QMessageBox
QMessageBox.information = MagicMock(return_value=QMessageBox.StandardButton.Ok)
QMessageBox.critical = MagicMock(return_value=QMessageBox.StandardButton.Ok)
QMessageBox.warning = MagicMock(return_value=QMessageBox.StandardButton.Ok)

from docx_server_launcher.gui.main_window import MainWindow

@pytest.fixture
def main_window(qtbot):
    # Mock settings to avoid polluting user config
    with patch('PyQt6.QtCore.QSettings') as MockSettings:
        # Configure mock settings to behave like a dict
        settings_store = {}
        mock_instance = MockSettings.return_value

        def set_value(key, value):
            settings_store[key] = value

        def value(key, default=None):
            return settings_store.get(key, default)

        mock_instance.setValue.side_effect = set_value
        mock_instance.value.side_effect = value

        window = MainWindow()

        # CRITICAL FIX: Mock wait methods to prevent QEventLoop blocking
        window._wait_for_server_stop = MagicMock(return_value=True)
        window._wait_for_server_start = MagicMock(return_value=True)

        qtbot.addWidget(window)
        yield window
        window.close()

@pytest.mark.timeout(5)  # Add timeout to prevent infinite hang
def test_switch_cwd_server_stopped(main_window, qtbot):
    """Test switching directory when server is stopped"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Perform switch (QMessageBox already mocked at module level)
        main_window.switch_cwd(tmpdir)

        # Verify UI updated
        expected_path = str(Path(tmpdir).resolve())
        assert main_window.cwd_input.text() == expected_path

        # Verify history updated
        history = main_window.cwd_manager.get_history()
        assert expected_path in history

@pytest.mark.timeout(5)  # Add timeout to prevent infinite hang
def test_switch_cwd_invalid_directory(main_window, qtbot):
    """Test switching to invalid directory"""
    original_cwd = main_window.cwd_input.text()

    # Perform switch to non-existent path (QMessageBox already mocked at module level)
    main_window.switch_cwd("/nonexistent/path/xyz")

    # Verify UI NOT updated
    assert main_window.cwd_input.text() == original_cwd

@pytest.mark.timeout(5)  # Add timeout to prevent infinite hang
def test_switch_cwd_server_running(main_window, qtbot):
    """Test switching directory when server is running (simulated)"""
    # Simulate running state
    main_window.start_btn.setText("Stop Server")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock dependencies to avoid actual server operations
        main_window.server_manager.stop_server = MagicMock()
        main_window.server_manager.start_server = MagicMock()

        # Note: wait methods already mocked in fixture

        # Perform switch (QMessageBox already mocked at module level)
        main_window.switch_cwd(tmpdir)

        # Verify stop called
        main_window.server_manager.stop_server.assert_called_once()

        # Verify start called with new path
        expected_path = str(Path(tmpdir).resolve())
        main_window.server_manager.start_server.assert_called_once()
        args = main_window.server_manager.start_server.call_args
        assert args[0][2] == expected_path  # 3rd arg is cwd
