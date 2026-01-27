# MCP Tool Docstring Guidelines

## Purpose

These guidelines ensure all MCP tool docstrings are optimized for Claude AI to understand:
- How to call the tools correctly
- How the model perceives which Word document is being edited
- The active file concept and session management
- Complete workflows from start to finish

## Standard Docstring Template

```python
def docx_tool_name(session_id: str, param1: str, param2: int = 0) -> str:
    """
    [One-line summary of what the tool does]

    [2-3 sentences explaining the tool's purpose and behavior in detail]

    **Session Context**: This tool operates on the document associated with
    session_id. Create a session first using docx_create(), which uses the
    global active file set by the Launcher GUI or --file parameter.

    Typical Use Cases:
        - [Use case 1]
        - [Use case 2]
        - [Use case 3]

    Args:
        session_id (str): Active session ID returned by docx_create().
            The session maintains document state and object registry.
        param1 (str): [Description with constraints/format if applicable]
        param2 (int, optional): [Description]. Defaults to 0.

    Returns:
        str: Markdown-formatted response with operation status, element_id
            (if applicable), and visual document context.

    Raises:
        SessionNotFound: If session_id is invalid or session has expired.
        [OtherError]: [When this error occurs]

    Examples:
        Basic usage:
        >>> # Step 1: Create session for active file
        >>> session_id = docx_create()
        >>> # Step 2: Use the tool
        >>> result = docx_tool_name(session_id, "value")
        >>> # Step 3: Extract element_id if needed
        >>> import re
        >>> match = re.search(r'\*\*Element ID\*\*:\s*(\w+)', result)
        >>> element_id = match.group(1) if match else None

        Complete workflow:
        >>> # Set active file via Launcher or --file parameter
        >>> session_id = docx_create()
        >>> result = docx_tool_name(session_id, "value")
        >>> docx_save(session_id, "./output.docx")
        >>> docx_close(session_id)

    Notes:
        - [Important behavior note 1]
        - [Important behavior note 2]
        - [Performance consideration if applicable]

    See Also:
        - docx_create: Create session for active file
        - docx_related_tool: [Why it's related]
        - /api/file/switch: HTTP API to change active file
    """
```

## Key Sections Explained

### 1. One-Line Summary
- Start with action verb (Add, Create, Update, Delete, Get, etc.)
- Be specific about what element is affected
- Keep under 80 characters

**Good**: "Add a new paragraph to the document with precise positioning"
**Bad**: "Paragraph insertion tool"

### 2. Detailed Description
- Explain what the tool does in 2-3 sentences
- Mention key capabilities (positioning, formatting, etc.)
- Highlight any special behavior

### 3. Session Context Block ⭐ NEW
**Always include this for tools that require session_id**:

```
**Session Context**: This tool operates on the document associated with
session_id. Create a session first using docx_create(), which uses the
global active file set by the Launcher GUI or --file parameter.
```

This helps Claude understand:
- The tool needs a session_id
- Where to get the session_id (docx_create)
- How the active file is managed (Launcher/--file)

### 4. Typical Use Cases
- List 3-5 concrete scenarios
- Use action-oriented language
- Help Claude choose the right tool

### 5. Args Section
- Always describe session_id with standard text
- Include type, constraints, defaults
- Mention format requirements (e.g., "Format: 'mode:target_id'")

**Standard session_id description**:
```
session_id (str): Active session ID returned by docx_create().
    The session maintains document state and object registry.
```

### 6. Returns Section
- Specify Markdown format (not JSON anymore in v2.0+)
- Mention key fields in response (element_id, status, context)
- Explain what the response contains

### 7. Raises Section
- Use specific error types (SessionNotFound, ValidationError, etc.)
- Explain when each error occurs
- Help Claude handle errors appropriately

