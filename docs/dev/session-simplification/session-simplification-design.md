---
feature: session-simplification
complexity: complex
version: 1
generated_at: 2026-01-27T11:00:00+08:00
---

# 技术设计文档: Session 简化 - 移除 session_id 参数

> **功能标识**: session-simplification
> **复杂度**: complex
> **版本**: 1.0
> **生成时间**: 2026-01-27

## 1. 设计概述

### 1.1 设计目标

简化 MCP 工具 API，通过全局会话管理机制移除所有工具的 `session_id` 参数，让 Claude 调用更简洁、更符合直觉。

### 1.2 核心设计原则

1. **单一活跃会话**: 系统同时只维护一个活跃会话（global_state.active_session_id）
2. **自动会话创建**: switch_file 时自动创建会话，无需手动调用 docx_create
3. **向后兼容性**: 这是 Breaking Change，不提供兼容层
4. **最小化变更**: 尽量复用现有基础设施（global_state、SessionManager）

### 1.3 设计权衡

| 方案 | 优点 | 缺点 | 选择 |
|------|------|------|------|
| 方案 A: 全局单会话 | API 简洁，实现简单 | 不支持多文档并行编辑 | ✅ 选择 |
| 方案 B: 隐式多会话 | 支持多文档 | API 复杂，需要文件路径映射 | ❌ 不选 |
| 方案 C: 保留 session_id | 向后兼容 | 不符合简化目标 | ❌ 不选 |

**选择理由**: 方案 A 符合 80% 的使用场景（单文档编辑），实现成本最低，API 最简洁。

---

## 2. 系统架构设计

### 2.1 架构变更对比

**当前架构 (v3.0)**:
```
┌─────────────┐
│  Launcher   │
└──────┬──────┘
       │ switch_file
       ↓
┌─────────────────────┐
│   global_state      │
│  - active_file      │
│  - active_session_id│  (未使用)
└─────────────────────┘
       │
       ↓
┌─────────────────────┐
│  Claude (MCP)       │
│  docx_create()      │  ← 手动创建会话
│  docx_insert_*(sid) │  ← 需要传 session_id
└─────────────────────┘
```

**目标架构 (v4.0)**:
```
┌─────────────┐
│  Launcher   │
└──────┬──────┘
       │ switch_file
       ↓
┌─────────────────────┐
│   global_state      │
│  - active_file      │
│  - active_session_id│  ← 自动创建并存储
└─────────────────────┘
       │
       ↓
┌─────────────────────┐
│  Claude (MCP)       │
│  docx_insert_*()    │  ← 自动使用全局会话
└─────────────────────┘
```

### 2.2 核心组件设计

#### 2.2.1 GlobalState (无变更)

现有的 `global_state` 已经支持 `active_session_id`，无需修改。

```python
# src/docx_mcp_server/core/global_state.py
class GlobalState:
    _active_file: Optional[str] = None
    _active_session_id: Optional[str] = None  # 已存在，直接使用
```

#### 2.2.2 FileController (核心变更)

**变更点**: `switch_file` 方法自动创建会话

```python
# src/docx_mcp_server/api/file_controller.py

@staticmethod
def switch_file(file_path: str, force: bool = False) -> Dict[str, Any]:
    """Switch to a new active file and auto-create session."""

    # ... 现有的验证逻辑 (1-5) ...

    # 6. Close active session if exists (现有逻辑)
    if current_session_id:
        session_manager.close_session(current_session_id)

    # 7. Set new active file (现有逻辑)
    global_state.active_file = file_path

    # 8. ⭐ 新增: 自动创建会话
    session_id = session_manager.create_session(
        file_path=file_path,
        auto_save=False  # 默认不自动保存
    )
    global_state.active_session_id = session_id

    logger.info(f"File switched and session created: {file_path} -> {session_id}")
    return {
        "currentFile": file_path,
        "sessionId": session_id  # ⭐ 返回新创建的 session_id
    }
```

#### 2.2.3 Session Tools (核心变更)

**变更 1**: 移除 `docx_create` 工具

```python
# src/docx_mcp_server/tools/session_tools.py

# ❌ 删除整个函数
# def docx_create(...) -> str:
#     ...

def register_tools(mcp: FastMCP):
    # ❌ 移除注册
    # mcp.tool()(docx_create)
    mcp.tool()(docx_close)
    mcp.tool()(docx_save)
    mcp.tool()(docx_get_context)
    mcp.tool()(docx_list_sessions)
    mcp.tool()(docx_cleanup_sessions)
```

**变更 2**: 新增 `docx_get_current_session` 工具

