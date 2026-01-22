"""
Unit tests for Log Search Feature

Tests cover all search functionality including:
- T-001: Search toolbar UI
- T-002: Plain text search engine
- T-003: Regex search engine
- T-004: Highlight manager
- T-005: Debounced search mechanism
- T-006: Result navigation
- T-007: Clear logs
- T-008: Keyboard shortcuts
- T-009: Settings persistence
"""

import pytest
import re
from typing import List, Tuple
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QColor
from docx_server_launcher.gui.main_window import MainWindow


# ========== T-001: Search Toolbar UI ==========

def test_search_toolbar_exists(qtbot):
    """Test that search toolbar UI elements exist."""
    window = MainWindow()
    qtbot.addWidget(window)

    # Check all required widgets exist
    assert hasattr(window, 'search_input'), "search_input should exist"
    assert hasattr(window, 'prev_btn'), "prev_btn should exist"
    assert hasattr(window, 'next_btn'), "next_btn should exist"
    assert hasattr(window, 'match_label'), "match_label should exist"
    assert hasattr(window, 'case_checkbox'), "case_checkbox should exist"
    assert hasattr(window, 'regex_checkbox'), "regex_checkbox should exist"
    assert hasattr(window, 'clear_log_btn'), "clear_log_btn should exist"


def test_search_toolbar_initial_state(qtbot):
    """Test search toolbar initial state."""
    window = MainWindow()
    qtbot.addWidget(window)

    # Initial match label should show "0 / 0"
    assert window.match_label.text() == "0 / 0"

    # Checkboxes should be unchecked by default (unless loaded from settings)
    # We'll verify loaded state in persistence tests


def test_search_toolbar_layout(qtbot):
    """Test that search toolbar is in the log group."""
    window = MainWindow()
    qtbot.addWidget(window)

    # Verify search toolbar is part of log_group layout
    log_layout = window.log_group.layout()
    assert log_layout is not None

    # Should have at least 2 rows (search toolbar + log area)
    # Since we add 2 layouts + 1 widget
    assert log_layout.count() >= 3


# ========== T-002: Plain Text Search Engine ==========

def test_find_matches_plain_case_insensitive(qtbot):
    """Test plain text search (case insensitive)."""
    window = MainWindow()
    qtbot.addWidget(window)

    text = "Error error ERROR"
    matches = window.find_matches_plain(text, "error", case_sensitive=False)

    assert len(matches) == 3
    assert matches == [(0, 5), (6, 5), (12, 5)]


def test_find_matches_plain_case_sensitive(qtbot):
    """Test plain text search (case sensitive)."""
    window = MainWindow()
    qtbot.addWidget(window)

    text = "Error error ERROR"
    matches = window.find_matches_plain(text, "error", case_sensitive=True)

    assert len(matches) == 1
    assert matches == [(6, 5)]


def test_find_matches_plain_overlapping(qtbot):
    """Test overlapping matches."""
    window = MainWindow()
    qtbot.addWidget(window)

    text = "aaa"
    matches = window.find_matches_plain(text, "aa", case_sensitive=False)

    # Should find 2 matches: position 0 and position 1
    assert len(matches) == 2
    assert matches == [(0, 2), (1, 2)]


def test_find_matches_plain_empty(qtbot):
    """Test empty pattern returns empty list."""
    window = MainWindow()
    qtbot.addWidget(window)

    text = "Some text"
    matches = window.find_matches_plain(text, "", case_sensitive=False)

    assert matches == []


def test_find_matches_plain_no_match(qtbot):
    """Test no matches found."""
    window = MainWindow()
    qtbot.addWidget(window)

    text = "Hello World"
    matches = window.find_matches_plain(text, "xyz", case_sensitive=False)

    assert matches == []


# ========== T-003: Regex Search Engine ==========

def test_find_matches_regex_basic(qtbot):
    """Test basic regex search."""
    window = MainWindow()
    qtbot.addWidget(window)

    text = "Date: 2026-01-22, Time: 10:30:45"
    matches = window.find_matches_regex(text, r"\d{4}-\d{2}-\d{2}", case_sensitive=False)

    assert len(matches) == 1
    assert matches == [(6, 10)]  # "2026-01-22"