### 8. Examples Section ⭐ CRITICAL
**Must include**:
1. **Basic usage**: Single tool call with minimal context
2. **Complete workflow**: Full sequence from docx_create() to docx_close()
3. **Element ID extraction**: Show how to parse Markdown response

**Template**:
```python
Examples:
    Basic usage:
    >>> # Step 1: Create session for active file
    >>> session_id = docx_create()
    >>> # Step 2: Use the tool
    >>> result = docx_tool_name(session_id, "value")

    Complete workflow:
    >>> # Set active file via Launcher or --file parameter
    >>> session_id = docx_create()
    >>> result = docx_tool_name(session_id, "value")
    >>> docx_save(session_id, "./output.docx")
    >>> docx_close(session_id)

    Extract element_id from response:
    >>> result = docx_tool_name(session_id, "value")
    >>> import re
    >>> match = re.search(r'\*\*Element ID\*\*:\s*(\w+)', result)
    >>> element_id = match.group(1) if match else None
```

### 9. Notes Section
- Important behaviors Claude should know
- Performance considerations
- Limitations or constraints
- Best practices

### 10. See Also Section
- Link to related tools
- Always include docx_create for tools requiring session_id
- Include HTTP API endpoints if relevant
- Explain why each tool is related

## Special Cases

### Tools Without session_id
For tools like `docx_list_files()` that don't need a session:

```python
def docx_list_files(directory: str = ".") -> str:
    """
    List all .docx files in the specified directory.

    Scans the directory for Word documents without requiring an active session.
    Useful for discovering available files before creating a session.

    **No Session Required**: This tool operates independently and does not
    need a session_id. Use it to find files before calling docx_create().

    [Rest of docstring...]
    ```

### Tools That Create Elements
For tools that return element_id (insert, create operations):

```python
Returns:
    str: Markdown-formatted response containing:
        - **Element ID**: Unique identifier for the created element (e.g., "para_abc123")
        - **Status**: Success/Error indicator
        - **Document Context**: ASCII visualization showing element position
        - **Cursor**: Current cursor position after operation
```

### Tools That Modify Elements
For tools that update existing elements:

```python
Args:
    element_id (str): ID of the element to modify. Obtain from:
        - Previous tool response (e.g., docx_insert_paragraph)
        - docx_find_paragraphs search results
        - Special IDs: "last_insert", "last_update", "cursor"
```

## Migration Notes (v2.x → v3.0)

For tools affected by the active file change, include:

```python
**Breaking Change (v3.0)**: The file_path parameter has been removed.
Files are now managed centrally by the Launcher via HTTP API (/api/file/switch).

Migration from v2.x:
    Old (v2.x):
    >>> session_id = docx_create(file_path="./template.docx")

    New (v3.0):
    1. Use Launcher to select file (calls /api/file/switch)
    2. Then create session:
    >>> session_id = docx_create()
```

## Checklist for Each Tool

- [ ] One-line summary is clear and action-oriented
- [ ] Detailed description explains behavior
- [ ] **Session Context** block included (if session_id required)
- [ ] Typical use cases listed (3-5 items)
- [ ] Args section has standard session_id description
- [ ] Returns section mentions Markdown format
- [ ] Raises section lists specific error types
- [ ] Examples include:
  - [ ] Basic usage
  - [ ] Complete workflow
  - [ ] Element ID extraction (if applicable)
- [ ] Notes section covers important behaviors
- [ ] See Also section links related tools
- [ ] Migration notes included (if breaking change)

## Priority Order for Updates

1. **High Priority** (Core workflow tools):
   - session_tools.py (mostly done)
   - paragraph_tools.py
   - content_tools.py
   - table_tools.py

2. **Medium Priority** (Frequently used):
   - run_tools.py
   - format_tools.py
   - composite_tools.py

3. **Low Priority** (Advanced/specialized):
   - cursor_tools.py
   - copy_tools.py
   - advanced_tools.py
   - history_tools.py
   - system_tools.py
   - table_rowcol_tools.py