```python
# src/docx_mcp_server/tools/session_tools.py

def docx_get_current_session() -> str:
    """Get the current active session information.

    Returns information about the globally active session, including
    session_id, file_path, and unsaved changes status.

    **No Session Required**: This tool operates on the global active session.

    Returns:
        str: Markdown-formatted response with session details

    Examples:
        >>> result = docx_get_current_session()
        >>> # Extract session_id from response
        >>> import re
        >>> match = re.search(r'\\*\\*Session ID\\*\\*:\\s*(\\w+)', result)
        >>> session_id = match.group(1) if match else None
    """
    from docx_mcp_server.server import session_manager
    from docx_mcp_server.core.global_state import global_state

    session_id = global_state.active_session_id

    if not session_id:
        return create_error_response(
            message="No active session. Please switch to a file first.",
            error_type="NoActiveSession"
        )

    session = session_manager.get_session(session_id)
    if not session:
        return create_error_response(
            message=f"Active session {session_id} not found or expired",
            error_type="SessionNotFound"
        )

    return create_markdown_response(
        session=None,
        message="Current session retrieved successfully",
        operation="Get Current Session",
        show_context=False,
        session_id=session.session_id,
        file_path=session.file_path or "None",
        auto_save=session.auto_save,
        has_unsaved_changes=session.has_unsaved_changes()
    )
```

**变更 3**: 新增 `docx_switch_session` 工具 (P2 优先级)

```python
def docx_switch_session(session_id: str) -> str:
    """Switch to a different active session.

    Allows switching between multiple sessions for advanced use cases.
    Most users should use the Launcher to switch files instead.

    Args:
        session_id: The session ID to switch to

    Returns:
        str: Markdown-formatted success message
    """
    from docx_mcp_server.server import session_manager
    from docx_mcp_server.core.global_state import global_state

    session = session_manager.get_session(session_id)
    if not session:
        return create_error_response(
            message=f"Session {session_id} not found or expired",
            error_type="SessionNotFound"
        )

    global_state.active_session_id = session_id
    global_state.active_file = session.file_path

    return create_markdown_response(
        session=None,
        message=f"Switched to session {session_id}",
        operation="Switch Session",
        show_context=False,
        session_id=session_id,
        file_path=session.file_path or "None"
    )
```

#### 2.2.4 所有工具模块 (批量变更)

**变更模式**: 移除 `session_id` 参数，从 global_state 获取

**变更前**:
```python
def docx_insert_paragraph(session_id: str, text: str, position: str, style: str = None) -> str:
    from docx_mcp_server.server import session_manager

    session = session_manager.get_session(session_id)
    if not session:
        return create_error_response(...)

    # ... 操作逻辑 ...
```

**变更后**:
```python
def docx_insert_paragraph(text: str, position: str, style: str = None) -> str:
    from docx_mcp_server.server import session_manager
    from docx_mcp_server.core.global_state import global_state

    # ⭐ 从全局状态获取 session_id
    session_id = global_state.active_session_id
    if not session_id:
        return create_error_response(
            message="No active session. Please switch to a file first.",
            error_type="NoActiveSession"
        )

    session = session_manager.get_session(session_id)
    if not session:
        return create_error_response(
            message=f"Active session {session_id} not found or expired",
            error_type="SessionNotFound"
        )

    # ... 操作逻辑 (无变更) ...
```

**辅助函数**: 提取公共逻辑

```python
# src/docx_mcp_server/utils/session_helpers.py (新文件)

def get_active_session():
    """Get the active session from global state.

    Returns:
        tuple: (session, error_response)
            - If successful: (Session object, None)
            - If failed: (None, error response string)
    """
    from docx_mcp_server.server import session_manager
    from docx_mcp_server.core.global_state import global_state
    from docx_mcp_server.core.response import create_error_response

    session_id = global_state.active_session_id
    if not session_id:
        return None, create_error_response(
            message="No active session. Please switch to a file first.",
            error_type="NoActiveSession"
        )

    session = session_manager.get_session(session_id)
    if not session:
        return None, create_error_response(
            message=f"Active session {session_id} not found or expired",
            error_type="SessionNotFound"
        )

    return session, None
```

**使用示例**:
```python
def docx_insert_paragraph(text: str, position: str, style: str = None) -> str:
    from docx_mcp_server.utils.session_helpers import get_active_session

    session, error = get_active_session()
    if error:
        return error

    # ... 操作逻辑 ...
```

---

## 3. 接口设计

### 3.1 HTTP API 变更

#### 3.1.1 POST /api/file/switch (变更)

