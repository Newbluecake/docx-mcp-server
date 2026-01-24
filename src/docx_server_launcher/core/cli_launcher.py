"""
CLI Launcher for Claude Desktop Integration.

This module provides functionality to launch Claude CLI with MCP configuration,
replacing the previous config file injection approach.
"""

import json
import logging
import os
import shlex
import shutil
import time
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
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

    def is_claude_cli_available(self) -> Tuple[bool, str]:
        """
        Check if Claude CLI is installed.

        Uses caching to avoid repeated filesystem lookups (5-minute TTL).

        Returns:
            Tuple of (is_available, path_or_error_message)
            - If available: (True, "/path/to/claude")
            - If not available: (False, "Claude CLI not found in PATH")
        """
        now = time.time()

        # Check cache
        if self._cli_path_cache and self._cache_time:
            if now - self._cache_time < self._cache_ttl:
                return True, self._cli_path_cache

        # Perform detection
        cli_path = shutil.which("claude")

        if cli_path:
            # Update cache
            self._cli_path_cache = cli_path
            self._cache_time = now
            return True, cli_path
        else:
            # Clear cache on failure
            self._cli_path_cache = None
            self._cache_time = None
            return False, "Claude CLI not found in PATH"

    def generate_mcp_config(self, server_url: str, transport: str) -> Dict[str, Any]:
        """
        Generate MCP configuration dictionary.

        Args:
            server_url: MCP server URL (e.g., http://127.0.0.1:8000/sse)
            transport: Transport type (sse, stdio, streamable-http)

        Returns:
            MCP configuration dictionary

        Raises:
            ValueError: If transport is 'stdio' (not supported for CLI launch)
        """
        # STDIO transport not supported for CLI launch
        if transport.lower() == "stdio":
            raise ValueError(
                "STDIO transport not supported for CLI launch. "
                "Use SSE or Streamable HTTP instead."
            )

        # Generate MCP config structure
        config = {
            "mcpServers": {
                "docx-server": {
                    "url": server_url,
                    "transport": transport
                }
            }
        }

        return config

    def build_command(self, mcp_config: Dict[str, Any], extra_params: str = "") -> List[str]:
        """
        Build Claude CLI command with MCP config.

        Args:
            mcp_config: MCP configuration dictionary
            extra_params: Additional CLI parameters (e.g., "--model opus")

        Returns:
            Command as list of strings

        Raises:
            ValueError: If extra_params cannot be parsed
        """
        # Build base command
        cmd = ["claude", "--mcp-config", json.dumps(mcp_config)]

        # Parse and append extra parameters
        if extra_params and extra_params.strip():
            try:
                parsed_params = shlex.split(extra_params.strip())
                cmd.extend(parsed_params)
            except ValueError as e:
                raise ValueError(f"Failed to parse extra parameters: {e}")

        return cmd



