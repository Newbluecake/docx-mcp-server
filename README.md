# docx-mcp-server

A Model Context Protocol (MCP) server that provides a granular API for creating and editing Microsoft Word (.docx) documents.

## Features

- **Session Management**: Maintain stateful document editing sessions.
- **Atomic Operations**: Granular control over paragraphs, runs, headings, and tables.
- **Formatting**: Set fonts (bold, italic, size, color) and alignment.
- **Layout**: Control margins and page breaks.
- **Tables**: Create tables and populate cells.

## Installation

```bash
pip install .
```

## Usage

### Running the Server

```bash
mcp-server-docx
```

### Tools Available

- `docx_create()`: Start a new document.
- `docx_add_paragraph(session_id, text)`: Add text.
- `docx_add_heading(session_id, text, level)`: Add headings.
- `docx_add_table(session_id, rows, cols)`: Create tables.
- `docx_save(session_id, file_path)`: Save result.
- ... and more.

## Development

```bash
# Install dependencies
pip install -e .

# Run tests
python -m unittest discover tests
```
