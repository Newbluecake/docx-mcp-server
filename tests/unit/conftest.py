"""
Shared test fixtures for unit tests.
"""
import pytest
import sys
import os


@pytest.fixture(scope="session")
def qapp():
    """
    Qt application fixture for GUI tests.

    This fixture creates a QApplication instance that can be shared across tests.
    Qt requires a QApplication to exist before creating any Qt widgets.

    Skips if:
    - PyQt6 is not installed
    - Running in headless environment (no DISPLAY on Linux)
    """
    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        pytest.skip("PyQt6 not available, skipping GUI tests")

    # Check if we're in a headless environment (CI/Linux without X server)
    if sys.platform.startswith('linux') and not os.environ.get('DISPLAY'):
        pytest.skip("No DISPLAY available, skipping GUI tests (headless environment)")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    yield app

    # Cleanup is handled automatically when the application exits
