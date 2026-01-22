---
feature: load-existing-file
version: 1
status: draft
generated_at: 2026-01-20
---

# Technical Design: Load Existing File

> **Feature**: load-existing-file
> **Related Requirements**: docs/dev/load-existing-file/load-existing-file-requirements.md

## 1. Architecture Overview

To support loading and editing existing `.docx` files, we will leverage the existing `SessionManager` capabilities which already support initializing a `Document` with a file path. The main work involves exposing this capability through the MCP API and adding tools to inspect the loaded content (read and search), as objects in existing files are not automatically registered in our ID system.

### 1.1 Core Components

- **Server Interface (`server.py`)**:
    - Update `docx_create` to accept `file_path`.
    - Add `docx_read_content` for document overview.
    - Add `docx_find_paragraphs` for targeting specific content.
- **Session Core (`session.py`)**:
    - No major changes needed in `Session` class structure, but usage pattern changes (lazy registration).

## 2. API Design

### 2.1 Update `docx_create`

Current signature:
```python
def docx_create() -> str
```

New signature:
```python
def docx_create(file_path: str = None) -> str
```

**Behavior**:
- If `file_path` is provided, verify it exists.
- Pass `file_path` to `session_manager.create_session`.
- Return `session_id`.

### 2.2 New Tool: `docx_read_content`

Signature:
```python
def docx_read_content(session_id: str) -> str
```

**Behavior**:
- Iterate through `document.paragraphs`.
- Compile a readable summary of the document (e.g., text content).
- **Format**: Return a JSON-formatted string or structured text containing a list of paragraphs to provide a quick overview. To avoid cluttering the registry, this tool might **not** register objects by default, or only register top-level structures if requested.
- **Decision**: To keep it simple and safe for large documents, this tool will return **Plain Text** of the document content, similar to reading a file. It serves as "read-only" inspection.

### 2.3 New Tool: `docx_find_paragraphs`

Signature:
```python
def docx_find_paragraphs(session_id: str, query: str) -> str
```

**Behavior**:
- Iterate through `document.paragraphs`.
- Check if `query` string exists in `paragraph.text` (case-insensitive option?).
- For matches:
    - Call `session.register_object(paragraph, "para")` to generate an ID.
    - Collect `{ "id": "para_...", "text": "..." }`.
- Return a JSON list of matches.

## 3. Implementation Details

### 3.1 Lazy Registration Strategy

The `python-docx` library loads the entire document structure into memory. Our `Session` object holds this `Document`.
- **Creation**: We do NOT traverse and register all paragraphs at startup.
- **On Demand**: When `docx_find_paragraphs` finds a match, we register *that specific paragraph instance* in `session.object_registry`.
- **Consistency**: The `python-docx` objects are mutable and persistent in memory for the life of the `Document` object. Registering them is safe.

### 3.2 Security & Error Handling

- **File Path**: Validate that `file_path` exists before attempting to open.
- **File Type**: Ensure it is a valid `.docx` file (handled by `python-docx` exception).
- **Empty Search**: Return empty list `[]` if no matches found.

## 4. Data Flow

```
User (Claude) -> docx_create("/path/to/doc.docx")
              -> Server checks file -> SessionManager -> Document(path) -> Session
              -> Returns session_id

User (Claude) -> docx_find_paragraphs(sid, "Introduction")
              -> Server iterates doc.paragraphs
              -> Found match -> session.register_object(para) -> "para_123"
              -> Returns [{"id": "para_123", "text": "1. Introduction..."}]

User (Claude) -> docx_insert_run(sid, " (Updated)", position="inside:para_123")
              -> Server looks up "para_123" -> gets Paragraph object
              -> calls para.add_run(...)
```

## 5. Verification Plan

- **Unit Tests**:
    - Test `docx_create` with valid/invalid paths.
    - Test `docx_read_content` returns text.
    - Test `docx_find_paragraphs` registers objects correctly (verify with `session.get_object`).
- **E2E Tests**:
    - Create a sample docx, save it.
    - Load it back.
    - Find a paragraph, modify it.
    - Save and verify modification.
