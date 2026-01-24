"""
Integration tests for CLI launch functionality (T-012).

These tests verify the end-to-end integration of CLILauncher with the GUI.
"""

import pytest
import subprocess
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings
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
        assert hasattr(window, "cli_launcher")
        assert isinstance(window.cli_launcher, CLILauncher)

    def test_settings_persistence_integration(self, qapp, tmp_path):
        """Test that CLI params persist across app restarts."""
        settings_file = str(tmp_path / "test_settings.ini")
        QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path))

        # First window: set and save params
        window1 = MainWindow()
        window1.settings = QSettings(settings_file, QSettings.Format.IniFormat)
        test_params = "--model haiku --fast"
        window1.cli_params_input.setText(test_params)
        window1.save_settings()

        # Second window: load params
        window2 = MainWindow()
        window2.settings = QSettings(settings_file, QSettings.Format.IniFormat)
        window2.load_settings()

        # Verify params were loaded
        assert window2.cli_params_input.text() == test_params


class TestCLILauncherEndToEnd:
    """End-to-end tests for CLILauncher."""

    def test_full_launch_workflow(self, tmp_path):
        """Test complete launch workflow."""
        with patch("shutil.which", return_value="/usr/bin/claude"):
            with patch("subprocess.Popen") as mock_popen:
                mock_process = MagicMock()
                mock_process.pid = 99999
                mock_popen.return_value = mock_process

                launcher = CLILauncher(log_dir=str(tmp_path))

                # Execute launch
                success, msg = launcher.launch(
                    "http://127.0.0.1:8000/sse",
                    "sse",
                    "--model opus"
                )

                # Verify success
                assert success is True
                assert "99999" in msg

                # Verify command construction
                call_args = mock_popen.call_args[0][0]
                assert call_args[0] == "claude"
                assert "--mcp-config" in call_args
                assert "--model" in call_args
                assert "opus" in call_args

                # Verify log file
                log_file = tmp_path / "launch.log"
                assert log_file.exists()
                log_content = log_file.read_text()
                assert "Launch Attempt" in log_content
                assert "started successfully" in log_content

    def test_launch_with_invalid_transport(self, tmp_path):
        """Test launch with invalid transport type."""
        with patch("shutil.which", return_value="/usr/bin/claude"):
            launcher = CLILauncher(log_dir=str(tmp_path))

            # Try STDIO (not supported)
            success, msg = launcher.launch("", "stdio", "")

            assert success is False
            assert "not supported" in msg.lower()

    def test_launch_with_parse_error(self, tmp_path):
        """Test launch with parameter parse error."""
        with patch("shutil.which", return_value="/usr/bin/claude"):
            launcher = CLILauncher(log_dir=str(tmp_path))

            # Invalid params (unclosed quote)
            success, msg = launcher.launch(
                "http://127.0.0.1:8000/sse",
                "sse",
                '--prompt "unclosed'
            )

            assert success is False
            assert "parse" in msg.lower()

    def test_security_validation_integration(self, tmp_path):
        """Test security validation in launch workflow."""
        with patch("shutil.which", return_value="/usr/bin/claude"):
            launcher = CLILauncher(log_dir=str(tmp_path))

            # Try various dangerous inputs
            dangerous_inputs = [
                "--model opus; rm -rf /",
                "--model opus && cat /etc/passwd",
                "--model `whoami`",
                "--model $USER",
            ]

            for dangerous in dangerous_inputs:
                success, msg = launcher.launch(
                    "http://127.0.0.1:8000/sse",
                    "sse",
                    dangerous
                )

                assert success is False, f"Should reject: {dangerous}"
                assert "invalid" in msg.lower() or "character" in msg.lower()

    def test_log_rotation_integration(self, tmp_path):
        """Test that log rotation is configured."""
        launcher = CLILauncher(log_dir=str(tmp_path))

        # Check rotation config
        from logging.handlers import RotatingFileHandler
        handler = launcher.logger.handlers[0]
        assert isinstance(handler, RotatingFileHandler)
        assert handler.maxBytes == 10 * 1024 * 1024
        assert handler.backupCount == 3
