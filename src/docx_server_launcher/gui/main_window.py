import os
import re
from pathlib import Path
from typing import List, Tuple
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QSpinBox, QPushButton,
    QGroupBox, QPlainTextEdit, QFileDialog, QMessageBox,
    QCheckBox, QComboBox, QTextEdit
)
from PyQt6.QtCore import Qt, QSettings, QEventLoop, QTimer, QEvent
from PyQt6.QtGui import QShortcut, QKeySequence, QTextCharFormat, QColor, QTextCursor
from docx_server_launcher.core.server_manager import ServerManager
from docx_server_launcher.core.cli_launcher import CLILauncher
from docx_server_launcher.core.working_directory_manager import WorkingDirectoryManager
from docx_server_launcher.core.language_manager import LanguageManager
from docx_server_launcher.core.config_manager import ConfigManager
from docx_server_launcher.core.http_client import HTTPClient, ServerConnectionError, ServerTimeoutError

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Initialize LanguageManager
        self.language_manager = LanguageManager()

        self.resize(600, 500)

        self.server_manager = ServerManager()
        self.cli_launcher = CLILauncher()
        self.settings = QSettings("DocxMCP", "Launcher")
        self.config_manager = ConfigManager("docx-mcp-server", "launcher")

        self.cwd_manager = WorkingDirectoryManager(self.settings)
        self._is_switching_cwd = False
        self.is_running = False

        # HTTP Client for server communication (T-008, T-009, T-010)
        self.http_client: HTTPClient = None
        self._status_poll_timer: QTimer = None
        self._current_file_path: str = None  # Track current active file

        # Search state (T-001, T-004, T-005)
        self._search_matches: List[Tuple[int, int]] = []  # [(start, length), ...]
        self._current_match_index: int = -1
        self._search_timer: QTimer = None

        # Command update timer (debounce)
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._do_update_command_display)

        self.init_ui()
        self.connect_signals()
        self.load_settings()

        # Initial translation
        self.retranslateUi()

        # Initialize command display
        self.update_command_display()

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

        self.cwd_history_btn = QPushButton("Recent ▼")
        self.cwd_history_btn.setMaximumWidth(100)
        cwd_layout.addWidget(self.cwd_history_btn)

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

        net_layout.addSpacing(20)

        self.log_level_label = QLabel()
        net_layout.addWidget(self.log_level_label)
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        net_layout.addWidget(self.log_level_combo)
        config_layout.addLayout(net_layout)

        self.config_group.setLayout(config_layout)
        main_layout.addWidget(self.config_group)

        # --- Preview Settings Section ---
        self.preview_group = QGroupBox()
        preview_layout = QVBoxLayout()

        # Row 1: WPS Path + Priority (horizontal)
        wps_priority_layout = QHBoxLayout()

        # WPS Path
        self.wps_label = QLabel()
        wps_priority_layout.addWidget(self.wps_label)
        self.wps_input = QLineEdit()
        self.wps_input.setPlaceholderText(self.tr("Auto-detect"))
        wps_priority_layout.addWidget(self.wps_input, stretch=1)
        self.wps_browse_btn = QPushButton()
        wps_priority_layout.addWidget(self.wps_browse_btn)

        wps_priority_layout.addSpacing(20)

        # Priority
        self.priority_label = QLabel()
        wps_priority_layout.addWidget(self.priority_label)
        self.priority_combo = QComboBox()
        # Data: "auto", "wps", "word"
        self.priority_combo.addItem("Auto", "auto")
        self.priority_combo.addItem("Prefer WPS", "wps")
        self.priority_combo.addItem("Prefer Word", "word")
        wps_priority_layout.addWidget(self.priority_combo)

        preview_layout.addLayout(wps_priority_layout)

        # Row 2: Word Path (horizontal)
        word_layout = QHBoxLayout()
        self.word_label = QLabel()
        word_layout.addWidget(self.word_label)
        self.word_input = QLineEdit()
        self.word_input.setPlaceholderText(self.tr("Auto-detect"))
        word_layout.addWidget(self.word_input)
        self.word_browse_btn = QPushButton()
        word_layout.addWidget(self.word_browse_btn)
        preview_layout.addLayout(word_layout)

        self.preview_group.setLayout(preview_layout)
        main_layout.addWidget(self.preview_group)

        # --- Control Section ---
        self.control_group = QGroupBox()
        control_layout = QVBoxLayout()

        # Status row
        status_row = QHBoxLayout()
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        status_row.addWidget(self.status_label)

        status_row.addStretch()

        self.start_btn = QPushButton()
        status_row.addWidget(self.start_btn)

        control_layout.addLayout(status_row)

        # T-008: File selection row (only visible when server is running)
        self.file_selection_group = QWidget()
        file_row = QHBoxLayout()
        file_row.setContentsMargins(0, 0, 0, 0)

        self.file_label = QLabel()
        file_row.addWidget(self.file_label)

        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("No file selected")
        self.file_input.setReadOnly(True)
        self.file_input.setStyleSheet("background-color: #f5f5f5;")
        file_row.addWidget(self.file_input)

        self.file_browse_btn = QPushButton()
        file_row.addWidget(self.file_browse_btn)

        self.file_selection_group.setLayout(file_row)
        self.file_selection_group.setVisible(False)  # Hidden by default
        control_layout.addWidget(self.file_selection_group)

        # T-009: Status bar (only visible when server is running)
        self.status_bar_group = QWidget()
        status_bar_row = QHBoxLayout()
        status_bar_row.setContentsMargins(0, 0, 0, 0)

        self.status_bar_label = QLabel()
        self.status_bar_label.setStyleSheet("color: #666; font-size: 11px;")
        self.status_bar_label.setText("Server: Not Connected")
        status_bar_row.addWidget(self.status_bar_label)

        status_bar_row.addStretch()

        self.status_bar_group.setLayout(status_bar_row)
        self.status_bar_group.setVisible(False)  # Hidden by default
        control_layout.addWidget(self.status_bar_group)

        self.control_group.setLayout(control_layout)
        main_layout.addWidget(self.control_group)

        # --- Integration Section ---
        self.integration_group = QGroupBox()
        integration_layout = QVBoxLayout()

        # Command Display Row
        command_layout = QHBoxLayout()
        self.command_display = QLineEdit()
        self.command_display.setReadOnly(True)
        self.command_display.setPlaceholderText("Command will appear here...")
        self.command_display.setStyleSheet("background-color: #f5f5f5;")
        command_layout.addWidget(self.command_display)

        self.copy_btn = QPushButton("Copy Command")
        self.copy_btn.setMaximumWidth(120)
        command_layout.addWidget(self.copy_btn)

        integration_layout.addLayout(command_layout)

        # Hint label
        hint_label = QLabel()
        hint_label.setObjectName("cli_params_hint")
        integration_layout.addWidget(hint_label)

        # CLI params input (for additional parameters)
        self.cli_params_input = QLineEdit()
        self.cli_params_input.setPlaceholderText("e.g., --dangerously-skip-permission")
        integration_layout.addWidget(self.cli_params_input)

        self.integration_group.setLayout(integration_layout)
        main_layout.addWidget(self.integration_group)

        # --- Logs Section ---
        self.log_group = QGroupBox()
        log_layout = QVBoxLayout()

        # T-001: Search Toolbar (Row 1 & 2)
        # Row 1: Search input + Navigation + Match count
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel(self.tr("Search:")))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.tr("Enter search text..."))
        self.search_input.setClearButtonEnabled(True)
        search_row.addWidget(self.search_input, stretch=1)

        self.prev_btn = QPushButton("↑")
        self.prev_btn.setToolTip(self.tr("Previous match (Shift+F3)"))
        self.prev_btn.setMaximumWidth(40)
        search_row.addWidget(self.prev_btn)

        self.next_btn = QPushButton("↓")
        self.next_btn.setToolTip(self.tr("Next match (F3)"))
        self.next_btn.setMaximumWidth(40)
        search_row.addWidget(self.next_btn)

        self.match_label = QLabel("0 / 0")
        self.match_label.setMinimumWidth(60)
        self.match_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        search_row.addWidget(self.match_label)

        log_layout.addLayout(search_row)

        # Row 2: Options + Clear button
        options_row = QHBoxLayout()

        self.case_checkbox = QCheckBox(self.tr("Case Sensitive"))
        options_row.addWidget(self.case_checkbox)

        self.regex_checkbox = QCheckBox(self.tr("Regex"))
        options_row.addWidget(self.regex_checkbox)

        options_row.addStretch()

        self.clear_log_btn = QPushButton(self.tr("Clear Logs"))
        options_row.addWidget(self.clear_log_btn)

        log_layout.addLayout(options_row)

        # Log area
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
        self.log_level_label.setText(self.tr("Log Level:"))

        # Preview Settings
        self.preview_group.setTitle(self.tr("Preview Settings"))
        self.wps_label.setText(self.tr("WPS Path:"))
        self.wps_browse_btn.setText(self.tr("Browse..."))
        self.word_label.setText(self.tr("Word Path:"))
        self.word_browse_btn.setText(self.tr("Browse..."))
        self.priority_label.setText(self.tr("Priority:"))

        # Update combo items text while keeping user data
        self.priority_combo.setItemText(0, self.tr("Auto"))
        self.priority_combo.setItemText(1, self.tr("Prefer WPS"))
        self.priority_combo.setItemText(2, self.tr("Prefer Word"))

        # Control
        self.control_group.setTitle(self.tr("Control"))
        if self.is_running:
            self.status_label.setText(self.tr("Status: Running"))
            self.start_btn.setText(self.tr("Stop Server"))
        else:
            self.status_label.setText(self.tr("Status: Stopped"))
            self.start_btn.setText(self.tr("Start Server"))

        # File selection (T-008)
        self.file_label.setText(self.tr("Active File:"))
        self.file_browse_btn.setText(self.tr("Select File..."))

        # Integration
        self.integration_group.setTitle(self.tr("Claude Integration"))
        self.command_display.setPlaceholderText(self.tr("Command will appear here..."))
        self.copy_btn.setText(self.tr("Copy Command"))

        hint_label = self.integration_group.findChild(QLabel, "cli_params_hint")
        if hint_label:
            hint_label.setText(self.tr("Add custom parameters below (e.g., --dangerously-skip-permission)"))
        self.cli_params_input.setPlaceholderText(
            self.tr("e.g., --dangerously-skip-permission")
        )

        # Logs
        self.log_group.setTitle(self.tr("Logs"))

    def connect_signals(self):
        # UI signals
        self.cwd_browse_btn.clicked.connect(self.browse_cwd)
        self.cwd_history_btn.clicked.connect(self.show_cwd_history)

        # Preview signals
        self.wps_browse_btn.clicked.connect(lambda: self.browse_exe(self.wps_input))
        self.word_browse_btn.clicked.connect(lambda: self.browse_exe(self.word_input))

        self.start_btn.clicked.connect(self.toggle_server)

        # T-008: File selection signal
        self.file_browse_btn.clicked.connect(self.browse_docx_file)

        # New signals
        self.copy_btn.clicked.connect(self.copy_command)
        self.port_input.valueChanged.connect(self.update_command_display)
        self.lan_checkbox.stateChanged.connect(self.update_command_display)
        self.cli_params_input.textChanged.connect(self.update_command_display)

        # ServerManager signals
        self.server_manager.server_started.connect(self.on_server_started)
        self.server_manager.server_stopped.connect(self.on_server_stopped)
        self.server_manager.log_received.connect(self.append_log)
        self.server_manager.server_error.connect(self.on_server_error)

        # T-005: Search signals (debounced)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.case_checkbox.stateChanged.connect(self.on_search_option_changed)
        self.regex_checkbox.stateChanged.connect(self.on_search_option_changed)

        # T-006: Navigation signals
        self.prev_btn.clicked.connect(lambda: self.navigate_to_match(-1))
        self.next_btn.clicked.connect(lambda: self.navigate_to_match(1))

        # T-007: Clear logs signal
        self.clear_log_btn.clicked.connect(self.clear_log_area)

        # T-008: Keyboard shortcuts
        self.setup_shortcuts()

    def load_settings(self):
        last_cwd = self.settings.value("cwd", os.getcwd())
        if last_cwd:
            self.cwd_input.setText(str(last_cwd))

        last_host = str(self.settings.value("host", "127.0.0.1"))
        self.lan_checkbox.setChecked(last_host == "0.0.0.0")

        last_port = self.settings.value("port", 8000)
        self.port_input.setValue(int(last_port))

        last_log_level = str(self.settings.value("log_level", "INFO")).upper()
        index = self.log_level_combo.findText(last_log_level)
        if index >= 0:
            self.log_level_combo.setCurrentIndex(index)
        else:
            self.log_level_combo.setCurrentText("INFO")

        # Load preview settings
        self.wps_input.setText(self.settings.value("preview/wps_path", ""))
        self.word_input.setText(self.settings.value("preview/word_path", ""))

        priority = self.settings.value("preview/priority", "auto")
        index = self.priority_combo.findData(priority)
        if index >= 0:
            self.priority_combo.setCurrentIndex(index)

        # Load CLI params
        self.cli_params_input.setText(self.settings.value("cli/extra_params", ""))

        # T-009: Load search settings
        self.load_search_settings()

    def save_settings(self):
        self.settings.setValue("cwd", self.cwd_input.text())
        host = "0.0.0.0" if self.lan_checkbox.isChecked() else "127.0.0.1"
        self.settings.setValue("host", host)
        self.settings.setValue("port", self.port_input.value())
        self.settings.setValue("log_level", self.log_level_combo.currentText())

        # Save preview settings
        self.settings.setValue("preview/wps_path", self.wps_input.text())
        self.settings.setValue("preview/word_path", self.word_input.text())
        self.settings.setValue("preview/priority", self.priority_combo.currentData())

        # Save CLI params
        self.settings.setValue("cli/extra_params", self.cli_params_input.text())

        # T-009: Save search settings
        self.save_search_settings()

    def update_command_display(self) -> None:
        """Debounced command display update."""
        self._update_timer.stop()
        self._update_timer.start(300)

    def _do_update_command_display(self) -> None:
        """Actually update the command display."""
        try:
            # 1. Get config
            if self.lan_checkbox.isChecked():
                host = self.cli_launcher.get_lan_ip()
            else:
                host = "127.0.0.1"

            port = self.port_input.value()
            extra_params = self.cli_params_input.text().strip()

            # 2. Build server URL
            server_url = f"http://{host}:{port}/sse"

            # 3. Build command (new signature: server_url, transport, extra_params)
            cmd_list = self.cli_launcher.build_command(server_url, "sse", extra_params)

            # 4. Format as string
            import platform
            # On Windows, build_command already adds cmd.exe /c, but let's double check join behavior
            # The list comes as ['cmd.exe', '/c', 'claude', ...] or ['claude', ...]
            # We just join them with spaces.
            # NOTE: shlex.join is better but might not be available on old python,
            # but we can assume basic space join is okay for display purposes unless params have spaces.
            # build_command handles params parsing.

            # Simple join for display
            cmd_str = ' '.join(cmd_list)

            self.command_display.setText(cmd_str)
            self.command_display.setCursorPosition(0)

        except Exception as e:
            self.command_display.setText(f"Error: {str(e)}")

    def copy_command(self) -> None:
        """Copy command to clipboard with feedback."""
        try:
            cmd = self.command_display.text()

            if not cmd or cmd.startswith("Error:"):
                QMessageBox.warning(
                    self,
                    self.tr("Copy Failed"),
                    self.tr("No valid command to copy.")
                )
                return

            # Copy to clipboard
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(cmd)

            # Visual feedback
            original_text = self.copy_btn.text()
            self.copy_btn.setText(self.tr("Copied!"))
            self.copy_btn.setEnabled(False)

            # Reset after 2s
            QTimer.singleShot(2000, lambda: self._reset_copy_button(original_text))

        except Exception as e:
            QMessageBox.critical(
                self,
                self.tr("Copy Error"),
                self.tr(f"Failed to copy command: {str(e)}")
            )

    def _reset_copy_button(self, original_text: str) -> None:
        """Reset copy button state."""
        # We need to make sure we use the translated text for "Copy Command" if original was overwritten
        self.copy_btn.setText(self.tr("Copy Command"))
        self.copy_btn.setEnabled(True)

    def on_lan_toggled(self, state):
        # We don't need to do much immediately, value is read on save/start
        pass

    def populate_languages(self):
        """Populate the language combo box with available languages."""
        available_languages = self.language_manager.get_available_languages()

        # Clear existing items
        self.lang_combo.clear()

        # Add languages (display name as shown, locale code as data)
        for locale_code, display_name in available_languages.items():
            self.lang_combo.addItem(display_name, locale_code)

        # Set current selection based on saved preference
        current_locale = self.language_manager.current_locale
        index = self.lang_combo.findData(current_locale)
        if index >= 0:
            self.lang_combo.setCurrentIndex(index)

    def on_language_changed(self, display_name: str):
        """Handle language selection change."""
        # Get the locale code from the combo box's current item
        locale_code = self.lang_combo.currentData()
        if locale_code and locale_code != self.language_manager.current_locale:
            self.language_manager.load_language(locale_code)

    def browse_cwd(self):
        """Open directory selection dialog"""
        current_dir = self.cwd_input.text() or os.getcwd()
        dir_path = QFileDialog.getExistingDirectory(
            self,
            self.tr("Select Working Directory"),
            current_dir
        )

        if dir_path:
            # Call new method to handle switching
            self.switch_cwd(dir_path)

    def browse_exe(self, target_input: QLineEdit):
        """Open file selection dialog for executables"""
        current_path = target_input.text()
        start_dir = os.path.dirname(current_path) if current_path and os.path.exists(current_path) else ""

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Select Executable"),
            start_dir,
            "Executables (*.exe);;All Files (*)"
        )

        if file_path:
            target_input.setText(file_path)

    def browse_docx_file(self):
        """T-008: Open file selection dialog for .docx files"""
        # Check if server is running
        if not self.is_running:
            QMessageBox.warning(
                self,
                self.tr("Server Not Running"),
                self.tr("Please start the server before selecting a file.")
            )
            return

        # Check if HTTP client is available
        if not self.http_client:
            QMessageBox.critical(
                self,
                self.tr("Connection Error"),
                self.tr("HTTP client not initialized. Please restart the server.")
            )
            return

        # Get current working directory
        cwd = self.cwd_input.text() or os.getcwd()

        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Select Document"),
            cwd,
            "Word Documents (*.docx);;All Files (*)"
        )

        if file_path:
            self.switch_active_file(file_path)

    def switch_active_file(self, file_path: str, force: bool = False):
        """T-008: Switch to a new active file via HTTP API.

        Args:
            file_path: Path to the .docx file
            force: If True, discard unsaved changes
        """
        if not self.http_client:
            QMessageBox.critical(
                self,
                self.tr("Connection Error"),
                self.tr("HTTP client not initialized.")
            )
            return

        try:
            # Call HTTP API
            response = self.http_client.switch_file(file_path, force=force)

            # Update UI
            self._current_file_path = response.get("currentFile")
            self.file_input.setText(self._current_file_path or "")

            # Log success
            self.append_log(f"✅ Switched to file: {self._current_file_path}")

            # Show success message
            QMessageBox.information(
                self,
                self.tr("Success"),
                self.tr(f"File switched to:\n{self._current_file_path}")
            )

        except ServerConnectionError as e:
            QMessageBox.critical(
                self,
                self.tr("Connection Error"),
                self.tr(f"Failed to connect to server:\n{str(e)}")
            )
            self.append_log(f"❌ Connection error: {e}")

        except ServerTimeoutError as e:
            QMessageBox.critical(
                self,
                self.tr("Timeout Error"),
                self.tr(f"Request timed out:\n{str(e)}")
            )
            self.append_log(f"❌ Timeout error: {e}")

        except Exception as e:
            # Check for specific HTTP errors
            import requests
            if isinstance(e, requests.HTTPError):
                status_code = e.response.status_code
                error_detail = e.response.json().get("detail", str(e)) if e.response else str(e)

                if status_code == 404:
                    QMessageBox.critical(
                        self,
                        self.tr("File Not Found"),
                        self.tr(f"The file does not exist:\n{file_path}")
                    )
                    self.append_log(f"❌ File not found: {file_path}")

                elif status_code == 403:
                    QMessageBox.critical(
                        self,
                        self.tr("Permission Denied"),
                        self.tr(f"Cannot access file (permission denied):\n{file_path}")
                    )
                    self.append_log(f"❌ Permission denied: {file_path}")

                elif status_code == 423:
                    QMessageBox.critical(
                        self,
                        self.tr("File Locked"),
                        self.tr(f"The file is locked by another process:\n{file_path}")
                    )
                    self.append_log(f"❌ File locked: {file_path}")

                elif status_code == 409:
                    # Unsaved changes - show dialog
                    self.show_unsaved_changes_dialog(file_path)

                else:
                    QMessageBox.critical(
                        self,
                        self.tr("Server Error"),
                        self.tr(f"Server returned error:\n{error_detail}")
                    )
                    self.append_log(f"❌ Server error: {error_detail}")
            else:
                QMessageBox.critical(
                    self,
                    self.tr("Error"),
                    self.tr(f"Failed to switch file:\n{str(e)}")
                )
                self.append_log(f"❌ Error switching file: {e}")

    def show_unsaved_changes_dialog(self, new_file_path: str):
        """T-008: Show dialog when switching with unsaved changes.

        Args:
            new_file_path: Path to the new file user wants to switch to
        """
        reply = QMessageBox.question(
            self,
            self.tr("Unsaved Changes"),
            self.tr(f"The current file has unsaved changes.\n\n"
                   f"Do you want to save and switch to:\n{new_file_path}?"),
            QMessageBox.StandardButton.Save |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save
        )

        if reply == QMessageBox.StandardButton.Save:
            # Save and switch
            try:
                # Close session with save
                self.http_client.close_session(save=True)
                self.append_log("💾 Saved current file")

                # Switch to new file
                self.switch_active_file(new_file_path, force=False)

            except Exception as e:
                QMessageBox.critical(
                    self,
                    self.tr("Save Error"),
                    self.tr(f"Failed to save current file:\n{str(e)}")
                )
                self.append_log(f"❌ Save error: {e}")

        elif reply == QMessageBox.StandardButton.Discard:
            # Discard and switch (force=True)
            self.switch_active_file(new_file_path, force=True)
            self.append_log("⚠️ Discarded unsaved changes")

        # else: Cancel - do nothing

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
                log_level = self.log_level_combo.currentText() or "INFO"

                self.server_manager.start_server(host, port, normalized_path, log_level=log_level)

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
                    log_level = self.log_level_combo.currentText() or "INFO"
                    self.server_manager.start_server(host, port, original_cwd, log_level=log_level)
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
        if not self.is_running:
            host = "0.0.0.0" if self.lan_checkbox.isChecked() else "127.0.0.1"
            port = self.port_input.value()
            cwd = self.cwd_input.text()

            if not os.path.isdir(cwd):
                QMessageBox.critical(self, self.tr("Error"), self.tr(f"Invalid working directory: {cwd}"))
                return

            self.save_settings()
            self.start_btn.setEnabled(False) # Disable until started
            log_level = self.log_level_combo.currentText() or "INFO"

            # Prepare env vars for preview config
            env_vars = {}
            wps_path = self.wps_input.text().strip()
            word_path = self.word_input.text().strip()
            priority = self.priority_combo.currentData()

            if wps_path:
                env_vars["DOCX_PREVIEW_WPS_PATH"] = wps_path
            if word_path:
                env_vars["DOCX_PREVIEW_WORD_PATH"] = word_path
            if priority:
                env_vars["DOCX_PREVIEW_PRIORITY"] = priority

            self.server_manager.start_server(host, port, cwd, log_level=log_level, extra_env=env_vars)
        else:
            self.start_btn.setEnabled(False) # Disable until stopped
            self.server_manager.stop_server()

    def on_server_started(self):
        self.is_running = True
        self.start_btn.setEnabled(True)
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        self.cwd_input.setEnabled(False)
        self.cwd_browse_btn.setEnabled(False)
        self.cwd_history_btn.setEnabled(False)
        self.lan_checkbox.setEnabled(False)
        self.port_input.setEnabled(False)
        self.retranslateUi()

        # T-009, T-010: Initialize HTTP client and status polling
        # Note: Server process has started, but HTTP server may take 2-3 seconds to be ready
        # Use a delayed timer with retries for health check
        port = self.port_input.value()
        base_url = f"http://127.0.0.1:{port}"

        # Use shorter timeout for health checks (faster retries)
        self.http_client = HTTPClient(base_url=base_url, timeout=2.0)

        # Delayed health check with retries
        self._health_check_retries = 0
        self._health_check_max_retries = 15  # Max 15 retries (7.5 seconds total)

        # Use longer initial delay (3 seconds) to allow Uvicorn to start
        self.append_log(f"⏳ Waiting for HTTP server to start...")
        QTimer.singleShot(3000, self._try_health_check)

    def _try_health_check(self):
        """T-010: Try to perform health check with retries."""
        try:
            health = self.http_client.health_check()
            self.append_log(f"✅ Server health check passed: {health.get('status', 'unknown')}")

            # Show file selection UI
            self.file_selection_group.setVisible(True)
            self.status_bar_group.setVisible(True)

            # T-009: Start status polling (every 2 seconds)
            self._status_poll_timer = QTimer()
            self._status_poll_timer.timeout.connect(self.update_server_status)
            self._status_poll_timer.start(2000)  # 2 seconds interval

            # Initial status update
            self.update_server_status()

        except Exception as e:
            self._health_check_retries += 1

            if self._health_check_retries < self._health_check_max_retries:
                # Retry after 0.5 seconds (faster retries with shorter timeout)
                if self._health_check_retries <= 3:
                    self.append_log(f"⏳ Waiting for server to be ready... (attempt {self._health_check_retries}/{self._health_check_max_retries})")
                QTimer.singleShot(500, self._try_health_check)
            else:
                # Max retries reached
                self.append_log(f"⚠️ Warning: Could not connect to HTTP API after {self._health_check_max_retries} attempts")
                self.append_log(f"   MCP tools are still available, but file selection is disabled")
                self.file_selection_group.setVisible(False)
                self.status_bar_group.setVisible(False)

    def on_server_stopped(self):
        self.is_running = False
        self.start_btn.setEnabled(True)
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.cwd_input.setEnabled(True)
        self.cwd_browse_btn.setEnabled(True)
        self.cwd_history_btn.setEnabled(True)
        self.lan_checkbox.setEnabled(True)
        self.port_input.setEnabled(True)
        self.retranslateUi()

        # T-009: Stop status polling
        if self._status_poll_timer:
            self._status_poll_timer.stop()
            self._status_poll_timer = None

        # Clean up HTTP client
        self.http_client = None
        self._current_file_path = None

        # Hide file selection UI
        self.file_selection_group.setVisible(False)
        self.status_bar_group.setVisible(False)

        # Clear file input
        self.file_input.setText("")

    def on_server_error(self, error_msg):
        self.append_log(f"ERROR: {error_msg}")
        self.on_server_stopped()

    def update_server_status(self):
        """T-009: Update server status from HTTP API (called every 2 seconds)"""
        if not self.http_client or not self.is_running:
            return

        try:
            # Call /api/status
            status = self.http_client.get_status()

            # Extract information
            current_file = status.get("currentFile")
            session_id = status.get("sessionId")
            has_unsaved = status.get("hasUnsaved", False)

            # Update UI
            if current_file:
                self._current_file_path = current_file
                self.file_input.setText(current_file)
            else:
                self._current_file_path = None
                self.file_input.setText("No file selected")

            # Update status bar
            status_parts = []

            # File status
            if current_file:
                file_name = os.path.basename(current_file)
                status_parts.append(f"📄 {file_name}")
            else:
                status_parts.append("📄 No file")

            # Session status
            if session_id:
                status_parts.append(f"🔗 Session: {session_id[:8]}...")
            else:
                status_parts.append("🔗 No session")

            # Unsaved changes
            if has_unsaved:
                status_parts.append("⚠️ Unsaved")
            else:
                status_parts.append("✅ Saved")

            self.status_bar_label.setText(" | ".join(status_parts))

        except ServerConnectionError:
            self.status_bar_label.setText("❌ Server: Connection Lost")
            # Don't log every poll failure to avoid spam

        except ServerTimeoutError:
            self.status_bar_label.setText("❌ Server: Timeout")
            # Don't log every poll failure to avoid spam

        except Exception as e:
            # Log unexpected errors but don't spam
            if not hasattr(self, '_last_status_error') or self._last_status_error != str(e):
                self.append_log(f"⚠️ Status poll error: {e}")
                self._last_status_error = str(e)
            self.status_bar_label.setText("❌ Server: Error")

    def append_log(self, text):
        self.log_area.appendPlainText(text.strip())
        self.log_area.verticalScrollBar().setValue(
            self.log_area.verticalScrollBar().maximum()
        )

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
        if self.is_running:
            self.server_manager.stop_server()
        super().closeEvent(event)

    # ==================== Log Search Feature ====================
    # T-002: Plain text search engine
    def find_matches_plain(self, text: str, pattern: str, case_sensitive: bool) -> List[Tuple[int, int]]:
        """
        Find all plain text matches.

        Args:
            text: Text to search in
            pattern: Search pattern
            case_sensitive: Case sensitive matching

        Returns:
            List of (start_pos, length) tuples
        """
        if not pattern:
            return []

        matches = []
        search_text = text if case_sensitive else text.lower()
        search_pattern = pattern if case_sensitive else pattern.lower()

        start = 0
        while True:
            pos = search_text.find(search_pattern, start)
            if pos == -1:
                break
            matches.append((pos, len(pattern)))
            start = pos + 1  # Allow overlapping matches

        return matches

    # T-003: Regex search engine
    def find_matches_regex(self, text: str, pattern: str, case_sensitive: bool) -> List[Tuple[int, int]]:
        """
        Find all regex matches.

        Args:
            text: Text to search in
            pattern: Regex pattern
            case_sensitive: Case sensitive matching

        Returns:
            List of (start_pos, length) tuples

        Raises:
            ValueError: If regex is invalid
        """
        try:
            flags = 0 if case_sensitive else re.IGNORECASE
            regex = re.compile(pattern, flags)
        except re.error as e:
            raise ValueError(f"Invalid regex: {e}")

        matches = []
        for match in regex.finditer(text):
            matches.append((match.start(), match.end() - match.start()))

        return matches

    def validate_regex_safety(self, pattern: str) -> Tuple[bool, str]:
        """
        Validate regex safety to prevent ReDoS attacks.

        Args:
            pattern: Regex pattern to validate

        Returns:
            Tuple of (is_safe, error_message)
        """
        # Detect dangerous nested quantifiers
        dangerous_patterns = [
            r'\([^)]*[+*]\)[+*]',  # (x+)+ or (x*)*
            r'\([^)]*[+*]\)\{',    # (x+){n,m}
        ]

        for dp in dangerous_patterns:
            if re.search(dp, pattern):
                return False, "Potentially dangerous regex (nested quantifiers)"

        return True, ""

    # T-004: Highlight manager
    def apply_highlights(self):
        """Apply search highlights to log area."""
        extra_selections = []

        # Get document length to validate positions
        doc_length = len(self.log_area.toPlainText())

        for i, (start, length) in enumerate(self._search_matches):
            # Skip invalid positions
            if start >= doc_length or start + length > doc_length:
                continue

            selection = QTextEdit.ExtraSelection()

            # Set cursor position
            cursor = self.log_area.textCursor()
            cursor.setPosition(start)
            cursor.setPosition(start + length, QTextCursor.MoveMode.KeepAnchor)
            selection.cursor = cursor

            # Set background color
            format = QTextCharFormat()
            if i == self._current_match_index:
                format.setBackground(QColor("#FFA500"))  # Orange (current match)
            else:
                format.setBackground(QColor("#FFFF00"))  # Yellow (normal match)
            selection.format = format

            extra_selections.append(selection)

        self.log_area.setExtraSelections(extra_selections)

    def clear_highlights(self):
        """Clear all search highlights."""
        self.log_area.setExtraSelections([])
        self._search_matches = []
        self._current_match_index = -1

    # T-005: Debounced search
    def on_search_text_changed(self, text: str):
        """Handle search text change with debouncing (300ms)."""
        if self._search_timer:
            self._search_timer.stop()

        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self.perform_search)
        self._search_timer.start(300)  # 300ms delay

    def on_search_option_changed(self):
        """Handle search option change (immediate search)."""
        self.perform_search()

    def perform_search(self):
        """Execute search and apply highlights."""
        pattern = self.search_input.text()

        if not pattern:
            self.clear_highlights()
            self.match_label.setText("0 / 0")
            return

        try:
            # Validate regex if enabled
            if self.regex_checkbox.isChecked():
                is_safe, msg = self.validate_regex_safety(pattern)
                if not is_safe:
                    self.show_search_error(msg)
                    return

            # Execute search
            text = self.log_area.toPlainText()
            use_regex = self.regex_checkbox.isChecked()
            case_sensitive = self.case_checkbox.isChecked()

            if use_regex:
                matches = self.find_matches_regex(text, pattern, case_sensitive)
            else:
                matches = self.find_matches_plain(text, pattern, case_sensitive)

            # Limit matches to prevent performance issues
            if len(matches) > 1000:
                matches = matches[:1000]

            # Update state
            self._search_matches = matches
            self._current_match_index = 0 if matches else -1

            # Apply highlights
            self.apply_highlights()
            self.update_match_label()

            # Clear error state
            self.search_input.setStyleSheet("")
            self.search_input.setToolTip("")

        except ValueError as e:
            self.show_search_error(str(e))
        except Exception as e:
            self.show_search_error(f"Search error: {e}")

    def show_search_error(self, message: str):
        """Display search error in UI."""
        self.search_input.setStyleSheet("border: 1px solid red;")
        self.search_input.setToolTip(message)
        self.match_label.setText("Error")
        self.clear_highlights()

    def show_error_dialog(self, title: str, message: str):
        """
        Show error dialog with copy button.

        Args:
            title: Dialog title
            message: Error message to display
        """
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Critical)
        dialog.setWindowTitle(title)
        dialog.setText(message)

        # Add copy button
        copy_button = dialog.addButton(self.tr("Copy"), QMessageBox.ButtonRole.ActionRole)
        dialog.addButton(QMessageBox.StandardButton.Ok)

        # Show dialog
        dialog.exec()

        # Check if copy button was clicked
        if dialog.clickedButton() == copy_button:
            self.copy_to_clipboard(message)

    def copy_to_clipboard(self, text: str):
        """
        Copy text to clipboard with size limit.

        Args:
            text: Text to copy (max 10KB)
        """
        from PyQt6.QtWidgets import QApplication

        # Limit to 10KB
        max_size = 10 * 1024
        if len(text) > max_size:
            text = text[:max_size] + "\n... (truncated)"

        clipboard = QApplication.clipboard()
        clipboard.setText(text)

        # Show confirmation
        QMessageBox.information(
            self,
            self.tr("Copied"),
            self.tr("Error message copied to clipboard")
        )

    # T-006: Result navigation
    def navigate_to_match(self, direction: int):
        """
        Navigate to previous/next match.

        Args:
            direction: -1 for previous, 1 for next
        """
        if not self._search_matches:
            return

        # Update index with wrapping
        self._current_match_index += direction
        if self._current_match_index >= len(self._search_matches):
            self._current_match_index = 0
        elif self._current_match_index < 0:
            self._current_match_index = len(self._search_matches) - 1

        # Reapply highlights (updates current match color)
        self.apply_highlights()

        # Scroll to current match
        start, length = self._search_matches[self._current_match_index]
        cursor = self.log_area.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(start + length, QTextCursor.MoveMode.KeepAnchor)
        self.log_area.setTextCursor(cursor)  # Triggers scroll

        # Update match label
        self.update_match_label()

    def update_match_label(self):
        """Update match count display."""
        if not self._search_matches:
            self.match_label.setText("0 / 0")
        else:
            current = self._current_match_index + 1
            total = len(self._search_matches)
            if total > 1000:
                self.match_label.setText(f"{current} / 1000+")
            else:
                self.match_label.setText(f"{current} / {total}")

    # T-007: Clear logs
    def clear_log_area(self):
        """Clear all log content with confirmation for large logs."""
        line_count = self.log_area.document().blockCount()

        if line_count > 100:
            # Show confirmation dialog
            reply = QMessageBox.question(
                self,
                self.tr("Confirm Clear"),
                self.tr(f"Are you sure you want to clear {line_count} lines of logs?"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

        # Clear log area
        self.log_area.clear()

        # Clear search state
        self.clear_highlights()
        self.match_label.setText("0 / 0")

    # T-008: Keyboard shortcuts
    def setup_shortcuts(self):
        """Setup keyboard shortcuts for search functionality."""
        # Ctrl+F: Focus search input
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(
            self.search_input.setFocus
        )

        # Enter / F3: Next match
        QShortcut(QKeySequence("Return"), self.search_input).activated.connect(
            lambda: self.navigate_to_match(1)
        )
        QShortcut(QKeySequence("F3"), self).activated.connect(
            lambda: self.navigate_to_match(1)
        )

        # Shift+Enter / Shift+F3: Previous match
        QShortcut(QKeySequence("Shift+Return"), self.search_input).activated.connect(
            lambda: self.navigate_to_match(-1)
        )
        QShortcut(QKeySequence("Shift+F3"), self).activated.connect(
            lambda: self.navigate_to_match(-1)
        )

        # Esc: Clear search input
        QShortcut(QKeySequence("Escape"), self.search_input).activated.connect(
            self.search_input.clear
        )

    # T-009: Settings persistence
    def save_search_settings(self):
        """Save search options to settings."""
        self.settings.setValue("search/case_sensitive", self.case_checkbox.isChecked())
        self.settings.setValue("search/use_regex", self.regex_checkbox.isChecked())

    def load_search_settings(self):
        """Load search options from settings."""
        case_sensitive = self.settings.value("search/case_sensitive", False, type=bool)
        use_regex = self.settings.value("search/use_regex", False, type=bool)

        self.case_checkbox.setChecked(case_sensitive)
        self.regex_checkbox.setChecked(use_regex)

