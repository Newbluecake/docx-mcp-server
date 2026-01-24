"""
Unit tests for CLILauncher module.
"""

import pytest
from pathlib import Path
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
