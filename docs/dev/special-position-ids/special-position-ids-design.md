---
feature: special-position-ids
complexity: standard
version: 1
created_at: 2026-01-24T10:45:00Z
---

# 技术设计文档: Special Position IDs

> **功能标识**: special-position-ids
> **复杂度**: standard
> **设计版本**: 1

## 1. 概述

### 1.1 设计目标

为 docx-mcp-server 添加特殊位置 ID（`last_insert`、`last_update`、`cursor`/`current`）支持，使 Agent 能够使用语义化标识符代替具体的 element_id，简化代码并减少错误。

### 1.2 核心设计原则

1. **透明解析**: 特殊 ID 在底层自动解析为具体 element_id，对上层工具透明
2. **向后兼容**: 现有使用具体 element_id 的代码继续工作
3. **明确错误**: 无法解析时返回清晰的错误信息，不做隐式 fallback
4. **O(1) 性能**: 特殊 ID 解析为直接属性查找，无性能损失

---

## 2. 系统架构设计

### 2.1 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                        MCP Tools Layer                       │
│  (paragraph_tools, run_tools, table_tools, etc.)            │
└──────────────────────┬──────────────────────────────────────┘
                       │ element_id parameter
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                    Session.get_object()                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  1. Check if element_id is special ID                 │  │
│  │  2. If yes: resolve_special_id() → concrete_id        │  │
│  │  3. If no: use element_id directly                    │  │
│  │  4. Lookup in object_registry                         │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                  Session State (Enhanced)                    │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  • last_insert_id: Optional[str]                      │  │
│  │  • last_update_id: Optional[str]                      │  │
│  │  • cursor: Cursor (already exists)                    │  │
│  │  • object_registry: Dict[str, Any]                    │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 数据流

**插入操作流程**:
```
docx_insert_paragraph(session_id, "Text", position="end:document_body")
    ↓
1. Create paragraph object
2. Register in object_registry → para_abc123
3. session.last_insert_id = "para_abc123"  ← 新增
4. session.update_context("para_abc123", action="create")
5. Return Markdown response with element_id
```

**使用特殊 ID 的操作流程**:
```
docx_insert_run(session_id, "Run", position="inside:last_insert")
    ↓
1. PositionResolver.resolve("inside:last_insert")
2. Extract target_id = "last_insert"
3. session.get_object("last_insert")
    ↓
    3.1 Detect "last_insert" is special ID
    3.2 session.resolve_special_id("last_insert") → "para_abc123"
    3.3 Lookup "para_abc123" in object_registry
    3.4 Return paragraph object
4. Continue with normal insertion logic
```

---

## 3. 组件设计

### 3.1 Session 类增强

**文件**: `src/docx_mcp_server/core/session.py`

#### 3.1.1 新增属性

```python
@dataclass
class Session:
    # ... existing fields ...

    # New fields for special ID tracking
    last_insert_id: Optional[str] = None
    last_update_id: Optional[str] = None

    # cursor already exists, no change needed
```

#### 3.1.2 新增方法

```python
def resolve_special_id(self, special_id: str) -> str:
    """
    Resolve special ID to concrete element_id.

    Args:
        special_id: One of "last_insert", "last_update", "cursor", "current", "document_body"

    Returns:
        Concrete element_id (e.g., "para_abc123") or special marker (e.g., "document_body")

    Raises:
        ValueError: If special ID cannot be resolved
    """
    special_id_lower = special_id.lower()

    if special_id_lower == "last_insert":
        if not self.last_insert_id:
            raise ValueError(
                "Special ID 'last_insert' not available: "
                "no insert operation in this session. "
                "Try using docx_insert_paragraph() or docx_insert_table() first."
            )
        return self.last_insert_id

    elif special_id_lower == "last_update":
        if not self.last_update_id:
            raise ValueError(
                "Special ID 'last_update' not available: "
                "no update operation in this session. "
                "Try using docx_update_paragraph_text() or docx_set_font() first."
            )
        return self.last_update_id

    elif special_id_lower in ("cursor", "current"):
        if not self.cursor.element_id:
            raise ValueError(
                "Special ID 'cursor' not available: "
                "cursor not initialized. "
                "Try using docx_cursor_move() first."
            )
        return self.cursor.element_id

    elif special_id_lower == "document_body":
        # Special marker for document body
        return "document_body"

    else:
        # Not a special ID, return as-is
        return special_id
```

