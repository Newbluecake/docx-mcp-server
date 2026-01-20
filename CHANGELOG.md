# Changelog

All notable changes to this project will be documented in this file.

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
