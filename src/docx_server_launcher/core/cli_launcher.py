"""
CLI Launcher for Claude Desktop Integration.

This module provides functionality to launch Claude CLI with MCP configuration,
replacing the previous config file injection approach.
"""

import json
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from logging.handlers import RotatingFileHandler


class CLILauncher:
    """
    Manages Claude CLI launching with MCP configuration.

    This class handles:
    - Claude CLI detection
    - MCP configuration generation
    - Command building and execution
    - Launch logging with rotation
    """

    def __init__(self, log_dir: str = "~/.docx-launcher"):
        """
        Initialize CLI launcher.

        Args:
            log_dir: Directory for launch logs (default: ~/.docx-launcher)
        """
        self.log_dir = Path(log_dir).expanduser().resolve()
        self.log_file = self.log_dir / "launch.log"

        # CLI detection cache (5-minute TTL)
        self._cli_path_cache: Optional[str] = None
        self._cache_time: Optional[float] = None
        self._cache_ttl = 300  # 5 minutes

        # Ensure log directory exists
        self._ensure_log_dir()

        # Setup logger
        self._setup_logger()

    def _ensure_log_dir(self) -> None:
        """Create log directory if it doesn't exist."""
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            # Set restrictive permissions (owner read/write only)
            os.chmod(self.log_dir, 0o700)
        except Exception as e:
            # Log directory creation failure shouldn't block initialization
            print(f"Warning: Failed to create log directory: {e}")

    def _setup_logger(self) -> None:
        """Setup rotating file handler for launch logging."""
        self.logger = logging.getLogger("CLILauncher")
        self.logger.setLevel(logging.INFO)

        # Remove existing handlers
        self.logger.handlers.clear()

        try:
            # Rotating file handler (10MB max, 3 backups)
            handler = RotatingFileHandler(
                self.log_file,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=3
            )

            # Set log format
            formatter = logging.Formatter(
                '[%(asctime)s] %(levelname)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)

            self.logger.addHandler(handler)

            # Set file permissions
            if self.log_file.exists():
                os.chmod(self.log_file, 0o600)

        except Exception as e:
            # Logging setup failure shouldn't block initialization
            print(f"Warning: Failed to setup logger: {e}")