**变更**: 响应中新增 `sessionId` 字段

**请求**:
```json
{
  "filePath": "/path/to/document.docx",
  "force": false
}
```

**响应 (变更后)**:
```json
{
  "currentFile": "/path/to/document.docx",
  "sessionId": "abc123def456"  // ⭐ 新增字段
}
```

### 3.2 MCP 工具变更

#### 3.2.1 移除的工具

| 工具名 | 说明 | 替代方案 |
|--------|------|----------|
| `docx_create` | 创建会话 | 通过 Launcher 切换文件自动创建 |

#### 3.2.2 新增的工具

| 工具名 | 参数 | 返回 | 说明 |
|--------|------|------|------|
| `docx_get_current_session` | 无 | session_id, file_path, has_unsaved | 获取当前活跃会话信息 |
| `docx_switch_session` | session_id | success | 切换到指定会话 (P2) |

#### 3.2.3 变更的工具 (所有文档操作工具)

**影响的工具模块** (~10 个文件):
- `paragraph_tools.py` (6 个工具)
- `run_tools.py` (3 个工具)
- `table_tools.py` (13 个工具)
- `format_tools.py` (6 个工具)
- `advanced_tools.py` (3 个工具)
- `cursor_tools.py` (2 个工具)
- `copy_tools.py` (2 个工具)
- `content_tools.py` (3 个工具)
- `composite_tools.py` (5 个工具)
- `session_tools.py` (3 个工具: docx_close, docx_save, docx_get_context)

**变更模式**:
1. 移除第一个参数 `session_id: str`
2. 在函数开头调用 `get_active_session()` 获取会话
3. 更新 docstring 中的参数说明和示例

**示例**:
```python
# 变更前
def docx_insert_paragraph(session_id: str, text: str, position: str, style: str = None) -> str:
    """..."""
    pass

# 变更后
def docx_insert_paragraph(text: str, position: str, style: str = None) -> str:
    """..."""
    pass
```

---

## 4. 数据设计

### 4.1 GlobalState (无变更)

现有结构已满足需求:

```python
class GlobalState:
    _active_file: Optional[str] = None
    _active_session_id: Optional[str] = None  # 已存在
```

### 4.2 Session (无变更)

Session 类无需修改，继续维护文档状态和对象注册表。

### 4.3 SessionManager (无变更)

SessionManager 的 `create_session` 和 `get_session` 方法无需修改。

---

## 5. 错误处理设计

### 5.1 新增错误类型

| 错误类型 | HTTP 状态码 | 说明 | 触发场景 |
|---------|------------|------|----------|
| `NoActiveSession` | 400 | 没有活跃会话 | 未切换文件就调用工具 |

### 5.2 错误响应格式

```markdown
# 操作结果: Error

**Status**: ❌ Error
**Error Type**: NoActiveSession
**Message**: No active session. Please switch to a file first.

---

## 💡 Suggestion

Use the Launcher GUI to select a file, or run:
```bash
mcp-server-docx --file /path/to/document.docx
```
```

### 5.3 错误处理流程

```
工具调用
    ↓
get_active_session()
    ├── global_state.active_session_id 为 None
    │   └── 返回 NoActiveSession 错误
    ├── session_manager.get_session() 返回 None
    │   └── 返回 SessionNotFound 错误
    └── 成功
        └── 继续执行工具逻辑
```

---

## 6. 安全考量

### 6.1 会话隔离

- **现状**: 每个会话独立，object_registry 互不干扰
- **变更后**: 无影响，全局会话仍然是独立的 Session 对象

### 6.2 并发安全

- **现状**: global_state 使用 threading.RLock 保护
- **变更后**: 无影响，继续使用现有锁机制

### 6.3 路径安全

- **现状**: switch_file 使用 validate_path_safety 检查
- **变更后**: 无影响，继续使用现有验证

---

## 7. 性能考量

### 7.1 性能影响分析

| 操作 | 变更前 | 变更后 | 影响 |
|------|--------|--------|------|
| 工具调用 | 直接使用 session_id | 查询 global_state | +1 次字典查询 (~O(1)) |
| 会话创建 | 手动调用 docx_create | switch_file 自动创建 | 无影响 |
| 内存占用 | N 个会话 | 1 个活跃会话 | 减少内存占用 |

**结论**: 性能影响可忽略不计 (每次工具调用增加 ~1μs)。

### 7.2 优化建议

1. **缓存 active_session_id**: 在高频调用场景下，可以在模块级别缓存 global_state.active_session_id
2. **延迟导入**: 使用 lazy import 减少模块加载时间

