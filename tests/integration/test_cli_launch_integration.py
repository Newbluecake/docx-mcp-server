"""
Integration tests for CLI launch functionality (T-012).

These tests verify the end-to-end integration of CLILauncher with the GUI.
"""

import pytest
import subprocess
import os
from unittest.mock import patch, MagicMock

# Force offscreen platform before creating QApplication
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# CRITICAL FIX: Mock QMessageBox BEFORE importing MainWindow
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QSettings

QMessageBox.information = MagicMock(return_value=QMessageBox.StandardButton.Ok)
QMessageBox.critical = MagicMock(return_value=QMessageBox.StandardButton.Ok)
QMessageBox.warning = MagicMock(return_value=QMessageBox.StandardButton.Ok)

from docx_server_launcher.gui.main_window import MainWindow
from docx_server_launcher.core.cli_launcher import CLILauncher


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't quit the app, let pytest-qt handle it


class TestCLILaunchIntegration:
    """Test CLI launch integration with GUI."""

    def test_cli_launcher_initialized_in_main_window(self, qapp):
        """Test that CLILauncher is properly initialized."""
        window = MainWindow()
        # CRITICAL FIX: Mock wait methods to prevent QEventLoop blocking
        window._wait_for_server_stop = MagicMock(return_value=True)
        window._wait_for_server_start = MagicMock(return_value=True)
        try:
            assert hasattr(window, "cli_launcher")
            assert isinstance(window.cli_launcher, CLILauncher)
        finally:
            window.close()
            window.deleteLater()
            qapp.processEvents()

    def test_settings_persistence_integration(self, qapp, tmp_path):
        """Test that CLI params persist across app restarts."""
        settings_file = str(tmp_path / "test_settings.ini")
        QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path))

        # First window: set and save params
        window1 = MainWindow()
        # CRITICAL FIX: Mock wait methods to prevent QEventLoop blocking
        window1._wait_for_server_stop = MagicMock(return_value=True)
        window1._wait_for_server_start = MagicMock(return_value=True)
        try:
            window1.settings = QSettings(settings_file, QSettings.Format.IniFormat)
            test_params = "--model haiku --fast"
            window1.cli_params_input.setText(test_params)
            window1.save_settings()
        finally:
            window1.close()
            window1.deleteLater()
            qapp.processEvents()

        # Second window: load params
        window2 = MainWindow()
        # CRITICAL FIX: Mock wait methods to prevent QEventLoop blocking
        window2._wait_for_server_stop = MagicMock(return_value=True)
        window2._wait_for_server_start = MagicMock(return_value=True)
        try:
            window2.settings = QSettings(settings_file, QSettings.Format.IniFormat)
            window2.load_settings()

            # Verify params were loaded
            assert window2.cli_params_input.text() == test_params
        finally:
            window2.close()
            window2.deleteLater()
            qapp.processEvents()


class TestCLILauncherEndToEnd:
    """End-to-end tests for CLILauncher."""

    def test_full_launch_workflow(self, tmp_path):
        """Test complete command building workflow."""
        with patch("shutil.which", return_value="/usr/bin/claude"):
            launcher = CLILauncher(log_dir=str(tmp_path))

            # Build command
            cmd_list = launcher.build_command(
                "http://127.0.0.1:8000/sse",
                "sse",
                "--model opus"
            )

            # Verify command construction
            assert cmd_list[0] == "claude"
            assert "mcp" in cmd_list
            assert "add" in cmd_list
            assert "--transport" in cmd_list
            assert "sse" in cmd_list
            assert "docx" in cmd_list
            assert "http://127.0.0.1:8000/sse" in cmd_list
            assert "--model" in cmd_list
            assert "opus" in cmd_list

    def test_launch_with_invalid_transport(self, tmp_path):
        """Test config generation with invalid transport type."""
        with patch("shutil.which", return_value="/usr/bin/claude"):
            launcher = CLILauncher(log_dir=str(tmp_path))

            # Try STDIO (not supported for config generation)
            with pytest.raises(ValueError, match="STDIO transport not supported"):
                launcher.generate_mcp_config("http://localhost", "stdio")

    def test_launch_with_parse_error(self, tmp_path):
        """Test command building with parameter parse error."""
        with patch("shutil.which", return_value="/usr/bin/claude"):
            launcher = CLILauncher(log_dir=str(tmp_path))

            # Invalid params (unclosed quote)
            with pytest.raises(ValueError, match="Failed to parse"):
                launcher.build_command(
                    "http://127.0.0.1:8000/sse",
                    "sse",
                    '--prompt "unclosed'
                )

    def test_security_validation_integration(self, tmp_path):
        """Test security validation in command building."""
        with patch("shutil.which", return_value="/usr/bin/claude"):
            launcher = CLILauncher(log_dir=str(tmp_path))

            # Try various dangerous inputs
            dangerous_inputs = [
                "--model opus; rm -rf /",
                "--model opus && cat /etc/passwd",
                "--model `whoami`",
                "--model $USER",
            ]

            # Note: build_command uses shlex.split which handles some of these,
            # but validate_cli_params should be called before or during.
            # Currently build_command does NOT call validate_cli_params automatically,
            # it relies on shlex.split to parse. shlex.split might succeed on some of these
            # if they are just args, but we want to ensure we catch shell injection attempts
            # if they were passed to a shell.
            # However, CLILauncher.build_command doesn't explicitly validate safety beyond parsing.
            # The GUI calls build_command directly.

            # Let's check what build_command actually does with these.
            # It uses shlex.split, which will interpret these as arguments, not shell commands.
            # So they are "safe" in the sense that they won't execute if passed to subprocess as a list.

            for dangerous in dangerous_inputs:
                # These should strictly fail parsing or be treated as safe args
                # If they contain shell metacharacters that shlex can't handle or
                # if we want to explicitly forbid them.

                # The current CLILauncher implementation has a validate_cli_params method
                # but it's not called by build_command.
                # We should test validate_cli_params directly if we want to test validation,
                # or check if build_command handles them safely (by quoting/splitting).

                is_valid, msg = launcher.validate_cli_params(dangerous)
                assert is_valid is False, f"Should reject: {dangerous}"
                assert "Invalid character" in msg or "parse error" in msg

    def test_log_rotation_integration(self, tmp_path):
        """Test that log rotation is configured."""
        launcher = CLILauncher(log_dir=str(tmp_path))

        # Check rotation config
        from logging.handlers import RotatingFileHandler
        handler = launcher.logger.handlers[0]
        assert isinstance(handler, RotatingFileHandler)
        assert handler.maxBytes == 10 * 1024 * 1024
        assert handler.backupCount == 3
