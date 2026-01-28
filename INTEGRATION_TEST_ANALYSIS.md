# Integration Test Performance Analysis

## Executive Summary

Integration tests are experiencing severe performance issues, with tests hanging indefinitely. The root causes have been identified across multiple dimensions:

### Critical Issues (Causing Hangs)

1. **QEventLoop Blocking in `_wait_for_server_*` methods** ⚠️ CRITICAL
2. **Modal QMessageBox dialogs not properly mocked** ⚠️ CRITICAL
3. **Incomplete fixture mocking causing real I/O operations**
4. **Repeated MainWindow creation without proper cleanup**

---

## Detailed Analysis

### 1. QEventLoop Blocking (CRITICAL)

**Location**: `src/docx_server_launcher/gui/main_window.py`

**Problem**:
```python
def _wait_for_server_stop(self, timeout: int) -> bool:
    loop = QEventLoop()
    timer = QTimer()
    # ...
    loop.exec()  # ← BLOCKS until signal or timeout
```

**Impact**:
- Tests calling `switch_cwd()` hang waiting for `server_stopped` signal
- Even with mocked `server_manager`, signals may not fire
- `loop.exec()` creates nested event loop that blocks test execution

**Affected Tests**:
- `test_cwd_switch.py::test_switch_cwd_server_stopped` (HANGS)
- `test_cwd_switch.py::test_switch_cwd_server_running` (HANGS)

**Solution**:
- Mock `_wait_for_server_stop` and `_wait_for_server_start` to return immediately
- Or refactor to use non-blocking async patterns
- Add `@pytest.mark.timeout(5)` to all integration tests

---

### 2. Modal Dialog Blocking

**Location**: Multiple test files

**Problem**:
```python
# In switch_cwd():
QMessageBox.information(self, "Success", "...")  # ← BLOCKS until user clicks OK

# In test:
with patch.object(QMessageBox, 'information') as mock_info:
    main_window.switch_cwd(tmpdir)  # Still hangs!
```

**Why Mocking Fails**:
- `patch.object` may not intercept the call if QMessageBox is imported differently
- Modal dialogs require event loop processing
- Test fixture may not properly set up the mock before MainWindow initialization

**Affected Tests**:
- All tests in `test_cwd_switch.py`
- Tests in `test_gui_command_display.py` using QMessageBox

**Solution**:
- Use `monkeypatch` fixture instead of `patch.object`
- Mock at import time: `patch('docx_server_launcher.gui.main_window.QMessageBox')`
- Add `QMessageBox.exec = MagicMock(return_value=QMessageBox.StandardButton.Ok)`

---

### 3. Repeated MainWindow Creation

**Location**: All GUI integration tests

**Problem**:
```python
# test_cli_launch_integration.py
def test_cli_launcher_initialized_in_main_window(self, qapp):
    window = MainWindow()  # ← Creates full GUI
    try:
        assert hasattr(window, "cli_launcher")
    finally:
        window.close()

def test_settings_persistence_integration(self, qapp, tmp_path):
    window1 = MainWindow()  # ← Another full GUI
    # ...
    window2 = MainWindow()  # ← Yet another full GUI
```

**Impact**:
- Each MainWindow creation initializes:
  - QSettings (file I/O)
  - ServerManager (process management)
  - CLILauncher (subprocess checks)
  - All GUI widgets (memory allocation)
  - Signal/slot connections
- Typical overhead: 200-500ms per window
- 40 tests × 2-3 windows each = 80-120 window creations

**Solution**:
- Use module-scoped fixtures for shared MainWindow
- Create lightweight test doubles for components
- Use `@pytest.fixture(scope="module")` for expensive setup

---

### 4. Incomplete Mocking

**Location**: `test_cwd_switch.py`

**Problem**:
```python
@pytest.fixture
def main_window(qtbot):
    with patch('PyQt6.QtCore.QSettings') as MockSettings:
        # Only mocks QSettings, but MainWindow also uses:
        # - ServerManager (not mocked)
        # - CWDManager (not mocked)
        # - CLILauncher (not mocked)
        window = MainWindow()
```

**Impact**:
- Real ServerManager tries to manage actual processes
- Real CWDManager performs file system operations
- Real CLILauncher checks for `claude` binary
- Signals from unmocked components may not fire correctly

**Solution**:
- Mock all external dependencies in fixture
- Use dependency injection for testability
- Create `MainWindowTestDouble` with mocked components

---

## Performance Metrics

### Current State (Estimated)
```
Total integration tests: 40
Hanging tests: ~5-10 (25%)
Average test time: 2-5 seconds (when not hanging)
Total time: TIMEOUT (>120 seconds)
```

### Expected After Fixes
```
Total integration tests: 40
Hanging tests: 0
Average test time: 0.1-0.5 seconds
Total time: 5-20 seconds
```

