"""
Unit tests for CLILauncher module.
"""

import pytest
import time
from pathlib import Path
from unittest.mock import patch
from docx_server_launcher.core.cli_launcher import CLILauncher


class TestCLILauncherInit:
    """Test CLILauncher initialization."""

    def test_cli_launcher_init(self, tmp_path):
        """Test basic initialization."""
        launcher = CLILauncher(log_dir=str(tmp_path))

        assert launcher.log_dir.exists()
        assert launcher.log_dir == tmp_path.resolve()
        assert launcher.log_file.name == "launch.log"
        assert launcher.log_file.parent == tmp_path.resolve()

    def test_log_dir_creation(self, tmp_path):
        """Test log directory is created if it doesn't exist."""
        log_dir = tmp_path / "subdir" / "logs"
        launcher = CLILauncher(log_dir=str(log_dir))

        assert log_dir.exists()
        assert launcher.log_dir == log_dir.resolve()

    def test_log_dir_expansion(self):
        """Test tilde expansion in log directory path."""
        launcher = CLILauncher(log_dir="~/.docx-launcher")

        assert "~" not in str(launcher.log_dir)
        assert launcher.log_dir.is_absolute()

    def test_logger_setup(self, tmp_path):
        """Test logger is properly configured."""
        launcher = CLILauncher(log_dir=str(tmp_path))

        assert launcher.logger is not None
        assert launcher.logger.name == "CLILauncher"
        assert len(launcher.logger.handlers) > 0

    def test_cache_initialization(self, tmp_path):
        """Test CLI path cache is initialized."""
        launcher = CLILauncher(log_dir=str(tmp_path))

        assert launcher._cli_path_cache is None
        assert launcher._cache_time is None
        assert launcher._cache_ttl == 300


class TestCLIDetection:
    """Test Claude CLI detection."""

    def test_is_claude_cli_available_found(self, tmp_path):
        """Test CLI detection when Claude is found."""
        with patch("shutil.which", return_value="/usr/bin/claude"):
            launcher = CLILauncher(log_dir=str(tmp_path))
            is_available, path = launcher.is_claude_cli_available()

            assert is_available is True
            assert path == "/usr/bin/claude"

    def test_is_claude_cli_available_not_found(self, tmp_path):
        """Test CLI detection when Claude is not found."""
        with patch("shutil.which", return_value=None):
            launcher = CLILauncher(log_dir=str(tmp_path))
            is_available, msg = launcher.is_claude_cli_available()

            assert is_available is False
            assert "not found" in msg.lower()

    def test_cli_detection_caching(self, tmp_path):
        """Test that CLI detection results are cached."""
        with patch("shutil.which", return_value="/usr/bin/claude") as mock_which:
            launcher = CLILauncher(log_dir=str(tmp_path))

            # First call
            is_available1, path1 = launcher.is_claude_cli_available()
            assert mock_which.call_count == 1

            # Second call (should use cache)
            is_available2, path2 = launcher.is_claude_cli_available()
            assert mock_which.call_count == 1  # Not called again

            assert is_available1 == is_available2
            assert path1 == path2

    def test_cli_detection_cache_expiry(self, tmp_path):
        """Test that cache expires after TTL."""
        with patch("shutil.which", return_value="/usr/bin/claude") as mock_which:
            launcher = CLILauncher(log_dir=str(tmp_path))
            launcher._cache_ttl = 0.1  # 100ms TTL for testing

            # First call
            launcher.is_claude_cli_available()
            assert mock_which.call_count == 1

            # Wait for cache to expire
            time.sleep(0.15)

            # Second call (cache expired, should call again)
            launcher.is_claude_cli_available()
            assert mock_which.call_count == 2

    def test_cli_detection_cache_cleared_on_failure(self, tmp_path):
        """Test that cache is cleared when CLI not found."""
        launcher = CLILauncher(log_dir=str(tmp_path))
        launcher._cache_ttl = 0.1  # Short TTL for testing

        # First call succeeds and sets cache
        with patch("shutil.which", return_value="/usr/bin/claude"):
            launcher.is_claude_cli_available()
            assert launcher._cli_path_cache == "/usr/bin/claude"

        # Wait for cache to expire
        time.sleep(0.15)

        # Second call fails and should clear cache
        with patch("shutil.which", return_value=None):
            is_available, msg = launcher.is_claude_cli_available()

            assert is_available is False
            assert launcher._cli_path_cache is None
            assert launcher._cache_time is None


