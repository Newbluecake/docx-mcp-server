import pytest
import tempfile
import os
from pathlib import Path
from PyQt6.QtCore import QSettings
from docx_server_launcher.core.working_directory_manager import WorkingDirectoryManager

@pytest.fixture
def settings():
    # Use a temporary file for QSettings to avoid polluting user config
    # Format: QSettings(fileName, format)
    return QSettings("test_config.ini", QSettings.Format.IniFormat)

@pytest.fixture
def manager(settings):
    settings.clear()
    return WorkingDirectoryManager(settings)

def test_validate_directory_valid(manager):
    with tempfile.TemporaryDirectory() as tmpdir:
        is_valid, error = manager.validate_directory(tmpdir)
        assert is_valid is True
        assert error == ""

def test_validate_directory_not_exists(manager):
    # Ensure this path does not exist
    path = "/nonexistent/path/definitely/not/here"
    is_valid, error = manager.validate_directory(path)
    assert is_valid is False
    assert "not exist" in error

def test_validate_directory_empty(manager):
    is_valid, error = manager.validate_directory("")
    assert is_valid is False
    assert "empty" in error

def test_add_to_history_new(manager):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Resolve to match manager's internal normalization
        resolved_path = str(Path(tmpdir).resolve())

        manager.add_to_history(tmpdir)

        history = manager.get_history()
        assert len(history) == 1
        assert history[0] == resolved_path

def test_add_to_history_duplicate(manager):
    with tempfile.TemporaryDirectory() as tmpdir:
        resolved_path = str(Path(tmpdir).resolve())

        manager.add_to_history(tmpdir)
        manager.add_to_history(tmpdir) # Add again

        history = manager.get_history()
        assert len(history) == 1
        assert history[0] == resolved_path

def test_add_to_history_reorder(manager):
    with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:
        path1 = str(Path(tmpdir1).resolve())
        path2 = str(Path(tmpdir2).resolve())

        manager.add_to_history(path1)
        manager.add_to_history(path2)

        # Verify order: path2 (newest) first
        assert manager.get_history() == [path2, path1]

        # Add path1 again
        manager.add_to_history(path1)

        # Verify order: path1 moved to top
        assert manager.get_history() == [path1, path2]

def test_add_to_history_max_limit(manager):
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir).resolve()

        # Add 12 different directories
        for i in range(12):
            subdir = base_path / f"dir{i}"
            subdir.mkdir()
            manager.add_to_history(str(subdir))

        history = manager.get_history()
        assert len(history) == 10
        # The last added (dir11) should be first
        # Use resolved path for comparison to handle Windows short paths
        expected_dir11 = str((base_path / "dir11").resolve())
        assert expected_dir11 == history[0]

        # The first added (dir0, dir1) should be gone
        # Check strict equality of paths, not substrings
        dir0 = str((base_path / "dir0").resolve())
        dir1 = str((base_path / "dir1").resolve())

        assert dir0 not in history
        assert dir1 not in history

def test_save_load_settings(settings):
    settings.clear() # Ensure clean state
    # Create a manager, add history
    manager1 = WorkingDirectoryManager(settings)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = str(Path(tmpdir).resolve())
        manager1.add_to_history(path)

    # Create a new manager using same settings
    manager2 = WorkingDirectoryManager(settings)
    assert manager2.get_history() == [path]
