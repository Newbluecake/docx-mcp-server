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
    Manages the Combined MCP Server lifecycle.

    The server runs in Combined mode (FastAPI + MCP tools) on a single port,
    providing both MCP protocol (/mcp) and HTTP REST API (/api/*) endpoints.
    """
    server_started = pyqtSignal()
    server_stopped = pyqtSignal()
    server_error = pyqtSignal(str)
    log_received = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        # Single process for Combined server
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(lambda: self._handle_stdout(self.process))
        self.process.readyReadStandardError.connect(lambda: self._handle_stderr(self.process))
        self.process.started.connect(self._handle_started)
        self.process.finished.connect(self._handle_finished)
        self.process.errorOccurred.connect(self._handle_error)

        self.logger = logging.getLogger(__name__)

    def start_server(self, host: str, port: int, cwd: str, log_level: str = "INFO", extra_env: dict = None):
        """
        Start Combined MCP server (FastAPI + MCP tools).

        Args:
            host: Host interface to bind to (e.g., '127.0.0.1' or '0.0.0.0')
            port: Port for the combined server (provides both /mcp and /api/* endpoints)
            cwd: Working directory for the server
            log_level: Log level to pass to server (DEBUG/INFO/WARNING/ERROR/CRITICAL)
            extra_env: Optional dictionary of environment variables to set
        """
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.log_received.emit("Server is already running.")
            return

        normalized_level = (log_level or "INFO").upper()

        # Prepare environment
        env = QProcess().processEnvironment()
        env.insert("PYTHONIOENCODING", "utf-8:strict")
        if extra_env:
            for key, value in extra_env.items():
                env.insert(key, str(value))

        # Start Combined Server (FastAPI + MCP)
        if getattr(sys, 'frozen', False):
            program = sys.executable
            args = [
                "--server-mode",
                "--transport", "combined",
                "--port", str(port),
                "--host", host,
                "--log-level", normalized_level,
            ]
        else:
            program = sys.executable
            args = [
                "-m", "docx_mcp_server.server",
                "--transport", "combined",
                "--port", str(port),
                "--host", host,
                "--log-level", normalized_level,
            ]

        self.process.setWorkingDirectory(cwd)
        self.process.setProcessEnvironment(env)

        self.log_received.emit(f"Starting Combined server on port {port}...")
        self.log_received.emit(f"Command: {program} {' '.join(args)}")
        self.process.start(program, args)

    def stop_server(self):
        """Stop the running server."""
        self.log_received.emit("Stopping server...")

        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.terminate()
            if not self.process.waitForFinished(3000):
                self.process.kill()

    def _handle_stdout(self, process: QProcess):
        data = process.readAllStandardOutput().data().decode('utf-8', errors='replace')
        if data:
            for line in data.strip().split('\n'):
                if line.strip():
                    self.log_received.emit(line)

    def _handle_stderr(self, process: QProcess):
        data = process.readAllStandardError().data().decode('utf-8', errors='replace')
        if data:
            for line in data.strip().split('\n'):
                if line.strip():
                    self.log_received.emit(line)

    def _handle_started(self):
        self.log_received.emit("Server process started successfully.")
        self.server_started.emit()

    def _handle_finished(self, exit_code: int, exit_status):
        self.log_received.emit(f"Server process finished with code {exit_code}.")
        self.server_stopped.emit()

    def _handle_error(self, error):
        error_msg = self.process.errorString()
        self.server_error.emit(error_msg)
        self.log_received.emit(f"Error: {error_msg}")