def test_find_matches_regex_case_insensitive(qtbot):
    """Test regex with case insensitive flag."""
    window = MainWindow()
    qtbot.addWidget(window)

    text = "ERROR Error error"
    matches = window.find_matches_regex(text, r"error", case_sensitive=False)

    assert len(matches) == 3


def test_find_matches_regex_case_sensitive(qtbot):
    """Test regex with case sensitive flag."""
    window = MainWindow()
    qtbot.addWidget(window)

    text = "ERROR Error error"
    matches = window.find_matches_regex(text, r"error", case_sensitive=True)

    assert len(matches) == 1


def test_find_matches_regex_invalid(qtbot):
    """Test invalid regex raises ValueError."""
    window = MainWindow()
    qtbot.addWidget(window)

    text = "Some text"

    with pytest.raises(ValueError, match="Invalid regex"):
        window.find_matches_regex(text, "[(", case_sensitive=False)


def test_validate_regex_safety_dangerous(qtbot):
    """Test dangerous regex detection."""
    window = MainWindow()
    qtbot.addWidget(window)

    is_safe, msg = window.validate_regex_safety(r"(a+)+b")

    assert not is_safe
    assert "dangerous" in msg.lower()


def test_validate_regex_safety_safe(qtbot):
    """Test safe regex passes validation."""
    window = MainWindow()
    qtbot.addWidget(window)

    is_safe, msg = window.validate_regex_safety(r"\d{4}-\d{2}-\d{2}")

    assert is_safe
    assert msg == ""


# ========== T-004: Highlight Manager ==========

def test_apply_highlights(qtbot):
    """Test highlight application."""
    window = MainWindow()
    qtbot.addWidget(window)

    window.log_area.setPlainText("ERROR error ERROR")
    window._search_matches = [(0, 5), (6, 5), (12, 5)]
    window._current_match_index = 1

    window.apply_highlights()

    selections = window.log_area.extraSelections()
    assert len(selections) == 3

    # Verify current match (index 1) is orange
    assert selections[1].format.background().color() == QColor("#FFA500")

    # Verify other matches are yellow
    assert selections[0].format.background().color() == QColor("#FFFF00")
    assert selections[2].format.background().color() == QColor("#FFFF00")


def test_clear_highlights(qtbot):
    """Test clearing all highlights."""
    window = MainWindow()
    qtbot.addWidget(window)

    # Set up some highlights
    window._search_matches = [(0, 5), (6, 5)]
    window._current_match_index = 0
    window.apply_highlights()

    # Clear
    window.clear_highlights()

    # Verify cleared
    assert window.log_area.extraSelections() == []
    assert window._search_matches == []
    assert window._current_match_index == -1


# ========== T-005: Debounced Search ==========

def test_debounce_search(qtbot):
    """Test search debouncing (300ms delay)."""
    window = MainWindow()
    qtbot.addWidget(window)

    window.log_area.setPlainText("ERROR error ERROR")

    # Rapid input changes
    window.search_input.setText("e")
    window.search_input.setText("er")
    window.search_input.setText("err")

    # Wait for debounce (350ms to be safe)
    qtbot.wait(350)

    # Should have searched for "err" (3 matches)
    assert len(window._search_matches) == 3


def test_search_option_changed_immediate(qtbot):
    """Test that changing search options triggers immediate search."""
    window = MainWindow()
    qtbot.addWidget(window)

    window.log_area.setPlainText("ERROR error")
    window.search_input.setText("error")

    # Wait for initial search
    qtbot.wait(350)

    # Should match 2 (case insensitive)
    assert len(window._search_matches) == 2

    # Enable case sensitive
    window.case_checkbox.setChecked(True)

    # No need to wait, should be immediate
    qtbot.wait(50)

    # Should match 1 (case sensitive)
    assert len(window._search_matches) == 1


def test_search_error_display(qtbot):
    """Test error display for invalid regex."""
    window = MainWindow()
    qtbot.addWidget(window)

    window.regex_checkbox.setChecked(True)
    window.search_input.setText("[(")

    # Wait for search
    qtbot.wait(350)

    # Should show error
    assert "red" in window.search_input.styleSheet().lower()
    assert window.match_label.text() == "Error"


# ========== T-006: Result Navigation ==========

