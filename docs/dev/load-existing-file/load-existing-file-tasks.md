---
feature: load-existing-file
version: 1
status: pending
generated_at: 2026-01-20
---

# Tasks: Load Existing File

> **Feature**: load-existing-file
> **Based on**: docs/dev/load-existing-file/load-existing-file-design.md

## Execution Plan

The implementation is divided into 2 groups:
1. **Core Loading**: Update creation and read tools.
2. **Search & Interaction**: Implement search functionality.

---

## Group 1: Core Loading & Reading

### T-001: Update `docx_create` to support file path
- **Goal**: Allow initializing session from existing file.
- **Files**: `src/docx_mcp_server/server.py`
- **Steps**:
  - Modify `docx_create` signature to accept optional `file_path`.
  - Add validation (check if file exists).
  - Pass path to `session_manager`.
- **Verification**: Unit test checking session creation with valid file path.

### T-002: Implement `docx_read_content`
- **Goal**: Provide text overview of the document.
- **Files**: `src/docx_mcp_server/server.py`
- **Steps**:
  - Add new tool `docx_read_content`.
  - Implement logic to iterate paragraphs and join text.
  - Return plain text content.
- **Verification**: Unit test loading a known file and checking returned text.

---

## Group 2: Search & Interaction

### T-003: Implement `docx_find_paragraphs`
- **Goal**: Locate paragraphs and get IDs for editing.
- **Files**: `src/docx_mcp_server/server.py`
- **Steps**:
  - Add new tool `docx_find_paragraphs(session_id, query)`.
  - Iterate paragraphs.
  - If text contains query (case-insensitive), register object in session.
  - Return list of `{element_id, text}`.
- **Verification**: Unit test finding a specific paragraph and verifying the returned ID can be used with `docx_insert_run` (position-based).

### T-004: E2E Verification
- **Goal**: Verify the full workflow.
- **Files**: `tests/e2e/test_load_edit.py` (new)
- **Steps**:
  - Create a script that:
    1. Creates a doc.
    2. Loads it back.
    3. Finds text.
    4. Edits it.
    5. Saves.
    6. Verifies changes.
