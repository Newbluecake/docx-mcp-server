import sys
import os
import shutil
from pathlib import Path
from PyQt6.QtCore import QObject, QProcess, pyqtSignal

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

    def start_server(self, host: str, port: int, cwd: str):
        """
        Start the docx-mcp-server process.

        Args:
            host: Host interface to bind to (e.g., '127.0.0.1')
            port: Port to listen on (e.g., 8000)
            cwd: Working directory for the server (where it will look for files)
        """
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.log_received.emit("Server is already running.")
            return

        # Determine Python interpreter path
        if getattr(sys, 'frozen', False):
            # Packaged environment: find system Python
            python_exe = shutil.which('python') or shutil.which('python3')
            if not python_exe:
                self.server_error.emit(
                    "Cannot find Python interpreter in PATH.\n"
                    "Please install Python 3.10+ and add it to PATH."
                )
                return
            program = python_exe
        else:
            # Development environment: use current Python interpreter
            program = sys.executable

        args = [
            "-m", "docx_mcp_server.server",
            "--transport", "sse",
            "--port", str(port),
            "--host", host
        ]

        self.process.setWorkingDirectory(cwd)

        # Merge environment if needed
        env = self.process.processEnvironment()
        # env.insert("SOME_VAR", "VALUE")
        self.process.setProcessEnvironment(env)

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
