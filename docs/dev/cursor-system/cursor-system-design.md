# Technical Design: Cursor System

## 1. Executive Summary

The **Cursor System** introduces a persistent, navigable insertion point within the document session. This allows Claude to edit documents more naturally (e.g., "insert a paragraph *after* the second table") without needing to manually track parent IDs or index positions. It moves beyond the current "append-only" or "last-accessed" implicit context.

## 2. Problem Statement

Current limitations:
- **Append-Bias**: Most `add_*` tools default to appending to the end of the document or parent container.
- **Insertion Difficulty**: Inserting content *between* existing elements requires complex XML manipulation or specific knowledge of the `insert_paragraph_before` API which isn't exposed uniformly.
- **Context Loss**: The simple `last_accessed_id` mechanism is fragile and doesn't support "traversal" (moving up/down/next/prev).

## 3. Architecture Design

### 3.1. Core Components

#### `Cursor` Class (`src/docx_mcp_server/core/cursor.py`)
A new state object attached to the `Session`.

```python
@dataclass
class Cursor:
    parent_id: str          # The container (Document, Cell, etc.)
    current_id: Optional[str] # The element the cursor is currently "on" or "after"
    position: str           # "before", "after", "inside_start", "inside_end"
    index: int              # Optional numerical index for list-based access
```

#### `Session` Update (`src/docx_mcp_server/core/session.py`)
Extend `Session` to hold a `Cursor` instance.

```python
class Session:
    # ... existing fields
    cursor: Cursor = field(default_factory=Cursor)
```

### 3.2. Data Flow

1. **Move Cursor**: User calls `docx_cursor_move(target_id, position)`.
2. **Update State**: Session updates `cursor` object.
3. **Insert Content**: User calls `docx_insert_paragraph("text")` (new tool).
4. **Resolution**: Tool checks `cursor`.
   - If `position="after"`, finds `target_id`'s element and calls `addnext()`.
   - If `position="before"`, calls `addprevious()` or `insert_paragraph_before()`.

### 3.3. New Tools (`src/docx_mcp_server/tools/cursor_tools.py`)

- `docx_cursor_get()`: Returns current cursor location.
- `docx_cursor_move(element_id, position)`: Moves cursor relative to an element.
- `docx_cursor_select(element_id)`: Selects an element (equivalent to "inside_end").
- `docx_insert_paragraph_at_cursor(text, style)`: Inserts paragraph at cursor.
- `docx_insert_table_at_cursor(rows, cols)`: Inserts table at cursor.

## 4. Implementation Details

### 4.1. `python-docx` Integration

Since `python-docx` doesn't natively support arbitrary insertion well (mostly "append" or "insert_paragraph_before"), we will need to utilize `lxml` manipulation for advanced placement if the native API falls short.

- **Paragraphs**: `paragraph.insert_paragraph_before()` is standard.
- **Tables**: `table.add_row()` appends. Inserting a table *between* paragraphs requires access to the parent `_body` element and `addnext`/`insert` on the XML element.

### 4.2. Backward Compatibility

Existing tools (`docx_add_paragraph`, `docx_add_table`) will continue to function as "append" operations. The new cursor-based insertion will be handled by specific `docx_insert_*` tools or by adding a `use_cursor=True` flag to existing tools (preferred: new specific tools to keep "add" vs "insert" semantics clear).

For this iteration, we will implement **new tools** for cursor-based insertion to avoid breaking changes.

## 5. Security & Safety

- **Validation**: Ensure cursor cannot point to deleted objects.
- **Scope**: Cursor must stay within the `session` boundaries.

## 6. Testing Strategy

- **Unit Tests**: Test `Cursor` state transitions.
- **Integration Tests**: Move cursor -> Insert -> Save -> Verify position in XML/Docx.
