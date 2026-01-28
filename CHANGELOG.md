# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-01-28

### 💥 Breaking Changes

- **session**: Removed `file_path` parameter from `docx_create()` - files are now managed globally via Launcher GUI or `--file` CLI parameter
- **session**: Removed `docx_list_files()` tool - file browsing is now handled by Launcher GUI
- **session**: Removed `session_id` parameter from all MCP tools - sessions are now managed automatically via global state

### ✨ Features

#### Session Management (v4.0)
- **Auto-session creation**: Sessions are automatically created when switching files via API
- **Global state management**: Simplified session handling with automatic session tracking
- **Session helper utilities**: New `setup_active_session()` and `teardown_active_session()` for testing

#### Launcher & Server
- **Dual-port architecture**: Separate HTTP (file management) and MCP (tools) services
- **FastMCP integration**: Migrated to FastMCP custom routes for better HTTP endpoint handling
- **Health check system**: Automatic server health monitoring on startup
- **Status polling**: Real-time server status updates in GUI
- **File selection UI**: Enhanced file browser with recent files and working directory management
- **HTTP client with retry**: Robust HTTP communication with automatic retry mechanism

#### API & Tools
- **REST API endpoints**: New `/api/file/switch`, `/api/file/status`, `/api/session/close` endpoints
- **Combined transport mode**: Support for `--transport combined` with both HTTP and MCP
- **File parameter**: New `--file` CLI parameter for specifying active document on startup
- **Optimized tool docstrings**: Improved descriptions for better Claude AI understanding

### 🐛 Bug Fixes

#### Test Infrastructure
- Fixed all test failures related to v4.0 session simplification
- Resolved Qt crash in headless CI environment
- Fixed Windows path issues in CLI launcher tests
- Resolved test hanging issues with proper QEventLoop handling
- Fixed global state isolation in E2E tests

#### Core Fixes
- **GlobalState deadlock**: Switched to RLock to prevent deadlock in atomic context operations
- **GUI freeze**: Prevented launcher freeze during server startup with proper threading
- **Dynamic offset detection**: Fixed content pagination test CI failures

### ♻️ Refactoring

- **Modular tool structure**: Split monolithic server.py into domain-specific tool modules
- **Unified logging patterns**: Standardized logging and context updates across all MCP tools
- **Shared logic extraction**: Centralized scope resolution and metadata generation
- **Position requirement**: All insert tools now require explicit `position` parameter

### 📚 Documentation

- **Migration guide**: Comprehensive v2.x → v3.0 → v4.0 migration documentation
- **Technical design docs**: Detailed architecture and task breakdown for session simplification
- **MCP tools guide**: Complete usage guide for all 50+ MCP tools
- **CLAUDE.md updates**: Updated development guide for v4.0 breaking changes
- **README updates**: Refreshed API reference and examples

### ✅ Tests

- **100% test coverage**: All 488 unit tests passing
- **Integration tests**: 37 E2E tests updated for v4.0
- **Test helpers**: New Markdown response extractors for test assertions
- **CI stability**: Resolved all platform-specific test failures (Windows/macOS/Linux)

### 🔧 Technical Details

- **Python 3.12**: Simplified CI matrix to Python 3.12 only
- **uv migration**: All build scripts now use uv for faster dependency resolution
- **GUI test isolation**: Proper Qt environment setup for headless CI
- **Deprecation fixes**: Replaced `datetime.utcnow()` with `datetime.now(timezone.utc)`

**Statistics**: 286 commits since v0.1.3
- Features: 98 | Bug Fixes: 66 | Documentation: 63 | Tests: 17 | Refactoring: 9 | Chores: 12

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
