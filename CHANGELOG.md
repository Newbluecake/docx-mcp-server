# Changelog

All notable changes to this project will be documented in this file.

## [0.1.3] - 2026-01-21

### ✨ Features

- **LAN Access Support**: Enhanced GUI Launcher with a simplified "Allow LAN Access" checkbox.
  - When checked, the server listens on `0.0.0.0` to allow external connections.
  - When unchecked (default), it listens on `127.0.0.1` for security.
- **Improved GUI**: Replaced complex Host/Port inputs with a more user-friendly interface.
- **CLI Enhancements**: Updated `server.py` to support explicit SSE transport configuration via command-line arguments (`--transport`, `--host`, `--port`).

### 🐛 Fixes

- Fixed `NameError: name 'QCheckBox' is not defined` runtime error in the launcher.
- Persisted network settings in GUI correctly across restarts.

## [0.1.2] - 2026-01-21

### 🐛 Fixes

- Fixed `ModuleNotFoundError` in Windows packaged build by implementing a "dual-mode" launcher. The executable now supports a `--server-mode` flag to run the MCP server directly from within the frozen environment, eliminating dependency on external Python installations.

### 👷 CI/CD

- Migrated CI workflows to use [uv](https://github.com/astral-sh/uv) for faster dependency resolution and testing.

## [0.1.1] - 2026-01-21

### 🐛 Fixes

- Fixed critical bug in Windows Launcher where clicking "Start Server" would recursively spawn new GUI windows instead of the server process.

### 👷 CI/CD

- Added comprehensive GitHub Actions workflow (`ci.yml`) for cross-platform testing (Windows, macOS, Ubuntu) and Python version matrix.

## [0.1.0] - 2026-01-20

### ✨ Features

- **GUI Launcher**: Added `DocxServerLauncher` (Windows GUI) for easy server management without command-line usage.
- **Advanced Document Operations**:
  - Deep table copying (`docx_copy_table`) with XML deep cloning.
  - Smart text replacement (`docx_replace_text`) supporting placeholders across multiple runs.
  - Batch table filling (`docx_fill_table`) for automated reporting.
  - Image insertion support (`docx_insert_image`).
- **Hybrid Context Architecture**:
  - Implemented stateful session tracking (`last_created_id`, `last_accessed_id`).
  - Enabled concise MCP tool calls by inferring context (e.g., `docx_set_font` without explicit ID).
- **Unified Properties Engine**: New `docx_set_properties` tool for setting complex formatting via JSON.
- **Compatibility**: Added shim layer to support legacy `docx_add_run` argument signatures.

### 🐛 Fixes

- Resolved `ValueError` in `docx_add_run` by detecting and swapping argument order for backward compatibility.
- Fixed table cell expansion logic in batch filling operations.

### 👷 CI/CD

- Added GitHub Actions workflow (`build-windows-exe.yml`) for automated Windows executable creation.
- Configured automated release generation on tag push.

### 📚 Documentation

- Created comprehensive `CLAUDE.md` development guide.
- Updated `README.md` with complete API reference, examples, and installation guide.
- Added usage templates in `.claude/prompts/`.
