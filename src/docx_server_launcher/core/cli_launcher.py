"""
CLI Launcher for Claude Desktop Integration.

This module provides functionality to launch Claude CLI with MCP configuration,
replacing the previous config file injection approach.
"""

import json
import logging
import os
import platform
import re
import shlex
import shutil
import socket
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
from logging.handlers import RotatingFileHandler
from .log_formatter import format_cli_command, format_log_message


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

    def get_lan_ip(self) -> str:
        """
        Get the LAN IP address of the current machine.

        Returns:
            LAN IP address (e.g., "192.168.1.100") or "127.0.0.1" if detection fails
        """
        try:
            # Create a UDP socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Connect to a public DNS server (doesn't actually send data)
            s.connect(("8.8.8.8", 80))
            # Get the socket's own address
            lan_ip = s.getsockname()[0]
            s.close()
            return lan_ip
        except Exception:
            # Fallback to localhost if detection fails
            return "127.0.0.1"

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

    def build_command(self, server_url: str, transport: str = "sse", extra_params: str = "") -> List[str]:
        """
        Build Claude MCP add command.

        Args:
            server_url: MCP server URL (e.g., http://192.168.1.100:8000/sse)
            transport: Transport type (default: "sse")
            extra_params: Additional CLI parameters (e.g., "--dangerously-skip-permission")

        Returns:
            Command as list of strings

        Raises:
            ValueError: If extra_params cannot be parsed
        """
        # Build base command: claude mcp add --transport sse docx <url>
        base_cmd = ["claude", "mcp", "add", "--transport", transport, "docx", server_url]

        # Parse and append extra parameters
        if extra_params and extra_params.strip():
            try:
                parsed_params = shlex.split(extra_params.strip())
                base_cmd.extend(parsed_params)
            except ValueError as e:
                raise ValueError(f"Failed to parse extra parameters: {e}")

        # On Windows, wrap with cmd.exe to ensure proper execution
        if platform.system() == "Windows":
            cmd = ["cmd.exe", "/c"] + base_cmd
        else:
            cmd = base_cmd

        return cmd

    def validate_cli_params(self, params: str) -> Tuple[bool, str]:
        """
        Validate CLI parameters for safety.

        Checks for:
        - Dangerous shell metacharacters
        - Parse errors (unclosed quotes, etc.)

        Args:
            params: CLI parameters to validate

        Returns:
            Tuple of (is_valid, error_message)
            - If valid: (True, "")
            - If invalid: (False, "Error description")
        """
        if not params or not params.strip():
            return True, ""

        # Check for dangerous shell metacharacters
        dangerous_chars = [";", "&", "|", "`", "$", "(", ")", "<", ">", "\n", "\r"]
        for char in dangerous_chars:
            if char in params:
                return False, f"Invalid character '{char}' in parameters. Shell metacharacters are not allowed."

        # Try parsing with shlex to catch syntax errors
        try:
            shlex.split(params)
        except ValueError as e:
            return False, f"Parameter parse error: {e}"

        return True, ""

    def sanitize_for_log(self, params: str) -> str:
        """
        Sanitize parameters for logging by redacting sensitive data.

        Args:
            params: Parameters to sanitize

        Returns:
            Sanitized parameters string
        """
        if not params:
            return params

        # Redact API keys
        sanitized = re.sub(
            r'--api-key\s+\S+',
            '--api-key [REDACTED]',
            params,
            flags=re.IGNORECASE
        )

        # Redact tokens
        sanitized = re.sub(
            r'--token\s+\S+',
            '--token [REDACTED]',
            sanitized,
            flags=re.IGNORECASE
        )

        # Redact passwords
        sanitized = re.sub(
            r'--password\s+\S+',
            '--password [REDACTED]',
            sanitized,
            flags=re.IGNORECASE
        )

        return sanitized






