# GUI Integration Test Best Practices

## Quick Reference for Writing GUI Tests

### Template for New GUI Integration Tests

```python
"""
Integration test for [feature name]
"""

import pytest
import os
from unittest.mock import MagicMock

# STEP 1: Set offscreen platform BEFORE any Qt imports
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# STEP 2: Mock QMessageBox BEFORE importing MainWindow
from PyQt6.QtWidgets import QApplication, QMessageBox

QMessageBox.information = MagicMock(return_value=QMessageBox.StandardButton.Ok)
QMessageBox.critical = MagicMock(return_value=QMessageBox.StandardButton.Ok)
QMessageBox.warning = MagicMock(return_value=QMessageBox.StandardButton.Ok)
QMessageBox.question = MagicMock(return_value=QMessageBox.StandardButton.Yes)

# STEP 3: Import GUI components
from docx_server_launcher.gui.main_window import MainWindow


# STEP 4: Create fixture with proper mocking
@pytest.fixture
def main_window(qtbot, request):
    """Create MainWindow with all blocking operations mocked."""
    window = MainWindow()

    # Mock wait methods to prevent QEventLoop blocking
    window._wait_for_server_stop = MagicMock(return_value=True)
    window._wait_for_server_start = MagicMock(return_value=True)

    qtbot.addWidget(window)

    def cleanup():
        window.close()
        window.deleteLater()
        QApplication.instance().processEvents()

    request.addfinalizer(cleanup)
    return window


# STEP 5: Write tests
def test_something(main_window, qtbot):
    """Test description."""
    # Your test code here
    assert main_window.some_widget.isVisible()
```

## Common Pitfalls to Avoid

### ❌ DON'T: Mock QMessageBox in test body
```python
def test_something(main_window):
    with patch.object(QMessageBox, 'information'):  # Too late!
        main_window.some_action()  # May still hang
```

### ✅ DO: Mock QMessageBox at module level
```python
# At top of file, before importing MainWindow
QMessageBox.information = MagicMock(return_value=QMessageBox.StandardButton.Ok)
```

---

### ❌ DON'T: Forget to mock wait methods
```python
@pytest.fixture
def main_window(qtbot):
    window = MainWindow()  # Will hang if test calls switch_cwd()
    return window
```

### ✅ DO: Mock wait methods in fixture
```python
@pytest.fixture
def main_window(qtbot):
    window = MainWindow()
    window._wait_for_server_stop = MagicMock(return_value=True)
    window._wait_for_server_start = MagicMock(return_value=True)
    return window
```

---

### ❌ DON'T: Create multiple MainWindow instances unnecessarily
```python
def test_feature_1():
    window = MainWindow()  # Expensive!
    # test code

def test_feature_2():
    window = MainWindow()  # Another expensive creation!
    # test code
```

### ✅ DO: Use shared fixtures
```python
@pytest.fixture(scope="module")
def main_window(qtbot):
    window = MainWindow()
    # ... mocking ...
    yield window
    window.close()

def test_feature_1(main_window):
    # Reuses same window

def test_feature_2(main_window):
    # Reuses same window
```

---

### ❌ DON'T: Import MainWindow before mocking
```python
from docx_server_launcher.gui.main_window import MainWindow

# Too late - MainWindow already imported!
QMessageBox.information = MagicMock()
```

### ✅ DO: Mock before importing
```python
# Mock first
QMessageBox.information = MagicMock()

# Then import
from docx_server_launcher.gui.main_window import MainWindow
```

## Debugging Hanging Tests

If a test hangs, check these in order:

1. **Is QMessageBox mocked at module level?**
   - Look for `QMessageBox.information = MagicMock()` before MainWindow import

2. **Are wait methods mocked in fixture?**
   - Look for `window._wait_for_server_stop = MagicMock(return_value=True)`

3. **Is QT_QPA_PLATFORM set to offscreen?**
   - Look for `os.environ["QT_QPA_PLATFORM"] = "offscreen"`

4. **Are there other blocking operations?**
   - Search for `QEventLoop`, `QDialog.exec()`, `QMessageBox` calls
   - Mock them at module level

## Performance Tips

### Use Module-Scoped Fixtures
```python
@pytest.fixture(scope="module")
def qapp():
    """Reuse QApplication across all tests in module."""
    return QApplication.instance() or QApplication([])
```

### Mock Expensive Operations
```python
@pytest.fixture
def main_window(qtbot, monkeypatch):
    # Mock file I/O
    monkeypatch.setattr('PyQt6.QtCore.QSettings', MagicMock())

    # Mock subprocess operations
    monkeypatch.setattr('subprocess.Popen', MagicMock())

    window = MainWindow()
    # ... rest of fixture
```

### Use Shared conftest.py
Place common fixtures in `tests/integration/conftest.py`:
```python
@pytest.fixture(autouse=True)
def mock_message_boxes(monkeypatch):
    """Auto-mock all QMessageBox dialogs."""
    monkeypatch.setattr('PyQt6.QtWidgets.QMessageBox.information', MagicMock())
    # ... other mocks
```

## Checklist for New GUI Tests

- [ ] Set `QT_QPA_PLATFORM=offscreen` before Qt imports
- [ ] Mock QMessageBox at module level before MainWindow import
- [ ] Mock wait methods in fixture
- [ ] Use qtbot.addWidget() for proper cleanup
- [ ] Add cleanup finalizer to close window
- [ ] Consider using module-scoped fixtures for expensive setup
- [ ] Verify test completes in < 5 seconds
- [ ] Check that test doesn't hang with `timeout 10 pytest test_file.py`

## Example: Complete Test File

See `tests/integration/test_cwd_switch.py` for a complete example following all best practices.

---

**Last Updated:** 2026-01-28
**Related Docs:**
- INTEGRATION_TEST_ANALYSIS.md
- INTEGRATION_TEST_FIXES_APPLIED.md
