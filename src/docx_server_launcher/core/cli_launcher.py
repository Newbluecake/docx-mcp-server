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
import subprocess
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

    def _log_launch(self, command: List[str], mcp_config: Dict[str, Any],
                    success: bool, error: str = "", pid: Optional[int] = None) -> None:
        """
        Log launch attempt to file.

        Args:
            command: Command that was executed
            mcp_config: MCP configuration used
            success: Whether launch was successful
            error: Error message (if failed)
            pid: Process ID (if successful)
        """
        try:
            self.logger.info("=" * 40)
            self.logger.info("Launch Attempt")
            self.logger.info(f"Command: {' '.join(command)}")
            self.logger.info(f"MCP Config: {json.dumps(mcp_config)}")

            if success:
                self.logger.info(f"Claude CLI started successfully (PID: {pid})")
            else:
                self.logger.error(f"Launch failed: {error}")

            self.logger.info("=" * 40)
        except Exception as e:
            # Logging failure shouldn't break the launch process
            print(f"Warning: Failed to log launch attempt: {e}")

    def launch(self, server_url: str, transport: str, extra_params: str = "") -> Tuple[bool, str]:
        """
        Launch Claude CLI with MCP configuration.

        Args:
            server_url: MCP server URL (e.g., http://127.0.0.1:8000/sse)
            transport: Transport type (sse, streamable-http)
            extra_params: Additional CLI parameters (e.g., "--model opus")

        Returns:
            Tuple of (success, message_or_error)
            - If successful: (True, "Claude CLI started successfully (PID: 12345)")
            - If failed: (False, "Error message")
        """
        # Check CLI availability
        is_available, cli_path_or_error = self.is_claude_cli_available()
        if not is_available:
            error_msg = cli_path_or_error
            self.logger.error(f"Launch failed: {error_msg}")
            return False, error_msg

        try:
            # Generate MCP config
            mcp_config = self.generate_mcp_config(server_url, transport)

            # Build command
            cmd = self.build_command(mcp_config, extra_params)

            # Launch process (non-blocking)
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )

            # Log success
            self._log_launch(cmd, mcp_config, success=True, pid=process.pid)

            success_msg = f"Claude CLI started successfully (PID: {process.pid})"
            return True, success_msg

        except ValueError as e:
            # Config generation or command building error
            error_msg = str(e)
            self.logger.error(f"Launch failed: {error_msg}")
            return False, error_msg

        except subprocess.SubprocessError as e:
            # Process launch error
            error_msg = f"Failed to launch Claude CLI: {e}"
            self.logger.error(error_msg)
            return False, error_msg

        except Exception as e:
            # Unexpected error
            error_msg = f"Unexpected error during launch: {e}"
            self.logger.exception(error_msg)
            return False, error_msg




