import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QSpinBox, QPushButton,
    QGroupBox, QPlainTextEdit, QFileDialog, QMessageBox,
    QCheckBox, QComboBox
)
from PyQt6.QtCore import Qt, QSettings, QEvent
from docx_server_launcher.core.server_manager import ServerManager
from docx_server_launcher.core.config_injector import ConfigInjector
from docx_server_launcher.core.language_manager import LanguageManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Initialize LanguageManager
        self.language_manager = LanguageManager()

        self.resize(600, 500)

        self.server_manager = ServerManager()
        self.config_injector = ConfigInjector()
        self.settings = QSettings("DocxMCP", "Launcher")

        self.is_running = False

        self.init_ui()
        self.connect_signals()
        self.load_settings()

        # Initial translation
        self.retranslateUi()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Configuration Section ---
        self.config_group = QGroupBox()
        config_layout = QVBoxLayout()

        # Working Directory
        cwd_layout = QHBoxLayout()
        self.cwd_label = QLabel()
        cwd_layout.addWidget(self.cwd_label)
        self.cwd_input = QLineEdit()
        self.cwd_input.setPlaceholderText(os.getcwd())
        cwd_layout.addWidget(self.cwd_input)
        self.cwd_browse_btn = QPushButton()
        cwd_layout.addWidget(self.cwd_browse_btn)
        config_layout.addLayout(cwd_layout)

        # Host and Port
        net_layout = QHBoxLayout()

        # Checkbox for LAN access (controls host)
        self.lan_checkbox = QCheckBox()
        self.lan_checkbox.stateChanged.connect(self.on_lan_toggled)
        net_layout.addWidget(self.lan_checkbox)

        net_layout.addStretch()

        # Language Selector
        self.lang_label = QLabel()
        net_layout.addWidget(self.lang_label)
        self.lang_combo = QComboBox()
        self.populate_languages()
        self.lang_combo.currentTextChanged.connect(self.on_language_changed)
        net_layout.addWidget(self.lang_combo)

        net_layout.addSpacing(20)

        self.port_label = QLabel()
        net_layout.addWidget(self.port_label)
        self.port_input = QSpinBox()
        self.port_input.setRange(1024, 65535)
        self.port_input.setValue(8000)
        net_layout.addWidget(self.port_input)
        config_layout.addLayout(net_layout)

        self.config_group.setLayout(config_layout)
        main_layout.addWidget(self.config_group)

        # --- Control Section ---
        self.control_group = QGroupBox()
        control_layout = QHBoxLayout()

        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        control_layout.addWidget(self.status_label)

        control_layout.addStretch()

        self.start_btn = QPushButton()
        control_layout.addWidget(self.start_btn)

        self.control_group.setLayout(control_layout)
        main_layout.addWidget(self.control_group)

        # --- Integration Section ---
        self.integration_group = QGroupBox()
        integration_layout = QHBoxLayout()

        self.inject_btn = QPushButton()
        integration_layout.addWidget(self.inject_btn)

        self.integration_group.setLayout(integration_layout)
        main_layout.addWidget(self.integration_group)

        # --- Logs Section ---
        self.log_group = QGroupBox()
        log_layout = QVBoxLayout()
        self.log_area = QPlainTextEdit()
        self.log_area.setReadOnly(True)
        log_layout.addWidget(self.log_area)
        self.log_group.setLayout(log_layout)
        main_layout.addWidget(self.log_group, stretch=1)

    def retranslateUi(self):
        """Update all UI texts with current translation."""
        self.setWindowTitle(self.tr("Docx MCP Server Launcher"))

        # Config
        self.config_group.setTitle(self.tr("Server Configuration"))
        self.cwd_label.setText(self.tr("Working Directory:"))
        self.cwd_browse_btn.setText(self.tr("Browse..."))
        self.lan_checkbox.setText(self.tr("Allow LAN Access"))
        self.lan_checkbox.setToolTip(self.tr("If checked, the server will listen on 0.0.0.0 (accessible from other devices).\nIf unchecked, it listens on 127.0.0.1 (local only)."))
        self.port_label.setText(self.tr("Port:"))

        # Control
        self.control_group.setTitle(self.tr("Control"))
        if self.is_running:
            self.status_label.setText(self.tr("Status: Running"))
            self.start_btn.setText(self.tr("Stop Server"))
        else:
            self.status_label.setText(self.tr("Status: Stopped"))
            self.start_btn.setText(self.tr("Start Server"))

        # Integration
        self.integration_group.setTitle(self.tr("Claude Desktop Integration"))
        self.inject_btn.setText(self.tr("Inject Config to Claude..."))

        # Logs
        self.log_group.setTitle(self.tr("Logs"))

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
        dir_path = QFileDialog.getExistingDirectory(self, self.tr("Select Working Directory"), self.cwd_input.text())
        if dir_path:
            self.cwd_input.setText(dir_path)

    def toggle_server(self):
        if not self.is_running:
            host = "0.0.0.0" if self.lan_checkbox.isChecked() else "127.0.0.1"
            port = self.port_input.value()
            cwd = self.cwd_input.text()

            if not os.path.isdir(cwd):
                QMessageBox.critical(self, self.tr("Error"), self.tr(f"Invalid working directory: {cwd}"))
                return

            self.save_settings()
            self.start_btn.setEnabled(False) # Disable until started
            self.server_manager.start_server(host, port, cwd)
        else:
            self.start_btn.setEnabled(False) # Disable until stopped
            self.server_manager.stop_server()

    def on_server_started(self):
        self.is_running = True
        self.start_btn.setEnabled(True)
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        self.cwd_input.setEnabled(False)
        self.cwd_browse_btn.setEnabled(False)
        self.lan_checkbox.setEnabled(False)
        self.port_input.setEnabled(False)
        self.retranslateUi()

    def on_server_stopped(self):
        self.is_running = False
        self.start_btn.setEnabled(True)
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.cwd_input.setEnabled(True)
        self.cwd_browse_btn.setEnabled(True)
        self.lan_checkbox.setEnabled(True)
        self.port_input.setEnabled(True)
        self.retranslateUi()

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
            self.tr("Select Claude Desktop Config"),
            default_path if default_path else os.path.expanduser("~"),
            "JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return

        host = "127.0.0.1"
        port = self.port_input.value()
        server_url = f"http://{host}:{port}/sse"

        result = QMessageBox.question(
            self,
            self.tr("Confirm Injection"),
            self.tr(f"This will update '{file_path}' to add 'docx-server' pointing to:\n{server_url}\n\nProceed?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if result == QMessageBox.StandardButton.Yes:
            success = self.config_injector.inject(file_path, server_url)
            if success:
                QMessageBox.information(self, self.tr("Success"), self.tr("Configuration injected successfully.\nPlease restart Claude Desktop."))
            else:
                QMessageBox.critical(self, self.tr("Error"), self.tr("Failed to update configuration file."))

    def closeEvent(self, event):
        # Stop server when closing window
        if self.is_running:
            self.server_manager.stop_server()
        super().closeEvent(event)