def test_navigate_to_match_forward(qtbot):
    """Test navigating forward through matches."""
    window = MainWindow()
    qtbot.addWidget(window)

    window.log_area.setPlainText("INFO ERROR INFO ERROR INFO")
    window._search_matches = [(5, 5), (16, 5)]  # 2 "ERROR"
    window._current_match_index = 0

    # Navigate forward
    window.navigate_to_match(1)

    assert window._current_match_index == 1
    assert window.match_label.text() == "2 / 2"


def test_navigate_to_match_backward(qtbot):
    """Test navigating backward through matches."""
    window = MainWindow()
    qtbot.addWidget(window)

    window.log_area.setPlainText("INFO ERROR INFO ERROR INFO")
    window._search_matches = [(5, 5), (16, 5)]
    window._current_match_index = 1

    # Navigate backward
    window.navigate_to_match(-1)

    assert window._current_match_index == 0
    assert window.match_label.text() == "1 / 2"


def test_navigate_to_match_wrap_forward(qtbot):
    """Test forward navigation wraps to beginning."""
    window = MainWindow()
    qtbot.addWidget(window)

    window._search_matches = [(0, 5), (6, 5)]
    window._current_match_index = 1  # Last match

    # Navigate forward (should wrap to 0)
    window.navigate_to_match(1)

    assert window._current_match_index == 0


def test_navigate_to_match_wrap_backward(qtbot):
    """Test backward navigation wraps to end."""
    window = MainWindow()
    qtbot.addWidget(window)

    window._search_matches = [(0, 5), (6, 5)]
    window._current_match_index = 0  # First match

    # Navigate backward (should wrap to last)
    window.navigate_to_match(-1)

    assert window._current_match_index == 1


def test_update_match_label_normal(qtbot):
    """Test match label update with normal count."""
    window = MainWindow()
    qtbot.addWidget(window)

    window._search_matches = [(0, 5), (6, 5), (12, 5)]
    window._current_match_index = 1

    window.update_match_label()

    assert window.match_label.text() == "2 / 3"


def test_update_match_label_over_limit(qtbot):
    """Test match label shows '1000+' when over 1000 matches."""
    window = MainWindow()
    qtbot.addWidget(window)

    # Simulate 1001 matches (truncated to 1000)
    window._search_matches = [(i, 1) for i in range(1000)]
    window._current_match_index = 0

    window.update_match_label()

    assert "1000+" in window.match_label.text()


# ========== T-007: Clear Logs ==========

def test_clear_log_area_small(qtbot):
    """Test clearing logs without confirmation (<100 lines)."""
    window = MainWindow()
    qtbot.addWidget(window)

    window.log_area.setPlainText("\n".join([f"Line {i}" for i in range(50)]))

    window.clear_log_area()

    assert window.log_area.toPlainText() == ""
    assert window.match_label.text() == "0 / 0"


def test_clear_log_area_large_confirmed(qtbot, monkeypatch):
    """Test clearing logs with confirmation (>100 lines)."""
    window = MainWindow()
    qtbot.addWidget(window)

    window.log_area.setPlainText("\n".join([f"Line {i}" for i in range(150)]))

    # Mock confirmation dialog to return Yes
    monkeypatch.setattr(
        QMessageBox, 'question',
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes
    )

    window.clear_log_area()

    assert window.log_area.toPlainText() == ""


def test_clear_log_area_large_cancelled(qtbot, monkeypatch):
    """Test clearing logs cancelled by user (>100 lines)."""
    window = MainWindow()
    qtbot.addWidget(window)

    original_text = "\n".join([f"Line {i}" for i in range(150)])
    window.log_area.setPlainText(original_text)

    # Mock confirmation dialog to return No
    monkeypatch.setattr(
        QMessageBox, 'question',
        lambda *args, **kwargs: QMessageBox.StandardButton.No
    )

    window.clear_log_area()

    # Text should remain unchanged
    assert window.log_area.toPlainText() == original_text


# ========== T-008: Keyboard Shortcuts ==========

def test_shortcut_ctrl_f(qtbot):
    """Test Ctrl+F focuses search input."""
    window = MainWindow()
    qtbot.addWidget(window)

    # Simulate Ctrl+F
    qtbot.keyClick(window, Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier)

    # Verify search input has focus
    assert window.search_input.hasFocus()


def test_shortcut_f3_navigation(qtbot):
    """Test F3 navigates to next match."""
    window = MainWindow()
    qtbot.addWidget(window)

    window.log_area.setPlainText("ERROR ERROR ERROR")
    window._search_matches = [(0, 5), (6, 5), (12, 5)]
    window._current_match_index = 0

    # Press F3
    qtbot.keyClick(window, Qt.Key.Key_F3)

    # Should navigate to next match
    assert window._current_match_index == 1


