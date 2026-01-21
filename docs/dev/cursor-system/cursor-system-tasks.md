# Task Breakdown: Cursor System

## Phase 1: Core Implementation

### Group 1: Core Logic
- [ ] **Task 1.1**: Create `Cursor` class in `src/docx_mcp_server/core/cursor.py`.
    - Define data structure (parent_id, element_id, position).
    - Implement validation logic.
- [ ] **Task 1.2**: Update `Session` class in `src/docx_mcp_server/core/session.py`.
    - Add `self.cursor` field.
    - Initialize cursor on session creation (default to end of document).

### Group 2: Navigation Tools
- [ ] **Task 2.1**: Implement `docx_cursor_move` and `docx_cursor_get` in `src/docx_mcp_server/tools/cursor_tools.py`.
    - Support "before", "after", "inside" positioning.
    - Register tools in `server.py`.

## Phase 2: Insertion Implementation

### Group 3: Insertion Tools
- [ ] **Task 3.1**: Implement `docx_insert_paragraph` using cursor.
    - Handle `insert_paragraph_before` logic.
    - Handle `xml` insertion for "after" logic (using `addnext` if needed).
- [ ] **Task 3.2**: Implement `docx_insert_table` using cursor.
    - Allow inserting tables at specific cursor positions.

## Phase 3: Integration & Verification

### Group 4: Testing
- [ ] **Task 4.1**: Create E2E test `tests/e2e/test_cursor_workflow.py`.
    - Scenario: Create doc, add paras, move cursor back, insert middle para, verify order.
