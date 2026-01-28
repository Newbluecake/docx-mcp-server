"""
Shared fixtures for integration tests.

This conftest provides common fixtures to reduce code duplication
and improve test performance.
"""

import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication, QMessageBox


@pytest.fixture(scope="module")
def qapp():
    """
    Module-scoped QApplication instance.

    Reuses the same QApplication across all tests in a module
    to avoid repeated initialization overhead.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't quit - let pytest-qt handle cleanup


@pytest.fixture(autouse=True)
def mock_message_boxes(monkeypatch):
    """
    Automatically mock all QMessageBox dialogs to prevent blocking.

    This fixture is autouse=True, so it applies to all tests
    without needing to be explicitly requested.
    """
    # Mock all QMessageBox methods that show modal dialogs
    monkeypatch.setattr(
        'PyQt6.QtWidgets.QMessageBox.information',
        MagicMock(return_value=QMessageBox.StandardButton.Ok)
    )
    monkeypatch.setattr(
        'PyQt6.QtWidgets.QMessageBox.critical',
        MagicMock(return_value=QMessageBox.StandardButton.Ok)
    )
    monkeypatch.setattr(
        'PyQt6.QtWidgets.QMessageBox.warning',
        MagicMock(return_value=QMessageBox.StandardButton.Ok)
    )
    monkeypatch.setattr(
        'PyQt6.QtWidgets.QMessageBox.question',
        MagicMock(return_value=QMessageBox.StandardButton.Yes)
    )


@pytest.fixture
def mock_wait_methods():
    """
    Provides mocks for MainWindow wait methods.

    Use this fixture when testing methods that call
    _wait_for_server_stop or _wait_for_server_start.

    Example:
        def test_something(main_window, mock_wait_methods):
            mock_wait_methods.patch_window(main_window)
            # Now wait methods return immediately
    """
    class WaitMethodMocks:
        def patch_window(self, window):
            """Patch wait methods on a MainWindow instance."""
            window._wait_for_server_stop = MagicMock(return_value=True)
            window._wait_for_server_start = MagicMock(return_value=True)

    return WaitMethodMocks()