def test_shortcut_shift_f3_navigation(qtbot):
    """Test Shift+F3 navigates to previous match."""
    window = MainWindow()
    qtbot.addWidget(window)

    window._search_matches = [(0, 5), (6, 5)]
    window._current_match_index = 1

    # Press Shift+F3
    qtbot.keyClick(window, Qt.Key.Key_F3, Qt.KeyboardModifier.ShiftModifier)

    # Should navigate to previous match
    assert window._current_match_index == 0


def test_shortcut_escape_clears_search(qtbot):
    """Test Escape key clears search input."""
    window = MainWindow()
    qtbot.addWidget(window)

    # Set focus to search input
    window.search_input.setFocus()
    window.search_input.setText("test")

    # Press Escape
    qtbot.keyClick(window.search_input, Qt.Key.Key_Escape)

    # Should clear search input
    assert window.search_input.text() == ""


def test_shortcut_enter_navigation(qtbot):
    """Test Enter key navigates to next match."""
    window = MainWindow()
    qtbot.addWidget(window)

    window._search_matches = [(0, 5), (6, 5)]
    window._current_match_index = 0

    # Set focus to search input
    window.search_input.setFocus()

    # Press Enter
    qtbot.keyClick(window.search_input, Qt.Key.Key_Return)

    # Should navigate to next match
    assert window._current_match_index == 1


# ========== T-009: Settings Persistence ==========

def test_settings_persistence(qtbot, tmp_path):
    """Test search settings are saved and restored."""
    # Create first window with test settings
    window1 = MainWindow()
    qtbot.addWidget(window1)

    # Use temporary settings file
    test_settings_path = str(tmp_path / "test.ini")
    window1.settings = QSettings(test_settings_path, QSettings.Format.IniFormat)

    # Set options
    window1.case_checkbox.setChecked(True)
    window1.regex_checkbox.setChecked(True)
    window1.save_search_settings()

    # Create second window and load settings
    window2 = MainWindow()
    qtbot.addWidget(window2)
    window2.settings = QSettings(test_settings_path, QSettings.Format.IniFormat)
    window2.load_search_settings()

    # Verify settings were restored
    assert window2.case_checkbox.isChecked() is True
    assert window2.regex_checkbox.isChecked() is True


def test_settings_default_values(qtbot, tmp_path):
    """Test default settings when no saved values exist."""
    window = MainWindow()
    qtbot.addWidget(window)

    # Use empty settings file
    test_settings_path = str(tmp_path / "empty.ini")
    window.settings = QSettings(test_settings_path, QSettings.Format.IniFormat)
    window.load_search_settings()

    # Should have default values (False)
    assert window.case_checkbox.isChecked() is False
    assert window.regex_checkbox.isChecked() is False


# ========== Performance Tests (T-005) ==========

def test_search_performance_large_log(qtbot):
    """Test search performance with 15000 lines."""
    import time

    window = MainWindow()
    qtbot.addWidget(window)

    # Generate 15000 lines
    log_text = "\n".join([f"[2026-01-22 10:{i:04d}] INFO Message {i}" for i in range(15000)])
    window.log_area.setPlainText(log_text)

    # Measure search time
    start = time.time()
    matches = window.find_matches_plain(log_text, "INFO", case_sensitive=False)
    elapsed = time.time() - start

    # Should complete in < 500ms
    assert elapsed < 0.5, f"Search took {elapsed}s, expected < 500ms"
    assert len(matches) == 15000


def test_highlight_performance(qtbot):
    """Test highlight application performance with 1000 matches."""
    import time

    window = MainWindow()
    qtbot.addWidget(window)

    # Generate text with 1000 "ERROR" occurrences
    text = " ".join(["ERROR"] * 1000)
    window.log_area.setPlainText(text)

    # Create 1000 matches
    window._search_matches = [(i * 6, 5) for i in range(1000)]
    window._current_match_index = 0

    # Measure highlight time
    start = time.time()
    window.apply_highlights()
    elapsed = time.time() - start

    # Should complete in < 100ms
    assert elapsed < 0.1, f"Highlight took {elapsed}s, expected < 100ms"
