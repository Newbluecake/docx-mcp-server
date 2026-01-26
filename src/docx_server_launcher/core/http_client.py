"""HTTP Client for Launcher-Server communication.

This module provides a robust HTTP client with retry logic for
communicating with the MCP server's REST API.
"""

import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ServerConnectionError(Exception):
    """Exception raised when unable to connect to server."""
    pass


class ServerTimeoutError(Exception):
    """Exception raised when server request times out."""
    pass


class HTTPClient:
    """HTTP client with retry mechanism for server communication.

    Features:
    - Automatic retry on transient errors (500, 502, 503, 504)
    - Exponential backoff strategy
    - Timeout handling
    - Custom exception types for better error handling

    Example:
        >>> client = HTTPClient("http://localhost:8080")
        >>> status = client.get("/api/status")
        >>> print(status)
        {'currentFile': None, 'sessionId': None, ...}
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8080",
        timeout: float = 5.0,
        max_retries: int = 3
    ):
        """Initialize HTTP client with retry configuration.

        Args:
            base_url: Base URL of the server (default: http://127.0.0.1:8080)
            timeout: Request timeout in seconds (default: 5.0)
            max_retries: Maximum number of retry attempts (default: 3)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

        # Create session with retry strategy
        self.session = requests.Session()

        # Configure retry strategy
        # - total: Maximum number of retries
        # - backoff_factor: Exponential backoff (0.5s, 1s, 2s, ...)
        # - status_forcelist: HTTP status codes to retry on
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST"],  # Only retry safe methods
            raise_on_status=False  # Don't raise on retried errors
        )

        # Mount adapter to session
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

        logger.info(f"HTTPClient initialized: {base_url}, timeout={timeout}s, retries={max_retries}")

    def get(self, path: str) -> Dict[str, Any]:
        """Send GET request to server.

        Args:
            path: API path (e.g., "/api/status")

        Returns:
            dict: JSON response from server

        Raises:
            ServerConnectionError: Failed to connect to server
            ServerTimeoutError: Request timed out
            requests.HTTPError: Server returned error status code
        """
        url = f"{self.base_url}{path}"
        logger.debug(f"GET {url}")

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise ServerConnectionError(f"Unable to connect to server at {self.base_url}") from e
        except requests.Timeout as e:
            logger.error(f"Timeout error: {e}")
            raise ServerTimeoutError(f"Request to {url} timed out after {self.timeout}s") from e
        except requests.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in GET request: {e}")
            raise

    def post(self, path: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send POST request to server.

        Args:
            path: API path (e.g., "/api/file/switch")
            data: JSON data to send in request body

        Returns:
            dict: JSON response from server

        Raises:
            ServerConnectionError: Failed to connect to server
            ServerTimeoutError: Request timed out
            requests.HTTPError: Server returned error status code
        """
        url = f"{self.base_url}{path}"
        logger.debug(f"POST {url} with data: {data}")

        try:
            response = self.session.post(url, json=data or {}, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise ServerConnectionError(f"Unable to connect to server at {self.base_url}") from e
        except requests.Timeout as e:
            logger.error(f"Timeout error: {e}")
            raise ServerTimeoutError(f"Request to {url} timed out after {self.timeout}s") from e
        except requests.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in POST request: {e}")
            raise

    def switch_file(self, file_path: str, force: bool = False) -> Dict[str, Any]:
        """Switch to a new active file.

        Args:
            file_path: Path to .docx file
            force: If True, discard unsaved changes

        Returns:
            dict: Server response with currentFile and sessionId

        Raises:
            ServerConnectionError: Failed to connect to server
            ServerTimeoutError: Request timed out
            requests.HTTPError: Server returned error (404, 403, 409, etc.)
        """
        return self.post("/api/file/switch", {"path": file_path, "force": force})

    def get_status(self) -> Dict[str, Any]:
        """Get current server status.

        Returns:
            dict: Status with currentFile, sessionId, hasUnsaved, serverVersion

        Raises:
            ServerConnectionError: Failed to connect to server
            ServerTimeoutError: Request timed out
        """
        return self.get("/api/status")

    def close_session(self, save: bool = False) -> Dict[str, Any]:
        """Close the active session.

        Args:
            save: If True, save document before closing

        Returns:
            dict: Result with success status

        Raises:
            ServerConnectionError: Failed to connect to server
            ServerTimeoutError: Request timed out
        """
        return self.post("/api/session/close", {"save": save})

    def health_check(self) -> Dict[str, Any]:
        """Check server health and version.

        Returns:
            dict: Health info with status, version, transport

        Raises:
            ServerConnectionError: Failed to connect to server
            ServerTimeoutError: Request timed out
        """
        return self.get("/health")