#### 3.1.3 修改 get_object() 方法

```python
def get_object(self, obj_id: str) -> Optional[Any]:
    if not obj_id or not isinstance(obj_id, str):
        return None

    # Clean ID
    clean_id = obj_id.strip().split()[0] if obj_id.strip() else ""

    # NEW: Try to resolve special ID first
    # IMPORTANT: Only resolve if it's actually a special ID to maintain backward compatibility
    if clean_id.lower() in ("last_insert", "last_update", "cursor", "current", "document_body"):
        try:
            resolved_id = self.resolve_special_id(clean_id)
        except ValueError:
            # Special ID cannot be resolved, propagate exception
            # Caller should handle this with appropriate error response
            raise
    else:
        # Not a special ID, use as-is
        resolved_id = clean_id

    # Handle document_body special case
    if resolved_id == "document_body":
        return self.document

    return self.object_registry.get(resolved_id)
```

#### 3.1.4 修改 update_context() 方法

```python
def update_context(self, element_id: str, action: str = "access"):
    """Update context pointers based on action type."""
    self.last_accessed_id = element_id

    if action == "create":
        self.last_created_id = element_id
        self.last_insert_id = element_id  # NEW

    elif action == "update":
        self.last_update_id = element_id  # NEW

    logger.debug(f"Context updated: element_id={element_id}, action={action}")

    # ... rest of auto-save logic ...
```

#### 3.1.5 update_context() 调用规范

为确保实施时的一致性，以下是各工具应该使用的 action 参数：

| 操作类型 | action 参数 | 更新的字段 |
|---------|------------|-----------|
| `docx_insert_paragraph` | `"create"` | `last_insert_id`, `last_created_id` |
| `docx_insert_run` | `"create"` | `last_insert_id`, `last_created_id` |
| `docx_insert_table` | `"create"` | `last_insert_id`, `last_created_id` |
| `docx_insert_heading` | `"create"` | `last_insert_id`, `last_created_id` |
| `docx_update_paragraph_text` | `"update"` | `last_update_id` |
| `docx_update_run_text` | `"update"` | `last_update_id` |
| `docx_set_font` | `"update"` | `last_update_id` |
| `docx_set_alignment` | `"update"` | `last_update_id` |
| `docx_copy_paragraph` | `"create"` | `last_insert_id` (复制产生新元素) |
| `docx_copy_table` | `"create"` | `last_insert_id` (复制产生新元素) |
| `docx_format_copy` | `"update"` | `last_update_id` (修改目标元素) |

**判断原则**：
- 如果操作创建新元素 → `action="create"`
- 如果操作修改现有元素 → `action="update"`
- 如果操作只读取元素 → `action="access"` (默认)

**删除操作的特殊处理**：
`docx_delete()` 工具不应修改 `last_insert_id` 或 `last_update_id`。这些指针保持不变，即使指向的元素已被删除。

理由：
1. 保持简单性：不需要维护历史栈或回退逻辑
2. 明确的错误：后续使用会得到清晰的 "ElementNotFound" 错误
3. 符合需求：R-006 明确要求此行为

### 3.2 PositionResolver 增强

**文件**: `src/docx_mcp_server/services/navigation.py`

#### 3.2.1 修改 resolve() 方法

