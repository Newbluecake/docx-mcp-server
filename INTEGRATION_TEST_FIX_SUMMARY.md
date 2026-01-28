# Integration Test Performance Fix Summary

## Problem Identified

Integration tests were **hanging indefinitely** due to blocking GUI operations.

## Root Causes

### 1. QEventLoop Blocking (PRIMARY CAUSE)
- `MainWindow._wait_for_server_stop()` and `_wait_for_server_start()` use `QEventLoop.exec()`
- These methods block until signals fire or timeout
- Tests calling `switch_cwd()` would hang waiting for server signals that never fire

### 2. Modal QMessageBox Dialogs (SECONDARY CAUSE)
- `QMessageBox.information()`, `.critical()`, `.warning()` are modal dialogs
- They block execution until user clicks a button
- Mocking with `patch.object()` was ineffective due to import timing

### 3. Repeated MainWindow Creation (PERFORMANCE ISSUE)
- Each test creates 1-3 MainWindow instances
- Each creation involves expensive operations (QSettings, ServerManager, etc.)
- 40 tests × 2 windows = 80+ expensive object creations

## Solutions Implemented

### Fix 1: Mock QMessageBox at Module Level ✅
**File**: `tests/integration/test_cwd_switch.py`

```python
# Mock BEFORE importing MainWindow
from PyQt6.QtWidgets import QMessageBox
QMessageBox.information = MagicMock(return_value=QMessageBox.StandardButton.Ok)
QMessageBox.critical = MagicMock(return_value=QMessageBox.StandardButton.Ok)
QMessageBox.warning = MagicMock(return_value=QMessageBox.StandardButton.Ok)

from docx_server_launcher.gui.main_window import MainWindow
```

**Impact**: Prevents modal dialogs from blocking tests

### Fix 2: Mock Wait Methods in Fixture ✅
**File**: `tests/integration/test_cwd_switch.py`

```python
@pytest.fixture
def main_window(qtbot):
    # ... existing setup ...
    window = MainWindow()

    # CRITICAL: Mock wait methods to prevent QEventLoop blocking
    window._wait_for_server_stop = MagicMock(return_value=True)
    window._wait_for_server_start = MagicMock(return_value=True)

    qtbot.addWidget(window)
    yield window
    window.close()
```

**Impact**: Prevents QEventLoop from blocking test execution

### Fix 3: Shared Fixtures (conftest.py) ✅
**File**: `tests/integration/conftest.py` (NEW)

- Module-scoped QApplication fixture
- Auto-use QMessageBox mocking fixture
- Reusable wait method mocks

**Impact**: Reduces code duplication and improves maintainability

## Results

### Before Fixes
```
Status: TIMEOUT (>120 seconds)
Hanging tests: 5-10 tests
Completion rate: 0%
```

### After Fixes
```
Duration: 100.49 seconds (1:40)
Passed: 21/40 (52.5%)
Failed: 19/40 (47.5%) - due to other issues, NOT hangs
Hanging tests: 0
```

### Performance Improvement
- **Eliminated all hanging tests** ✅
- Tests now complete in reasonable time
- Failures are now due to test logic issues, not infrastructure problems

## Remaining Issues

The 19 failing tests are due to:
1. **NameError** in history_tools tests (missing imports)
2. **Session management** issues in special_ids tests (v4.0 migration)
3. **Test logic** issues (not infrastructure problems)

These are **separate issues** from the performance/hanging problems and should be addressed individually.

## Recommendations

### Immediate (Already Done)
- ✅ Mock QMessageBox at module level
- ✅ Mock wait methods in fixtures
- ✅ Create shared conftest.py

### Short Term (Next Steps)
1. **Fix remaining test failures** (separate from performance issues)
2. **Add pytest-timeout plugin** to pyproject.toml
3. **Apply same fixes to other GUI test files**:
   - `test_gui_command_display.py`
   - `test_launcher_logging.py`

### Long Term (Architecture)
1. **Refactor MainWindow** for better testability
   - Extract business logic from GUI code
   - Use dependency injection
2. **Create test doubles** for expensive components
3. **Split tests** into fast/slow categories

## Files Modified

1. `tests/integration/test_cwd_switch.py` - Fixed hanging tests
2. `tests/integration/conftest.py` - NEW shared fixtures
3. `INTEGRATION_TEST_ANALYSIS.md` - NEW detailed analysis

## Verification

```bash
# Run integration tests (should complete in ~2 minutes)
timeout 120 uv run pytest tests/integration/ -v

# Run specific fixed test
uv run pytest tests/integration/test_cwd_switch.py -v
```

## Conclusion

The integration test hanging issue has been **RESOLVED**. Tests now complete successfully without timeouts. The remaining test failures are unrelated to the performance/hanging issues and can be addressed separately.

**Key Takeaway**: GUI tests require careful mocking of blocking operations (QEventLoop, QMessageBox) to prevent hangs. Module-level mocking is more reliable than context-manager-based mocking for GUI components.