---

## 8. 测试策略

### 8.1 单元测试

**新增测试**:
- `test_switch_file_auto_creates_session()`: 验证 switch_file 自动创建会话
- `test_get_current_session()`: 验证获取当前会话
- `test_no_active_session_error()`: 验证未切换文件时的错误
- `test_switch_session()`: 验证会话切换 (P2)

**修改测试** (~60 个测试文件):
- 所有工具测试: 移除 `session_id` 参数传递
- 使用 `global_state.active_session_id` 设置测试会话

**测试辅助函数**:
```python
# tests/helpers/session_helpers.py

def setup_active_session(file_path: Optional[str] = None):
    """Setup a global active session for testing."""
    from docx_mcp_server.server import session_manager
    from docx_mcp_server.core.global_state import global_state

    session_id = session_manager.create_session(file_path)
    global_state.active_session_id = session_id
    return session_id

def teardown_active_session():
    """Teardown the global active session."""
    from docx_mcp_server.server import session_manager
    from docx_mcp_server.core.global_state import global_state

    if global_state.active_session_id:
        session_manager.close_session(global_state.active_session_id)
    global_state.clear()
```

### 8.2 E2E 测试

**新增测试场景**:
1. **完整工作流**: Launcher 切换文件 → 调用工具 → 保存 → 关闭
2. **错误场景**: 未切换文件直接调用工具 → 验证 NoActiveSession 错误
3. **会话切换**: 创建多个会话 → 切换 → 验证操作正确性 (P2)

### 8.3 回归测试

**策略**: 运行所有现有测试，确保功能无退化

**预期失败**: ~60 个测试需要更新（移除 session_id 参数）

---

## 9. 部署与迁移

### 9.1 版本策略

- **版本号**: v4.0.0 (Breaking Change)
- **发布类型**: Major Release
- **向后兼容**: 不兼容 v3.x

### 9.2 迁移指南

**用户迁移步骤**:

1. **更新服务器**: 升级到 v4.0.0
2. **更新调用代码**: 移除所有 `session_id` 参数
3. **更新工作流**: 使用 Launcher 切换文件，不再手动调用 `docx_create`

**迁移示例**:

```python
# v3.x (旧代码)
session_id = docx_create(file_path="./template.docx")
para_id = docx_insert_paragraph(session_id, "Text", position="end:document_body")
docx_save(session_id, "./output.docx")
docx_close(session_id)

# v4.0 (新代码)
# 1. 通过 Launcher 切换文件 (或启动时 --file 参数)
# 2. 直接调用工具
para_id = docx_insert_paragraph("Text", position="end:document_body")
docx_save("./output.docx")
# 注意: docx_close 仍需调用，但不需要 session_id
```

### 9.3 回滚计划

如果发现严重问题，可以回滚到 v3.x:

1. **保留 v3.x 分支**: 在 Git 中保留 `release/v3.x` 分支
2. **Docker 镜像**: 保留 v3.x 的 Docker 镜像
3. **文档**: 在 README 中说明如何使用 v3.x

---

## 10. 文档更新

### 10.1 需要更新的文档

| 文档 | 变更内容 |
|------|----------|
| `README.md` | 更新工具列表，移除 docx_create，新增 docx_get_current_session |
| `CLAUDE.md` | 更新所有示例代码，移除 session_id 参数 |
| `CHANGELOG.md` | 添加 v4.0.0 变更日志 |
| API 文档 | 更新所有工具的参数说明 |

### 10.2 示例代码更新

所有文档中的示例代码需要更新为新的调用方式（移除 session_id 参数）。

---

## 11. 风险与缓解

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 大量测试需要更新 | 高 | 100% | 编写脚本批量更新测试 |
| 用户代码需要迁移 | 高 | 100% | 提供详细迁移指南和示例 |
| 多会话需求 | 中 | 20% | 保留 docx_switch_session 工具 (P2) |
| 性能退化 | 低 | 5% | 性能测试验证 |

---

## 12. 后续优化

### 12.1 Phase 2 (可选)

1. **多会话支持**: 实现文件路径到 session_id 的映射，支持多文档并行编辑
2. **会话持久化**: 将会话状态持久化到磁盘，服务器重启后恢复
3. **会话共享**: 支持多个 Claude 实例共享同一会话（需要分布式锁）

### 12.2 性能优化

1. **会话池**: 预创建会话池，减少创建延迟
2. **懒加载**: 延迟加载文档内容，减少内存占用

---

**设计完成时间**: 2026-01-27
**设计者**: AI Architect
**审核状态**: 待审核
