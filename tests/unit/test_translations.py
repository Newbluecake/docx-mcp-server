"""
Unit tests for translation updates (T-011).
"""

import pytest
import xml.etree.ElementTree as ET
from pathlib import Path


class TestTranslations:
    """Test translation file updates."""

    @pytest.fixture
    def translation_file(self):
        """Get translation file path."""
        return Path(__file__).parent.parent.parent / "src" / "docx_server_launcher" / "resources" / "translations" / "zh_CN.ts"

    def test_translation_file_exists(self, translation_file):
        """Test that translation file exists."""
        assert translation_file.exists()

    def test_translation_file_valid_xml(self, translation_file):
        """Test that translation file is valid XML."""
        tree = ET.parse(translation_file)
        root = tree.getroot()
        assert root.tag == "TS"

    def test_new_cli_translations_present(self, translation_file):
        """Test that new CLI-related translations are present."""
        tree = ET.parse(translation_file)
        root = tree.getroot()

        # Get all translation sources
        sources = []
        for msg in root.findall(".//message"):
            source = msg.find("source")
            if source is not None and source.text:
                sources.append(source.text)

        # Check for new translations
        required_translations = [
            "Extra CLI Parameters (optional):",
            "e.g., --model opus --agent reviewer",
            "Launch Claude",
            "Claude CLI Not Found",
            "Claude CLI is required to use this feature.",
        ]

        for required in required_translations:
            assert required in sources, f"Missing translation for: {required}"

    def test_old_inject_translations_removed(self, translation_file):
        """Test that old injection-related translations are removed."""
        tree = ET.parse(translation_file)
        root = tree.getroot()

        # Get all translation sources
        sources = []
        for msg in root.findall(".//message"):
            source = msg.find("source")
            if source is not None and source.text:
                sources.append(source.text)

        # Check that old translations are NOT present
        obsolete_translations = [
            "Inject Config to Claude...",
            "Select Claude Desktop Config",
            "Confirm Injection",
            "Configuration injected successfully.\nPlease restart Claude Desktop.",
        ]

        for obsolete in obsolete_translations:
            assert obsolete not in sources, f"Obsolete translation still present: {obsolete}"

    def test_translations_have_chinese_text(self, translation_file):
        """Test that translations have Chinese text."""
        tree = ET.parse(translation_file)
        root = tree.getroot()

        # Check that translations have Chinese characters
        for msg in root.findall(".//message"):
            source = msg.find("source")
            translation = msg.find("translation")

            if source is not None and translation is not None:
                source_text = source.text
                translation_text = translation.text

                # For new CLI translations, verify they have Chinese
                if source_text in ["Launch Claude", "Extra CLI Parameters (optional):"]:
                    assert translation_text is not None
                    # Check for Chinese characters (Unicode range)
                    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in translation_text)
                    assert has_chinese, f"Translation for '{source_text}' lacks Chinese characters"

    def test_installation_instructions_translated(self, translation_file):
        """Test that installation instructions are translated."""
        tree = ET.parse(translation_file)
        root = tree.getroot()

        # Find installation instructions message
        for msg in root.findall(".//message"):
            source = msg.find("source")
            if source is not None and "Installation Options:" in source.text:
                translation = msg.find("translation")
                assert translation is not None
                assert translation.text is not None
                # Should contain Chinese
                has_chinese = any('\u4e00' <= char <= '\u9fff' for char in translation.text)
                assert has_chinese
                break
        else:
            pytest.fail("Installation instructions translation not found")
