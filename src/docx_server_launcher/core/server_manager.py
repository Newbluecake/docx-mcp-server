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
    Manages the lifecycle of the docx-mcp-server subprocess.
    """
    server_started = pyqtSignal()
    server_stopped = pyqtSignal()
    server_error = pyqtSignal(str)
    log_received = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self._handle_stdout)
        self.process.readyReadStandardError.connect(self._handle_stderr)
        self.process.started.connect(self._handle_started)
        self.process.finished.connect(self._handle_finished)
        self.process.errorOccurred.connect(self._handle_error)
        self.logger = logging.getLogger(__name__)

    def start_server(self, host: str, port: int, cwd: str, log_level: str = "INFO", extra_env: dict = None):
        """
        Start the docx-mcp-server process.

        Args:
            host: Host interface to bind to (e.g., '127.0.0.1')
            port: Port to listen on (e.g., 8000)
            cwd: Working directory for the server (where it will look for files)
            log_level: Log level to pass to the server (DEBUG/INFO/WARNING/ERROR/CRITICAL)
            extra_env: Optional dictionary of environment variables to set
        """
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.log_received.emit("Server is already running.")
            return

        normalized_level = (log_level or "INFO").upper()

        # Determine program and args
        if getattr(sys, 'frozen', False):
            # Packaged environment: run the executable itself in server mode
            program = sys.executable
            args = [
                "--server-mode",
                "--transport", "combined",
                "--port", str(port),
                "--host", host,
                "--log-level", normalized_level,
            ]
        else:
            # Development environment: use current Python interpreter
            program = sys.executable
            args = [
                "-m", "docx_mcp_server.server",
                "--transport", "combined",
                "--port", str(port),
                "--host", host,
                "--log-level", normalized_level,
            ]

        self.process.setWorkingDirectory(cwd)

        # Merge environment if needed
        env = self.process.processEnvironment()
        # Force UTF-8 encoding for Python subprocess output
        env.insert("PYTHONIOENCODING", "utf-8:strict")

        if extra_env:
            for key, value in extra_env.items():
                env.insert(key, str(value))

        self.process.setProcessEnvironment(env)

        # Log the startup command in structured format
        log_data = format_mcp_command(program, args)
        log_message = format_log_message(log_data)
        self.logger.info(log_message)

        self.log_received.emit(f"Starting server in {cwd}...")
        self.log_received.emit(f"Command: {program} {' '.join(args)}")

        self.process.start(program, args)

    def stop_server(self):
        """Stop the running server."""
        if self.process.state() == QProcess.ProcessState.NotRunning:
            return

        self.log_received.emit("Stopping server...")
        self.process.terminate()
        # Give it a moment to shut down gracefully
        if not self.process.waitForFinished(3000):
            self.process.kill()

    def _handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode('utf-8', errors='replace')
        if data:
            self.log_received.emit(data)

    def _handle_stderr(self):
        data = self.process.readAllStandardError().data().decode('utf-8', errors='replace')
        if data:
            self.log_received.emit(data)

    def _handle_started(self):
        self.server_started.emit()
        self.log_received.emit("Server process started successfully.")

    def _handle_finished(self, exit_code, exit_status):
        self.server_stopped.emit()
        self.log_received.emit(f"Server process finished with code {exit_code}.")

    def _handle_error(self, error):
        error_msg = self.process.errorString()
        self.server_error.emit(error_msg)
        self.log_received.emit(f"Error: {error_msg}")
