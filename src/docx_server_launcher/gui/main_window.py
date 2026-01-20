import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QSpinBox, QPushButton,
    QGroupBox, QPlainTextEdit, QFileDialog, QMessageBox,
    QCheckBox
)
from PyQt6.QtCore import Qt, QSettings
from docx_server_launcher.core.server_manager import ServerManager
from docx_server_launcher.core.config_injector import ConfigInjector

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Docx MCP Server Launcher")
        self.resize(600, 500)

        self.server_manager = ServerManager()
        self.config_injector = ConfigInjector()
        self.settings = QSettings("DocxMCP", "Launcher")

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
        dir_path = QFileDialog.getExistingDirectory(self, "Select Working Directory", self.cwd_input.text())
        if dir_path:
            self.cwd_input.setText(dir_path)

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
        self.lan_checkbox.setEnabled(False)
        self.port_input.setEnabled(False)

    def on_server_stopped(self):
        self.start_btn.setText("Start Server")
        self.start_btn.setEnabled(True)
        self.status_label.setText("Status: Stopped")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.cwd_input.setEnabled(True)
        self.cwd_browse_btn.setEnabled(True)
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

    def closeEvent(self, event):
        # Stop server when closing window
        if self.start_btn.text() == "Stop Server":
            self.server_manager.stop_server()
        super().closeEvent(event)
