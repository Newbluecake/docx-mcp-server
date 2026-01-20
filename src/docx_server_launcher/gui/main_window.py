import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QSpinBox, QPushButton,
    QGroupBox, QPlainTextEdit, QFileDialog, QMessageBox,
    QCheckBox
)
from PyQt6.QtCore import Qt, QSettings, QEventLoop, QTimer
from docx_server_launcher.core.server_manager import ServerManager
from docx_server_launcher.core.config_injector import ConfigInjector
from docx_server_launcher.core.working_directory_manager import WorkingDirectoryManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Docx MCP Server Launcher")
        self.resize(600, 500)

        self.server_manager = ServerManager()
        self.config_injector = ConfigInjector()
        self.settings = QSettings("DocxMCP", "Launcher")

        self.cwd_manager = WorkingDirectoryManager(self.settings)
        self._is_switching_cwd = False

        self.init_ui()
        self.connect_signals()
        self.load_settings()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Configuration Section ---
        config_group = QGroupBox("Server Configuration")
        config_layout = QVBoxLayout()

        # Working Directory
        cwd_layout = QHBoxLayout()
        cwd_layout.addWidget(QLabel("Working Directory:"))
        self.cwd_input = QLineEdit()
        self.cwd_input.setPlaceholderText(os.getcwd())
        cwd_layout.addWidget(self.cwd_input)
        self.cwd_browse_btn = QPushButton("Browse...")
        cwd_layout.addWidget(self.cwd_browse_btn)

        self.cwd_history_btn = QPushButton("Recent ▼")
        self.cwd_history_btn.setMaximumWidth(100)
        cwd_layout.addWidget(self.cwd_history_btn)

        config_layout.addLayout(cwd_layout)

        # Host and Port
        net_layout = QHBoxLayout()

        # Checkbox for LAN access (controls host)
        self.lan_checkbox = QCheckBox("Allow LAN Access")
        self.lan_checkbox.setToolTip("If checked, the server will listen on 0.0.0.0 (accessible from other devices).\nIf unchecked, it listens on 127.0.0.1 (local only).")
        self.lan_checkbox.stateChanged.connect(self.on_lan_toggled)
        net_layout.addWidget(self.lan_checkbox)

        # Hidden host input for internal logic (optional, or we can just use variable)
        # We can keep self.host_value in state instead of a widget if we want simplicity
        # But previous code used self.host_input.text(). Let's keep a hidden input or just logic?
        # Let's use a hidden input or readonly label for debug?
        # Actually, user wants "checkbox form".
        # Let's remove host_input widget from UI but keep property logic simpler.

        net_layout.addStretch()

        net_layout.addWidget(QLabel("Port:"))
        self.port_input = QSpinBox()
        self.port_input.setRange(1024, 65535)
        self.port_input.setValue(8000)
        net_layout.addWidget(self.port_input)
        config_layout.addLayout(net_layout)

        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)

        # --- Control Section ---
        control_group = QGroupBox("Control")
        control_layout = QHBoxLayout()

        self.status_label = QLabel("Status: Stopped")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        control_layout.addWidget(self.status_label)

        control_layout.addStretch()

        self.start_btn = QPushButton("Start Server")
        control_layout.addWidget(self.start_btn)

        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)

        # --- Integration Section ---
        integration_group = QGroupBox("Claude Desktop Integration")
        integration_layout = QHBoxLayout()

        self.inject_btn = QPushButton("Inject Config to Claude...")
        integration_layout.addWidget(self.inject_btn)

        integration_group.setLayout(integration_layout)
        main_layout.addWidget(integration_group)

        # --- Logs Section ---
        log_group = QGroupBox("Logs")
        log_layout = QVBoxLayout()
        self.log_area = QPlainTextEdit()
        self.log_area.setReadOnly(True)
        log_layout.addWidget(self.log_area)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group, stretch=1)

    def connect_signals(self):
        # UI signals
        self.cwd_browse_btn.clicked.connect(self.browse_cwd)
        self.cwd_history_btn.clicked.connect(self.show_cwd_history)
        self.start_btn.clicked.connect(self.toggle_server)
        self.inject_btn.clicked.connect(self.inject_config)

        # ServerManager signals
        self.server_manager.server_started.connect(self.on_server_started)
        self.server_manager.server_stopped.connect(self.on_server_stopped)
        self.server_manager.log_received.connect(self.append_log)
        self.server_manager.server_error.connect(self.on_server_error)

    def load_settings(self):
        last_cwd = self.settings.value("cwd", os.getcwd())
        if last_cwd:
            self.cwd_input.setText(str(last_cwd))

        last_host = str(self.settings.value("host", "127.0.0.1"))
        self.lan_checkbox.setChecked(last_host == "0.0.0.0")

        last_port = self.settings.value("port", 8000)
        self.port_input.setValue(int(last_port))

    def save_settings(self):
        self.settings.setValue("cwd", self.cwd_input.text())
        host = "0.0.0.0" if self.lan_checkbox.isChecked() else "127.0.0.1"
        self.settings.setValue("host", host)
        self.settings.setValue("port", self.port_input.value())

    def on_lan_toggled(self, state):
        # We don't need to do much immediately, value is read on save/start
        pass

    def browse_cwd(self):
        """Open directory selection dialog"""
        current_dir = self.cwd_input.text() or os.getcwd()
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Working Directory",
            current_dir
        )

        if dir_path:
            # Call new method to handle switching
            self.switch_cwd(dir_path)

    def switch_cwd(self, new_path: str):
        """
        Switch working directory and restart server if running

        Args:
            new_path: New working directory path
        """
        # Prevent concurrent switching
        if self._is_switching_cwd:
            QMessageBox.warning(self, "Warning", "Working directory switch in progress, please wait...")
            return

        # Validate directory
        is_valid, error_msg = self.cwd_manager.validate_directory(new_path)
        if not is_valid:
            QMessageBox.critical(self, "Invalid Directory", error_msg)
            return

        # Normalize path
        normalized_path = str(Path(new_path).resolve())
        current_path = self.cwd_input.text() or os.getcwd()

        # Check if same as current
        if normalized_path == str(Path(current_path).resolve()):
            return  # No change needed

        # Save original cwd for rollback
        original_cwd = current_path

        # Check server status
        is_server_running = (self.start_btn.text() == "Stop Server")

        self._is_switching_cwd = True

        try:
            if is_server_running:
                # Step 1: Stop server
                self.status_label.setText("Status: Stopping server...")
                self.status_label.setStyleSheet("color: orange; font-weight: bold;")
                self._disable_controls()

                # Stop server
                self.server_manager.stop_server()

                # Wait for stop (max 5 seconds)
                if not self._wait_for_server_stop(timeout=5000):
                    raise Exception("Server stop timeout")

            # Step 2: Update UI and Config
            self.cwd_input.setText(normalized_path)
            self.settings.setValue("cwd", normalized_path)
            self.cwd_manager.add_to_history(normalized_path)

            if is_server_running:
                # Step 3: Start server
                self.status_label.setText("Status: Starting server...")
                host = "0.0.0.0" if self.lan_checkbox.isChecked() else "127.0.0.1"
                port = self.port_input.value()

                self.server_manager.start_server(host, port, normalized_path)

                # Wait for start (max 10 seconds)
                if not self._wait_for_server_start(timeout=10000):
                    raise Exception("Server start failed")

            # Success message
            QMessageBox.information(
                self,
                "Success",
                f"Working directory switched to:\n{normalized_path}" +
                ("\nServer restarted" if is_server_running else "")
            )

        except Exception as e:
            # Rollback
            self.cwd_input.setText(original_cwd)
            self.settings.setValue("cwd", original_cwd)

            QMessageBox.critical(
                self,
                "Error",
                f"Switch failed: {str(e)}\nRolled back to original directory"
            )

            # Try to restore server state if it was running
            if is_server_running:
                try:
                    host = "0.0.0.0" if self.lan_checkbox.isChecked() else "127.0.0.1"
                    port = self.port_input.value()
                    self.server_manager.start_server(host, port, original_cwd)
                except:
                    pass  # Silent fail on rollback recovery, user already knows error

        finally:
            self._is_switching_cwd = False
            self._enable_controls()

    def _disable_controls(self):
        """Disable all control buttons"""
        self.start_btn.setEnabled(False)
        self.cwd_browse_btn.setEnabled(False)
        self.cwd_history_btn.setEnabled(False)
        self.cwd_input.setEnabled(False)
        self.lan_checkbox.setEnabled(False)
        self.port_input.setEnabled(False)

    def _enable_controls(self):
        """Enable buttons based on server state"""
        is_running = (self.start_btn.text() == "Stop Server")

        self.start_btn.setEnabled(True)
        self.cwd_browse_btn.setEnabled(not is_running)
        self.cwd_history_btn.setEnabled(not is_running)
        self.cwd_input.setEnabled(not is_running)
        self.lan_checkbox.setEnabled(not is_running)
        self.port_input.setEnabled(not is_running)

    def _wait_for_server_stop(self, timeout: int) -> bool:
        """
        Wait for server to stop

        Args:
            timeout: Timeout in milliseconds

        Returns:
            True if stopped, False if timeout
        """
        loop = QEventLoop()
        timer = QTimer()
        timer.setSingleShot(True)

        stopped = [False]

        def on_stopped():
            stopped[0] = True
            loop.quit()

        # Connect temporary signals
        self.server_manager.server_stopped.connect(on_stopped)
        timer.timeout.connect(loop.quit)

        timer.start(timeout)
        loop.exec()

        # Disconnect signals to avoid accumulation
        try:
            self.server_manager.server_stopped.disconnect(on_stopped)
        except:
            pass

        return stopped[0]

    def _wait_for_server_start(self, timeout: int) -> bool:
        """
        Wait for server to start

        Args:
            timeout: Timeout in milliseconds

        Returns:
            True if started, False if timeout or error
        """
        loop = QEventLoop()
        timer = QTimer()
        timer.setSingleShot(True)

        result = [False]

        def on_started():
            result[0] = True
            loop.quit()

        def on_error(msg):
            result[0] = False
            loop.quit()

        # Connect temporary signals
        self.server_manager.server_started.connect(on_started)
        self.server_manager.server_error.connect(on_error)
        timer.timeout.connect(loop.quit)

        timer.start(timeout)
        loop.exec()

        # Disconnect signals
        try:
            self.server_manager.server_started.disconnect(on_started)
            self.server_manager.server_error.disconnect(on_error)
        except:
            pass

        return result[0]


    def toggle_server(self):
        if self.start_btn.text() == "Start Server":
            host = "0.0.0.0" if self.lan_checkbox.isChecked() else "127.0.0.1"
            port = self.port_input.value()
            cwd = self.cwd_input.text()

            if not os.path.isdir(cwd):
                QMessageBox.critical(self, "Error", f"Invalid working directory: {cwd}")
                return

            self.save_settings()
            self.start_btn.setEnabled(False) # Disable until started
            self.server_manager.start_server(host, port, cwd)
        else:
            self.start_btn.setEnabled(False) # Disable until stopped
            self.server_manager.stop_server()

    def on_server_started(self):
        self.start_btn.setText("Stop Server")
        self.start_btn.setEnabled(True)
        self.status_label.setText("Status: Running")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        self.cwd_input.setEnabled(False)
        self.cwd_browse_btn.setEnabled(False)
        self.cwd_history_btn.setEnabled(False)
        self.lan_checkbox.setEnabled(False)
        self.port_input.setEnabled(False)

    def on_server_stopped(self):
        self.start_btn.setText("Start Server")
        self.start_btn.setEnabled(True)
        self.status_label.setText("Status: Stopped")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.cwd_input.setEnabled(True)
        self.cwd_browse_btn.setEnabled(True)
        self.cwd_history_btn.setEnabled(True)
        self.lan_checkbox.setEnabled(True)
        self.port_input.setEnabled(True)

    def on_server_error(self, error_msg):
        self.append_log(f"ERROR: {error_msg}")
        self.on_server_stopped()

    def append_log(self, text):
        self.log_area.appendPlainText(text.strip())
        self.log_area.verticalScrollBar().setValue(
            self.log_area.verticalScrollBar().maximum()
        )

    def inject_config(self):
        default_path = self.config_injector.get_default_config_path()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Claude Desktop Config",
            default_path if default_path else os.path.expanduser("~"),
            "JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return

        host = "127.0.0.1"  # Always inject localhost for local Claude config, even if listening on 0.0.0.0?
        # Actually, if we listen on 0.0.0.0, we can still use 127.0.0.1 locally.
        # But if the user wants to inject config to a REMOTE computer's Claude Desktop, they wouldn't use this button here.
        # This button is for "Inject to LOCAL Claude Desktop".
        # So using 127.0.0.1 is safer and always correct for local access.
        # HOWEVER, if they unchecked LAN, it IS 127.0.0.1.
        # If they CHECKED LAN, it is 0.0.0.0, but we should still access via 127.0.0.1 or localhost.

        port = self.port_input.value()
        server_url = f"http://{host}:{port}/sse"

        result = QMessageBox.question(
            self,
            "Confirm Injection",
            f"This will update '{file_path}' to add 'docx-server' pointing to:\n{server_url}\n\nProceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if result == QMessageBox.StandardButton.Yes:
            success = self.config_injector.inject(file_path, server_url)
            if success:
                QMessageBox.information(self, "Success", "Configuration injected successfully.\nPlease restart Claude Desktop.")
            else:
                QMessageBox.critical(self, "Error", "Failed to update configuration file.")

    def show_cwd_history(self):
        """Show history directory selection menu"""
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction

        history = self.cwd_manager.get_history()

        if not history:
            QMessageBox.information(self, "No History", "No recent directories")
            return

        menu = QMenu(self)

        for path in history:
            action = QAction(path, self)
            # Use default argument p=path to capture loop variable
            action.triggered.connect(lambda checked, p=path: self.switch_cwd(p))
            menu.addAction(action)

        # Show below the button
        menu.exec(self.cwd_history_btn.mapToGlobal(
            self.cwd_history_btn.rect().bottomLeft()
        ))

    def closeEvent(self, event):
        # Stop server when closing window
        if self.start_btn.text() == "Stop Server":
            self.server_manager.stop_server()
        super().closeEvent(event)
