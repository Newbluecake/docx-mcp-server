# Changelog

All notable changes to this project will be documented in this file.

## [0.2.1] - 2026-01-24

### ✨ Features

- **Special Position IDs**: Added three special position identifiers to simplify consecutive operations.
  - `last_insert`: References the last inserted element, eliminating the need to extract and pass element IDs in consecutive insertions.
  - `last_update`: References the last updated element, useful for format copying and batch operations.
  - `cursor`: References the current cursor position, enabling cursor-based insertions.
- **Session State Management**: Enhanced session object with `last_insert_id` and `last_update_id` tracking.
- **Position Resolution**: Extended `resolve_position()` method to handle special IDs with proper initialization checks.

### 🔧 Technical Improvements

- All insertion tools (`docx_insert_*`) now automatically update `last_insert_id`.
- All update/formatting tools (`docx_update_*`, `docx_set_*`) now automatically update `last_update_id`.
- New error type `SpecialIdNotInitialized` for better error handling when special IDs are used before initialization.
- Comprehensive E2E tests covering all special ID scenarios (6 test cases).
- Updated documentation with usage examples and development guidelines.

### 📚 Documentation

- Added "Special Position IDs" section to README.md with usage examples.
- Updated CLAUDE.md with development guidelines for special IDs.
- Added new error type to error classification table.

## [0.2.0] - 2026-01-23

### ✨ Features

- **Table Row/Column Operations**: Added precise table manipulation capabilities.
  - `docx_insert_row_at()`: Insert rows at specific positions (after:N, before:N, start, end) with optional format copying.
  - `docx_insert_col_at()`: Insert columns at specific positions with optional format copying.
  - `docx_delete_row()`: Delete rows by index with automatic element_id cleanup.
  - `docx_delete_col()`: Delete columns by index with automatic element_id cleanup.
- **Format Painter Enhancements**: Extended FormatPainter with row/column/cell format copying methods.
- **Registry Cleaner**: New service for automatic cleanup of invalidated element_ids after deletions.
- **Enhanced ElementManipulator**: Added low-level XML operations for table row/column manipulation.

### 🔧 Technical Improvements

- All new tools follow standardized JSON response format with status, message, and data fields.
- Comprehensive error handling with specific error types (ValidationError, IndexError, ElementNotFound).
- Boundary protection: prevents deletion of last row/column to maintain table integrity.
- Deep copy of cell XML structure ensures proper namespace preservation during column insertion.
- 25 comprehensive unit tests covering all scenarios and edge cases.

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
- **Compatibility**: Insert tools now use `docx_insert_*` naming and require `position` for placement.

### 🐛 Fixes

- Resolved `ValueError` in `docx_insert_run` by validating position targets.
- Fixed table cell expansion logic in batch filling operations.

### 👷 CI/CD

- Added GitHub Actions workflow (`build-windows-exe.yml`) for automated Windows executable creation.
- Configured automated release generation on tag push.

### 📚 Documentation

- Created comprehensive `CLAUDE.md` development guide.
- Updated `README.md` with complete API reference, examples, and installation guide.
- Added usage templates in `.claude/prompts/`.
