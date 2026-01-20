import os
import sys
from typing import Dict
from PyQt6.QtCore import QObject, QSettings, QTranslator, QCoreApplication, pyqtSignal

class LanguageManager(QObject):
    """
    Manages application language settings and translation loading.
    """
    language_changed = pyqtSignal(str)

    def __init__(self, settings_prefix: str = "DocxMCP"):
        super().__init__()
        self.settings = QSettings(settings_prefix, "Launcher")
        self.translator = QTranslator()

        # Default to system locale? For now, default to English as requested or stored value
        # Ideally check QLocale.system().name() if not set, but requirements said "en_US" default for now
        self.current_locale = self.settings.value("language", "en_US")

        # Initialize
        # We don't auto-load in __init__ to allow caller to hook signals first if needed,
        # but usually we want state restored immediately.
        self.load_language(str(self.current_locale))

    def get_available_languages(self) -> Dict[str, str]:
        """Returns a dict of locale_code: display_name."""
        return {
            "en_US": "English",
            "zh_CN": "简体中文"
        }

    def load_language(self, locale_code: str):
        """
        Load the specified language.
        """
        # Save preference
        self.settings.setValue("language", locale_code)
        self.settings.sync()  # Force save to ensure persistence
        self.current_locale = locale_code

        app = QCoreApplication.instance()
        if not app:
            # Allow usage without running QApp (e.g. basic unit tests)
            return

        # Always remove old translator first to reset to default/source
        app.removeTranslator(self.translator)

        if locale_code == "en_US":
            # English is source language
            self.language_changed.emit(locale_code)
            return

        # Determine path to .qm files
        base_path = self._get_resource_path()
        qm_file = os.path.join(base_path, "translations", f"{locale_code}.qm")

        # Try to load
        if self.translator.load(qm_file):
            app.installTranslator(self.translator)
        else:
            # If we expected to load but failed (e.g. file missing during dev), log it
            # For now just print to stderr
            print(f"Warning: Could not load translation file: {qm_file}", file=sys.stderr)

        self.language_changed.emit(locale_code)

    def _get_resource_path(self) -> str:
        """Get the base path for resources, handling frozen (PyInstaller) vs dev env."""
        if getattr(sys, 'frozen', False):
            # In PyInstaller bundle, resources are at sys._MEIPASS
            return sys._MEIPASS
        else:
            # In dev, assuming we are in src/docx_server_launcher/core/
            # Resources are in src/docx_server_launcher/resources/
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # ../resources
            return os.path.abspath(os.path.join(current_dir, "..", "resources"))