---

## Recommended Fixes (Priority Order)

### Priority 1: Fix Hanging Tests (IMMEDIATE)

1. **Add timeout decorator to all integration tests**
   ```python
   @pytest.mark.timeout(5)
   def test_switch_cwd_server_stopped(main_window, qtbot):
       ...
   ```

2. **Mock wait methods in test fixtures**
   ```python
   @pytest.fixture
   def main_window(qtbot):
       window = MainWindow()
       window._wait_for_server_stop = MagicMock(return_value=True)
       window._wait_for_server_start = MagicMock(return_value=True)
       yield window
   ```

3. **Fix QMessageBox mocking**
   ```python
   @pytest.fixture(autouse=True)
   def mock_message_boxes(monkeypatch):
       monkeypatch.setattr('PyQt6.QtWidgets.QMessageBox.information', MagicMock())
       monkeypatch.setattr('PyQt6.QtWidgets.QMessageBox.critical', MagicMock())
       monkeypatch.setattr('PyQt6.QtWidgets.QMessageBox.warning', MagicMock())
   ```

### Priority 2: Optimize Fixtures (SHORT TERM)

1. **Create module-scoped QApplication**
   ```python
   @pytest.fixture(scope="module")
   def qapp():
       app = QApplication.instance() or QApplication([])
       yield app
       # Don't quit - let pytest-qt handle it
   ```

2. **Create reusable MainWindow fixture with full mocking**
   ```python
   @pytest.fixture
   def mocked_main_window(qtbot, monkeypatch):
       # Mock all external dependencies
       monkeypatch.setattr('docx_server_launcher.gui.main_window.QSettings', MagicMock())
       monkeypatch.setattr('docx_server_launcher.gui.main_window.ServerManager', MagicMock())

       window = MainWindow()
       window._wait_for_server_stop = MagicMock(return_value=True)
       window._wait_for_server_start = MagicMock(return_value=True)

       qtbot.addWidget(window)
       yield window
       window.close()
   ```

3. **Add conftest.py with shared fixtures**
   - Create `tests/integration/conftest.py`
   - Define common fixtures once
   - Reduce code duplication

### Priority 3: Architectural Improvements (LONG TERM)

1. **Refactor MainWindow for testability**
   - Extract business logic from GUI code
   - Use dependency injection for managers
   - Create interfaces for mockable components

2. **Split integration tests into categories**
   - Fast tests (< 1 second): Unit-like integration tests
   - Slow tests (> 1 second): Full GUI integration tests
   - Mark with `@pytest.mark.slow` and run separately

3. **Consider test doubles**
   - Create `MainWindowTestDouble` class
   - Lightweight version for testing
   - Only initialize components needed for specific test

---

## Immediate Action Items

### Step 1: Add Global Timeout (5 minutes)
```bash
# In pyproject.toml or pytest.ini
[tool.pytest.ini_options]
timeout = 10  # 10 seconds per test
```

### Step 2: Fix Hanging Tests (30 minutes)
- Add mocks for `_wait_for_server_*` methods
- Fix QMessageBox mocking in `test_cwd_switch.py`
- Verify tests pass with timeout

### Step 3: Create Shared Fixtures (1 hour)
- Create `tests/integration/conftest.py`
- Move common fixtures
- Update tests to use shared fixtures

### Step 4: Measure Improvement (10 minutes)
```bash
time uv run pytest tests/integration/ -v --durations=10
```

---

## Test-Specific Issues

### test_cwd_switch.py
- **Issue**: `switch_cwd()` calls blocking methods
- **Fix**: Mock `_wait_for_server_stop/start` in fixture
- **Estimated speedup**: From TIMEOUT to 0.5s per test

### test_cli_launch_integration.py
- **Issue**: Creates 3+ MainWindow instances
- **Fix**: Use module-scoped fixture
- **Estimated speedup**: From 5s to 1s total

### test_launcher_logging.py
- **Issue**: Creates 2 MainWindow instances per test
- **Fix**: Reuse window fixture
- **Estimated speedup**: From 3s to 0.5s per test

### test_gui_command_display.py
- **Issue**: Complex fixture setup per test
- **Fix**: Use autouse fixture for common mocks
- **Estimated speedup**: From 2s to 0.3s per test

---

## Conclusion

The integration tests are slow primarily due to:
1. **Blocking event loops** (causing hangs)
2. **Unmocked modal dialogs** (causing hangs)
3. **Repeated expensive object creation** (causing slowness)
4. **Incomplete mocking** (causing unpredictable behavior)

Implementing the Priority 1 fixes will immediately resolve the hanging issues. Priority 2 and 3 fixes will improve overall test suite performance by 10-20x.

**Estimated total fix time**: 2-3 hours
**Expected result**: All tests pass in < 20 seconds
