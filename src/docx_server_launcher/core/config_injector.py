import json
import os
from typing import Dict, Any

class ConfigInjector:
    """
    Injects docx-server configuration into Claude Desktop config file.
    """

    def inject(self, config_path: str, server_url: str) -> bool:
        """
        Update the Claude Desktop configuration file with the current server settings.

        Args:
            config_path: Path to claude_desktop_config.json
            server_url: The SSE URL (e.g., http://127.0.0.1:8000/sse)

        Returns:
            bool: True if successful, False otherwise
        """
        if not os.path.exists(config_path):
            # Try to create it if it doesn't exist?
            # Usually better to ensure the directory exists at least.
            config_dir = os.path.dirname(config_path)
            if not os.path.exists(config_dir):
                return False # Directory doesn't exist, user might have picked wrong path

            # Start with empty config
            config = {}
        else:
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except Exception:
                # Corrupt file or other issue
                return False

        if "mcpServers" not in config:
            config["mcpServers"] = {}

        # Config for SSE
        config["mcpServers"]["docx-server"] = {
            "url": server_url,
            "transport": "sse"
        }

        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception:
            return False

    @staticmethod
    def get_default_config_path() -> str:
        """
        Get the default path for Claude Desktop config on Windows.
        Returns empty string if not on Windows or APPDATA not set.
        """
        if os.name == 'nt':
            app_data = os.getenv('APPDATA')
            if app_data:
                return os.path.join(app_data, 'Claude', 'claude_desktop_config.json')
        return ""
