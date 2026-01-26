import sys
import os
import shutil
import json
import logging
from pathlib import Path
from PyQt6.QtCore import QObject, QProcess, pyqtSignal
from .log_formatter import format_mcp_command, format_log_message

class ServerManager(QObject):
    """
    Manages the lifecycle of two server subprocesses:
    1. MCP Server (SSE mode, port 8000) - for Claude Desktop
    2. HTTP API Server (port 8001) - for Launcher GUI
    """
    server_started = pyqtSignal()
    server_stopped = pyqtSignal()
    server_error = pyqtSignal(str)
    log_received = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        # MCP Server process (SSE mode)
        self.mcp_process = QProcess()
        self.mcp_process.readyReadStandardOutput.connect(lambda: self._handle_stdout(self.mcp_process, "MCP"))
        self.mcp_process.readyReadStandardError.connect(lambda: self._handle_stderr(self.mcp_process, "MCP"))
        self.mcp_process.started.connect(lambda: self._handle_started("MCP"))
        self.mcp_process.finished.connect(lambda code, status: self._handle_finished(code, status, "MCP"))
        self.mcp_process.errorOccurred.connect(lambda error: self._handle_error(error, "MCP"))

        # HTTP API Server process
        self.http_process = QProcess()
        self.http_process.readyReadStandardOutput.connect(lambda: self._handle_stdout(self.http_process, "HTTP"))
        self.http_process.readyReadStandardError.connect(lambda: self._handle_stderr(self.http_process, "HTTP"))
        self.http_process.started.connect(lambda: self._handle_started("HTTP"))
        self.http_process.finished.connect(lambda code, status: self._handle_finished(code, status, "HTTP"))
        self.http_process.errorOccurred.connect(lambda error: self._handle_error(error, "HTTP"))

        self.logger = logging.getLogger(__name__)
        self._mcp_started = False
        self._http_started = False

    def start_server(self, host: str, port: int, cwd: str, log_level: str = "INFO", extra_env: dict = None):
        """
        Start both MCP server (SSE mode) and HTTP API server.

        Args:
            host: Host interface to bind to (e.g., '127.0.0.1' or '0.0.0.0')
            port: Base port for MCP server (HTTP API will use port+1)
                  e.g., port=8000 → MCP on 8000, HTTP API on 8001
            cwd: Working directory for the servers
            log_level: Log level to pass to servers (DEBUG/INFO/WARNING/ERROR/CRITICAL)
            extra_env: Optional dictionary of environment variables to set
        """
        if self.mcp_process.state() != QProcess.ProcessState.NotRunning:
            self.log_received.emit("Servers are already running.")
            return

        normalized_level = (log_level or "INFO").upper()
        mcp_port = port
        http_port = port + 1

        # Prepare environment
        env = QProcess().processEnvironment()
        env.insert("PYTHONIOENCODING", "utf-8:strict")
        if extra_env:
            for key, value in extra_env.items():
                env.insert(key, str(value))

        # ===== Start MCP Server (SSE mode) =====
        if getattr(sys, 'frozen', False):
            mcp_program = sys.executable
            mcp_args = [
                "--server-mode",
                "--transport", "sse",
                "--port", str(mcp_port),
                "--host", host,
                "--log-level", normalized_level,
            ]
        else:
            mcp_program = sys.executable
            mcp_args = [
                "-m", "docx_mcp_server.server",
                "--transport", "sse",
                "--port", str(mcp_port),
                "--host", host,
                "--log-level", normalized_level,
            ]

        self.mcp_process.setWorkingDirectory(cwd)
        self.mcp_process.setProcessEnvironment(env)

        self.log_received.emit(f"Starting MCP server (SSE) on port {mcp_port}...")
        self.log_received.emit(f"Command: {mcp_program} {' '.join(mcp_args)}")
        self.mcp_process.start(mcp_program, mcp_args)

        # ===== Start HTTP API Server =====
        if getattr(sys, 'frozen', False):
            http_program = sys.executable
            http_args = [
                "--http-api-mode",
                "--port", str(http_port),
                "--host", host,
                "--log-level", normalized_level,
            ]
        else:
            http_program = sys.executable
            http_args = [
                "-m", "docx_mcp_server.http_api_server",
                "--port", str(http_port),
                "--host", host,
            ]

        self.http_process.setWorkingDirectory(cwd)
        self.http_process.setProcessEnvironment(env)

        self.log_received.emit(f"Starting HTTP API server on port {http_port}...")
        self.log_received.emit(f"Command: {http_program} {' '.join(http_args)}")
        self.http_process.start(http_program, http_args)

    def stop_server(self):
        """Stop both running servers."""
        self.log_received.emit("Stopping servers...")

        # Stop HTTP API server
        if self.http_process.state() != QProcess.ProcessState.NotRunning:
            self.http_process.terminate()
            if not self.http_process.waitForFinished(3000):
                self.http_process.kill()

        # Stop MCP server
        if self.mcp_process.state() != QProcess.ProcessState.NotRunning:
            self.mcp_process.terminate()
            if not self.mcp_process.waitForFinished(3000):
                self.mcp_process.kill()

    def _handle_stdout(self, process: QProcess, prefix: str):
        data = process.readAllStandardOutput().data().decode('utf-8', errors='replace')
        if data:
            # Prefix log lines with [MCP] or [HTTP] for clarity
            for line in data.strip().split('\n'):
                if line.strip():
                    self.log_received.emit(f"[{prefix}] {line}")

    def _handle_stderr(self, process: QProcess, prefix: str):
        data = process.readAllStandardError().data().decode('utf-8', errors='replace')
        if data:
            for line in data.strip().split('\n'):
                if line.strip():
                    self.log_received.emit(f"[{prefix}] {line}")

    def _handle_started(self, server_type: str):
        if server_type == "MCP":
            self._mcp_started = True
        elif server_type == "HTTP":
            self._http_started = True

        self.log_received.emit(f"{server_type} server process started successfully.")

        # Emit server_started signal only when both servers are running
        if self._mcp_started and self._http_started:
            self.server_started.emit()

    def _handle_finished(self, exit_code: int, exit_status, server_type: str):
        if server_type == "MCP":
            self._mcp_started = False
        elif server_type == "HTTP":
            self._http_started = False

        self.log_received.emit(f"{server_type} server process finished with code {exit_code}.")

        # Emit server_stopped signal when both servers have stopped
        if not self._mcp_started and not self._http_started:
            self.server_stopped.emit()

    def _handle_error(self, error, server_type: str):
        # Get the appropriate process
        process = self.mcp_process if server_type == "MCP" else self.http_process
        error_msg = process.errorString()
        self.server_error.emit(f"{server_type}: {error_msg}")
        self.log_received.emit(f"Error ({server_type}): {error_msg}")