```python
def resolve(self, position_str: Optional[str], default_parent=None):
    """
    Parse position string and resolve to document objects.

    Now supports special IDs in target_id.
    """
    if not position_str:
        return default_parent or self.session.document, None, "append"

    parts = position_str.split(":", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid position format: '{position_str}'. Expected 'mode:id'")

    mode, target_id = parts[0].lower(), parts[1]

    if mode not in ["after", "before", "inside", "start", "end"]:
         raise ValueError(f"Invalid position mode: '{mode}'. Supported: after, before, inside, start, end")

    # NEW: Let get_object() handle special ID resolution
    # This avoids duplicate resolution logic
    try:
        target_obj = self.session.get_object(target_id)
    except ValueError as e:
        # Catch special ID resolution errors and add position context
        if "Special ID" in str(e):
            raise ValueError(f"Position resolution failed: {e}")
        raise

    if not target_obj:
        raise ValueError(f"Target element '{target_id}' not found")

    # ... rest of resolution logic unchanged ...
```

### 3.3 工具层修改

**影响的文件**: 所有 `src/docx_mcp_server/tools/*.py`

#### 3.3.1 修改策略

大多数工具已经通过 `session.get_object(element_id)` 获取对象，因此只需确保：

1. `session.get_object()` 内部调用 `resolve_special_id()`（已在 3.1.3 实现）
2. 错误处理捕获 `ValueError` 并转换为标准错误响应

#### 3.3.2 错误处理模式

```python
def docx_some_tool(session_id: str, element_id: str, ...):
    session = session_manager.get_session(session_id)
    if not session:
        return create_error_response(
            f"Session {session_id} not found",
            error_type="SessionNotFound"
        )

    try:
        # This will now handle special IDs automatically
        element = session.get_object(element_id)
        if not element:
            return create_error_response(
                f"Element '{element_id}' not found",
                error_type="ElementNotFound"
            )

        # ... perform operation ...

    except ValueError as e:
        # Catch special ID resolution errors
        if "Special ID" in str(e):
            return create_error_response(
                str(e),
                error_type="SpecialIDNotAvailable"
            )
        raise
```

#### 3.3.3 需要修改的工具

所有接受 `element_id` 参数的工具都需要添加上述错误处理。主要包括：

- `paragraph_tools.py`: `docx_update_paragraph_text`, `docx_copy_paragraph`, `docx_delete`
- `run_tools.py`: `docx_update_run_text`, `docx_set_font`
- `table_tools.py`: `docx_get_cell`, `docx_copy_table`, 行列操作
- `format_tools.py`: `docx_set_alignment`, `docx_format_copy`, `docx_set_properties`
- `advanced_tools.py`: `docx_replace_text`, `docx_insert_image`
- `copy_tools.py`: `docx_get_element_source`, `docx_copy_elements_range`

### 3.4 响应格式增强

**文件**: `src/docx_mcp_server/core/response.py`

#### 3.4.1 添加 ERROR_SUGGESTIONS 字典

```python
# 在 response.py 中添加
ERROR_SUGGESTIONS = {
    "SpecialIDNotAvailable": "Make sure you have performed the required operation before using this special ID.",
    "SessionNotFound": "The session may have expired. Create a new session with docx_create().",
    "ElementNotFound": "The element may have been deleted. Verify the element ID is correct.",
    # ... 其他错误类型 ...
}

def create_error_response(message: str, error_type: Optional[str] = None) -> str:
    """Create standardized error response in Markdown format."""
    lines = []
    lines.append("# 操作结果: Error")
    lines.append("")
    lines.append("**Status**: ❌ Error")

    if error_type:
        lines.append(f"**Error Type**: {error_type}")

    lines.append(f"**Message**: {message}")

    # 添加建议（如果有）
    if error_type and error_type in ERROR_SUGGESTIONS:
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 💡 Suggestion")
        lines.append("")
        lines.append(ERROR_SUGGESTIONS[error_type])

    return "\\n".join(lines)
```

#### 3.4.2 成功响应（无变化）

```markdown
# 操作结果: Insert Paragraph

**Status**: ✅ Success
**Element ID**: para_abc123
**Operation**: Insert Paragraph
**Position**: end:document_body

---

## 📄 Document Context
...
```

#### 3.4.3 新增错误类型示例

