#!/usr/bin/env python3
"""
Manual test script for log search功能
Run with: QT_QPA_PLATFORM=offscreen python tests/manual_test_log_search.py
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PyQt6.QtWidgets import QApplication
from docx_server_launcher.gui.main_window import MainWindow


def test_ui_exists():
    """Test that all UI elements exist."""
    app = QApplication(sys.argv)
    window = MainWindow()

    # Check all widgets exist
    assert hasattr(window, 'search_input'), "search_input missing"
    assert hasattr(window, 'prev_btn'), "prev_btn missing"
    assert hasattr(window, 'next_btn'), "next_btn missing"
    assert hasattr(window, 'match_label'), "match_label missing"
    assert hasattr(window, 'case_checkbox'), "case_checkbox missing"
    assert hasattr(window, 'regex_checkbox'), "regex_checkbox missing"
    assert hasattr(window, 'clear_log_btn'), "clear_log_btn missing"

    print("✓ All UI elements exist")


def test_plain_search():
    """Test plain text search."""
    app = QApplication(sys.argv)
    window = MainWindow()

    # Test case insensitive
    text = "Error error ERROR"
    matches = window.find_matches_plain(text, "error", case_sensitive=False)
    assert len(matches) == 3, f"Expected 3 matches, got {len(matches)}"
    assert matches == [(0, 5), (6, 5), (12, 5)]

    # Test case sensitive
    matches = window.find_matches_plain(text, "error", case_sensitive=True)
    assert len(matches) == 1, f"Expected 1 match, got {len(matches)}"

    # Test empty pattern
    matches = window.find_matches_plain(text, "", case_sensitive=False)
    assert matches == [], "Empty pattern should return empty list"

    print("✓ Plain search works correctly")


def test_regex_search():
    """Test regex search."""
    app = QApplication(sys.argv)
    window = MainWindow()

    text = "Date: 2026-01-22, Time: 10:30:45"
    matches = window.find_matches_regex(text, r"\d{4}-\d{2}-\d{2}", case_sensitive=False)
    assert len(matches) == 1
    assert matches == [(6, 10)]  # "2026-01-22"

    print("✓ Regex search works correctly")


def test_regex_validation():
    """Test regex safety validation."""
    app = QApplication(sys.argv)
    window = MainWindow()

    # Dangerous regex
    is_safe, msg = window.validate_regex_safety(r"(a+)+b")
    assert not is_safe, "Dangerous regex should be detected"
    assert "dangerous" in msg.lower()

    # Safe regex
    is_safe, msg = window.validate_regex_safety(r"\d{4}-\d{2}-\d{2}")
    assert is_safe, "Safe regex should pass"
    assert msg == ""

    print("✓ Regex validation works correctly")


def test_highlight_manager():
    """Test highlight application."""
    app = QApplication(sys.argv)
    window = MainWindow()

    window.log_area.setPlainText("ERROR error ERROR")
    window._search_matches = [(0, 5), (6, 5), (12, 5)]
    window._current_match_index = 1

    window.apply_highlights()

    selections = window.log_area.extraSelections()
    assert len(selections) == 3, f"Expected 3 selections, got {len(selections)}"

    print("✓ Highlight manager works correctly")


def test_navigation():
    """Test result navigation."""
    app = QApplication(sys.argv)
    window = MainWindow()

    window._search_matches = [(0, 5), (6, 5)]
    window._current_match_index = 0

    # Navigate forward
    window.navigate_to_match(1)
    assert window._current_match_index == 1

    # Navigate forward (wrap)
    window.navigate_to_match(1)
    assert window._current_match_index == 0

    # Navigate backward
    window.navigate_to_match(-1)
    assert window._current_match_index == 1

    print("✓ Navigation works correctly")


def test_integrated_search():
    """Test integrated search flow."""
    app = QApplication(sys.argv)
    window = MainWindow()

    window.log_area.setPlainText("ERROR\nINFO\nERROR\nWARNING\nERROR")

    # Perform search
    window.search_input.setText("ERROR")
    window.perform_search()

    # Should find 3 matches
    assert len(window._search_matches) == 3
    assert window.match_label.text() == "1 / 3"

    print("✓ Integrated search works correctly")


if __name__ == "__main__":
    print("Running manual tests for log search feature...\n")

    try:
        test_ui_exists()
        test_plain_search()
        test_regex_search()
        test_regex_validation()
        test_highlight_manager()
        test_navigation()
        test_integrated_search()

        print("\n✅ All tests passed!")
        sys.exit(0)

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