```markdown
# 操作结果: Error

**Status**: ❌ Error
**Error Type**: SpecialIDNotAvailable
**Message**: Special ID 'last_insert' not available: no insert operation in this session. Try using docx_insert_paragraph() or docx_insert_table() first.

---

## 💡 Suggestion

Make sure you have performed the required operation before using this special ID.
```

---

## 4. 接口设计

### 4.1 公共接口

#### 4.1.1 Session.resolve_special_id()

```python
def resolve_special_id(self, special_id: str) -> str:
    """
    Resolve special ID to concrete element_id.

    Args:
        special_id: One of "last_insert", "last_update", "cursor", "current"
                   or a concrete element_id (will be returned as-is)

    Returns:
        Concrete element_id

    Raises:
        ValueError: If special ID is recognized but cannot be resolved
                   (e.g., last_insert not available)

    Examples:
        >>> session.resolve_special_id("last_insert")
        "para_abc123"

        >>> session.resolve_special_id("para_xyz789")
        "para_xyz789"  # Pass-through for concrete IDs

        >>> session.resolve_special_id("last_insert")  # No insert yet
        ValueError: Special ID 'last_insert' not available: no insert operation in this session
    """
```

#### 4.1.2 Session.get_object() (Enhanced)

```python
def get_object(self, obj_id: str) -> Optional[Any]:
    """
    Get object from registry, with automatic special ID resolution.

    Args:
        obj_id: Element ID (concrete or special)

    Returns:
        The docx object, or None if not found

    Raises:
        ValueError: If special ID cannot be resolved

    Examples:
        >>> session.get_object("last_insert")
        <Paragraph object>

        >>> session.get_object("para_abc123")
        <Paragraph object>
    """
```

### 4.2 内部接口

#### 4.2.1 Session.update_context() (Enhanced)

```python
def update_context(self, element_id: str, action: str = "access"):
    """
    Update context pointers based on action type.

    Args:
        element_id: The element ID to track
        action: One of "access", "create", "update"

    Side Effects:
        - Always updates last_accessed_id
        - If action="create": updates last_created_id and last_insert_id
        - If action="update": updates last_update_id
        - Triggers auto-save if enabled
    """
```

---

## 5. 数据设计

### 5.1 Session 状态扩展

```python
@dataclass
class Session:
    # Existing fields
    session_id: str
    document: DocumentType
    object_registry: Dict[str, Any]
    cursor: Cursor
    last_created_id: Optional[str]
    last_accessed_id: Optional[str]

    # NEW: Special ID tracking
    last_insert_id: Optional[str] = None   # Tracks last inserted element
    last_update_id: Optional[str] = None   # Tracks last updated element

    # Note: cursor.element_id already tracks cursor position
```

### 5.2 特殊 ID 映射表

| Special ID | Session Attribute | Fallback Behavior |
|-----------|------------------|-------------------|
| `last_insert` | `session.last_insert_id` | Error if None |
| `last_update` | `session.last_update_id` | Error if None |
| `cursor` | `session.cursor.element_id` | Error if None |
| `current` | `session.cursor.element_id` | Error if None (alias) |

### 5.3 状态转换

```
Session Created
    ↓
last_insert_id = None
last_update_id = None
cursor.element_id = None
    ↓
[Insert Operation]
    ↓
last_insert_id = "para_abc123"
    ↓
[Update Operation]
    ↓
last_update_id = "para_abc123"
    ↓
[Cursor Move]
    ↓
cursor.element_id = "para_xyz789"
    ↓
[Delete last_insert element]
    ↓
last_insert_id = "para_abc123" (unchanged)
    ↓
[Use last_insert]
    ↓
resolve_special_id("last_insert") → "para_abc123"
get_object("para_abc123") → None
    ↓
Error: ElementNotFound
```

---

## 6. 安全考量

### 6.1 输入验证

1. **特殊 ID 大小写不敏感**: `last_insert`, `Last_Insert`, `LAST_INSERT` 都应识别
2. **防止注入**: 特殊 ID 仅限于预定义的 4 个值，不支持动态构造
3. **ID 清理**: 继续使用现有的 `clean_id` 逻辑，去除空白和额外上下文

### 6.2 错误处理

1. **明确错误消息**: 区分"特殊 ID 不可用"和"元素不存在"
2. **不泄露内部状态**: 错误消息不应暴露 object_registry 的内部结构
3. **原子性**: 特殊 ID 解析失败时，不修改文档状态

### 6.3 并发安全

1. **Session 隔离**: 每个 session 独立跟踪特殊 ID，无跨 session 影响
2. **无全局状态**: 所有状态存储在 Session 实例中
3. **线程安全**: 当前实现假设单线程访问 session（MCP 协议保证）

---

## 7. 性能考量

### 7.1 时间复杂度

| 操作 | 复杂度 | 说明 |
|------|--------|------|
| `resolve_special_id()` | O(1) | 直接属性查找 |
| `get_object()` (with special ID) | O(1) | resolve + dict lookup |
| `update_context()` | O(1) | 属性赋值 |

### 7.2 空间复杂度

- 新增 2 个 Optional[str] 字段：`last_insert_id`, `last_update_id`
- 每个 session 增加约 16 bytes（2 个指针）
- 对于 1000 个 session，增加约 16 KB 内存

### 7.3 优化策略

1. **延迟解析**: 仅在需要时解析特殊 ID，不预先缓存
2. **无历史记录**: 不维护 last_insert 的历史栈，节省内存
3. **复用现有机制**: cursor 使用现有的 Cursor 类，无额外开销

---

## 8. 测试策略

### 8.1 单元测试

**文件**: `tests/unit/test_special_position_ids.py`

测试覆盖：
1. `Session.resolve_special_id()` 的所有分支
2. `Session.get_object()` 与特殊 ID 的集成
3. `Session.update_context()` 的状态更新
4. 错误场景（未初始化、元素删除后）

### 8.2 集成测试

**文件**: `tests/integration/test_special_ids_integration.py`

测试覆盖：
1. PositionResolver 与特殊 ID 的集成
2. 各工具（paragraph, run, table）使用特殊 ID
3. 多个特殊 ID 同时使用（如 `docx_format_copy("last_insert", "last_update")`）

### 8.3 E2E 测试

**文件**: `tests/e2e/test_special_ids_workflow.py`

测试场景：
1. 完整的插入-更新-格式化工作流
2. 使用 `last_insert` 简化连续插入
3. 使用 `cursor` 进行定位插入
4. 错误恢复场景

---

## 9. 部署与回滚

### 9.1 部署步骤

1. **代码部署**: 合并 PR 到 master
2. **测试验证**: 运行完整测试套件
3. **文档更新**: 更新 README.md 和 CLAUDE.md
4. **发布说明**: 在 CHANGELOG.md 中记录新功能

### 9.2 回滚计划

如果发现严重问题：

1. **向后兼容**: 现有代码不受影响，可以继续使用具体 element_id
2. **快速回滚**: 恢复 Session 类和 PositionResolver 的修改
3. **数据安全**: 无数据迁移，回滚无数据丢失风险

### 9.3 监控指标

1. **错误率**: 监控 `SpecialIDNotAvailable` 错误的频率
2. **使用率**: 统计特殊 ID 的使用频率（通过日志）
3. **性能**: 确认 resolve_special_id() 不增加延迟

---

## 10. 未来扩展

### 10.1 可能的增强

1. **历史记录**: 支持 `last_insert[0]`, `last_insert[1]` 访问历史
2. **选区支持**: 支持 `selection_start`, `selection_end` 批量操作
3. **自定义别名**: 允许用户定义 `my_bookmark` 等自定义 ID
4. **持久化**: 将特殊 ID 状态保存到文件，支持跨会话恢复

### 10.2 不建议的方向

1. **自动 fallback**: 保持明确错误，不做隐式 fallback
2. **复杂表达式**: 不支持 `last_insert.parent` 等链式访问
3. **全局 ID**: 不支持跨 session 的特殊 ID

---

**设计者**: AI Team
**审核者**: TBD
**最后更新**: 2026-01-24
