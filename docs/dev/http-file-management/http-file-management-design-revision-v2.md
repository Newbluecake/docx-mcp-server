---
feature: http-file-management
complexity: complex
version: 2
generated_at: 2026-01-26
revision_reason: Plan review feedback - correct FastMCP integration approach
---

# 技术设计文档修订版 v2: HTTP File Management

> **功能标识**: http-file-management
> **复杂度**: complex
> **版本**: v2 (Revision)
> **修订时间**: 2026-01-26
> **修订原因**: 修正 FastMCP HTTP 集成方式，根据 spec-plan-reviewer 审查报告

## 📋 修订摘要

### Critical Issues 修正

| Issue ID | 问题描述 | 修正方案 | 影响范围 |
|---------|---------|---------|---------|
| CI-1 | FastMCP HTTP API 集成方式错误 | 改用 FastAPI + 挂载 MCP 的正确架构 | 架构设计、Server 端实现 |
| CI-2 | 缺少依赖声明 | 添加 fastapi, uvicorn, requests 到 pyproject.toml | 依赖管理 |
| CI-3 | Session 未保存检测逻辑有缺陷 | 添加显式 dirty flag 跟踪 | Session Manager |
| CI-4 | Breaking Change 影响分析不完整 | 完整识别受影响文件并提供迁移路径 | 测试、文档 |

### Important Additions 新增

| Addition ID | 新增内容 | 优先级 |
|------------|---------|--------|
| IA-1 | GlobalState 线程安全 | P0 |
| IA-2 | Launcher HTTP 重试逻辑 | P1 |
| IA-3 | Launcher 服务器健康检查 | P1 |
| IA-4 | STDIO 模式优雅降级 | P1 |
| IA-5 | 路径验证安全性增强 | P0 |

---

## 1. 架构设计修正（CI-1）

### 1.1 原设计问题

**错误假设**：FastMCP 可以直接托管自定义 REST 端点
```
MCP Server (fastmcp)
  ├─ HTTP API Layer (自定义端点)  # ❌ 错误
  │   ├─ POST /api/file/switch
  │   └─ GET /api/status
```

### 1.2 正确架构

**正确方式**：FastAPI 作为主应用，挂载 MCP

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
│                   (主 ASGI 应用)                              │
├─────────────────────────────────────────────────────────────┤
│  Custom REST API Endpoints                                   │
│  ├─ POST /api/file/switch                                    │
│  ├─ GET /api/status                                          │
│  └─ POST /api/session/close                                  │
├─────────────────────────────────────────────────────────────┤
│  MCP Server (Mounted at /mcp)                                │
│  └─ MCP Tools: docx_create(), docx_save(), etc.             │
└─────────────────────────────────────────────────────────────┘
         │
         ↓ uvicorn (ASGI Server)
         ↓ http://localhost:8080
```

### 1.3 实现代码

**文件**: `src/docx_mcp_server/combined_server.py` (新增)

```python
"""
Combined FastAPI + MCP Server.

Architecture:
- FastAPI hosts custom REST API endpoints for file management
- MCP server is mounted at /mcp for Claude integration
- Single unified server process
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import logging

# Import MCP server
from docx_mcp_server.server import mcp

# Import file management
from docx_mcp_server.api.file_controller import (
    FileController,
    FileLockError,
    UnsavedChangesError
)

logger = logging.getLogger(__name__)

# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Docx MCP Server",
    description="Combined MCP + REST API for document management",
    version="3.0.0"
)

# ============================================================================
# Request/Response Models
# ============================================================================

class SwitchFileRequest(BaseModel):
    path: str
    force: bool = False

class CloseSessionRequest(BaseModel):
    save: bool = False

class StatusResponse(BaseModel):
    currentFile: Optional[str]
    sessionId: Optional[str]
    hasUnsaved: bool
    serverVersion: str

# ============================================================================
# Custom REST API Endpoints
# ============================================================================

@app.post("/api/file/switch", response_model=dict)
async def switch_file(request: SwitchFileRequest):
    """
    Switch to a new active file.

    Errors:
        404: File not found
        403: Permission denied
        423: File locked
        409: Unsaved changes (use force=true to override)
    """
    try:
        result = FileController.switch_file(request.path, request.force)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileLockError as e:
        raise HTTPException(status_code=423, detail=str(e))
    except UnsavedChangesError as e:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "Unsaved changes exist",
                "currentFile": FileController.get_status()["currentFile"],
                "message": "Call with force=true to discard changes"
            }
        )

@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Get current server status."""
    return FileController.get_status()

@app.post("/api/session/close")
async def close_session(request: CloseSessionRequest):
    """Close the active session."""
    return FileController.close_session(request.save)

@app.get("/health")
async def health_check():
    """Health check endpoint for Launcher."""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "transport": "http"
    }

# ============================================================================
# Mount MCP Server
# ============================================================================

# Mount MCP server at /mcp path
app.mount("/mcp", mcp.get_asgi_app(path="/mcp"))

logger.info("MCP server mounted at /mcp")

# ============================================================================
# Main Entry Point
# ============================================================================

def run_combined_server(host: str = "127.0.0.1", port: int = 8080):
    """Run the combined FastAPI + MCP server."""
    import uvicorn

    logger.info(f"Starting combined server at http://{host}:{port}")
    logger.info(f"  - REST API: http://{host}:{port}/api/")
    logger.info(f"  - MCP endpoint: http://{host}:{port}/mcp")

    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    run_combined_server()
```

### 1.4 启动脚本修改

**文件**: `src/docx_mcp_server/__main__.py`

```python
def main():
    parser = argparse.ArgumentParser(description="Docx MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse", "streamable-http", "combined"],
                        default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--file", help="Default active file path")

    args = parser.parse_args()

    # Set initial active file from CLI
    if args.file:
        from docx_mcp_server.core.global_state import global_state
        global_state.set_active_file(args.file)
        logger.info(f"Initial active file: {args.file}")

    if args.transport == "combined":
        # New combined mode: FastAPI + MCP
        from docx_mcp_server.combined_server import run_combined_server
        run_combined_server(host=args.host, port=args.port)
    elif args.transport == "stdio":
        # Traditional MCP-only mode
        mcp.run(transport="stdio")
    # ... other modes
```

---

## 2. 依赖管理修正（CI-2）

### 2.1 pyproject.toml 更新

```toml
[project]
name = "docx-mcp-server"
version = "3.0.0"  # Major version bump for breaking change
dependencies = [
    "mcp>=0.1.0",
    "python-docx>=1.1.0",
    "pywin32>=306 ; sys_platform == 'win32'",
    # ⭐ New dependencies for HTTP API
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.0.0",
    "requests>=2.31.0"  # For Launcher HTTP client
]

[project.optional-dependencies]
gui = [
    "PyQt6>=6.6.0",
    "PyQt6-Qt6>=6.6.0",
    "PyQt6-sip>=13.6.0",
    "requests>=2.31.0"  # Already in main deps, kept for clarity
]
```

---

## 3. Session 未保存检测修正（CI-3）

### 3.1 问题分析

**当前实现**（有缺陷）:
```python
def _has_unsaved_changes(session) -> bool:
    return len(session.history_stack) > 0  # ❌ 保存后不会清空
```

**问题**:
1. `history_stack` 用于 rollback/undo，不是变更追踪
2. `docx_save()` 后不会清空 `history_stack`
3. 导致误判：保存后仍显示 hasUnsaved=True

### 3.2 解决方案

**修改**: `src/docx_mcp_server/core/session.py`

```python
from dataclasses import dataclass, field
import threading

@dataclass
class Session:
    """Document editing session."""
    session_id: str
    document: Document
    object_registry: Dict[str, Any] = field(default_factory=dict)
    history_stack: List[Commit] = field(default_factory=list)
    cursor: Cursor = field(default_factory=Cursor)

    # ⭐ New: Explicit dirty tracking
    _is_dirty: bool = False
    _last_save_commit_index: int = -1
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def mark_dirty(self):
        """Mark session as having unsaved changes."""
        with self._lock:
            self._is_dirty = True

    def has_unsaved_changes(self) -> bool:
        """Check if session has unsaved changes."""
        with self._lock:
            # Dirty if explicitly marked OR if commits since last save
            return (
                self._is_dirty or
                len(self.history_stack) > self._last_save_commit_index + 1
            )

    def mark_saved(self):
        """Mark session as saved (clear dirty flag)."""
        with self._lock:
            self._is_dirty = False
            self._last_save_commit_index = len(self.history_stack) - 1
```

**修改**: `src/docx_mcp_server/tools/session_tools.py`

```python
def docx_save(session_id: str, file_path: str) -> str:
    """Save document to disk."""
    session = session_manager.get_session(session_id)
    if not session:
        return create_error_response(f"Session {session_id} not found")

    try:
        session.document.save(file_path)

        # ⭐ Clear dirty flag after successful save
        session.mark_saved()

        return create_success_response(
            f"Document saved to {file_path}",
            file_path=file_path
        )
    except Exception as e:
        logger.exception(f"Save failed: {e}")
        return create_error_response(f"Save failed: {str(e)}")
```

**触发 dirty flag**: 所有修改操作中调用

```python
# 在所有修改工具中添加
def docx_insert_paragraph(session_id: str, text: str, position: str) -> str:
    session = session_manager.get_session(session_id)
    # ... 插入逻辑 ...

    # ⭐ Mark session as dirty
    session.mark_dirty()

    return create_context_aware_response(...)
```

---

## 4. Breaking Change 影响分析（CI-4）

### 4.1 受影响文件识别

**搜索命令**:
```bash
# 查找所有使用 docx_create(file_path) 的代码
grep -r "docx_create(" --include="*.py" | grep -v "docx_create()" | wc -l

# 查找 docx_list_files 使用
grep -r "docx_list_files" --include="*.py" | wc -l

# 查找 docx_create_file 使用
grep -r "docx_create_file" --include="*.py" | wc -l
```

**预期影响范围**:
- 单元测试: `tests/unit/test_session_tools.py`, `tests/unit/test_paragraph_tools.py` (约 20+ 处)
- E2E 测试: `tests/e2e/test_template_workflow.py` (约 5+ 处)
- 文档: `README.md`, `CLAUDE.md` (约 10+ 处示例代码)

### 4.2 迁移路径

#### Phase 1: v2.3 添加废弃警告（兼容期 3 个月）

```python
def docx_create(file_path: str = "") -> str:
    """
    Create a new session.

    Args:
        file_path: [DEPRECATED] Will be removed in v3.0.
                   Use Launcher or --file instead.
    """
    if file_path:
        # ⚠️ 显示废弃警告但仍可工作
        logger.warning(
            "DEPRECATION WARNING: docx_create(file_path) will be removed in v3.0. "
            "Please use Launcher file selection or --file CLI parameter instead. "
            "See migration guide: https://github.com/.../docs/migration-v2-to-v3.md"
        )
        # 仍使用旧逻辑
        return _old_create_session(file_path)
    else:
        # 新逻辑
        return _new_create_session_from_active_file()
```

#### Phase 2: v3.0 移除旧接口（Breaking Change）

```python
def docx_create() -> str:
    """
    Create a new session for the active file.

    The active file must be set via:
    - Launcher file selection (POST /api/file/switch)
    - CLI parameter (--file /path/to/doc.docx)

    Raises:
        ValueError: If no active file is set
    """
    from docx_mcp_server.core.global_state import global_state

    if not global_state.active_file:
        return create_error_response(
            "No active file set. Use Launcher to select a file or start with --file parameter.",
            error_type="NoActiveFile"
        )

    return _new_create_session_from_active_file()
```

#### Phase 3: 更新所有测试和文档

**Task Checklist**:
- [ ] T-014: 更新所有单元测试（移除 file_path 参数）
- [ ] T-015: 更新所有 E2E 测试（使用 global_state.set_active_file()）
- [ ] T-016: 更新 README.md 示例代码
- [ ] T-017: 更新 CLAUDE.md 示例代码
- [ ] T-018: 创建迁移指南 `docs/migration-v2-to-v3.md`

---

## 5. 线程安全增强（IA-1）

### 5.1 GlobalState 线程安全

**文件**: `src/docx_mcp_server/core/global_state.py`

```python
import threading
from typing import Optional
from contextlib import contextmanager

class GlobalState:
    """
    Thread-safe global state manager.

    In HTTP mode, FastAPI uses async/multi-threaded request handling.
    Must protect mutable state with locks.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._active_file: Optional[str] = None
        self._active_session_id: Optional[str] = None

    @contextmanager
    def atomic(self):
        """Context manager for atomic operations."""
        with self._lock:
            yield

    @property
    def active_file(self) -> Optional[str]:
        """Thread-safe getter for active_file."""
        with self._lock:
            return self._active_file

    @active_file.setter
    def active_file(self, value: Optional[str]):
        """Thread-safe setter for active_file."""
        with self._lock:
            self._active_file = value

    def set_active_file(self, file_path: str):
        """Set active file atomically."""
        with self._lock:
            self._active_file = file_path

    # Similar for active_session_id...

# Global singleton
global_state = GlobalState()
```

---

## 6. Launcher HTTP 重试逻辑（IA-2）

### 6.1 HTTPClient 增强

**文件**: `src/launcher/http_client.py`

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

logger = logging.getLogger(__name__)

class HTTPClient:
    """HTTP client with retry logic for Launcher."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 5.0,
        max_retries: int = 3
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()

        # ⭐ Configure retry adapter
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=0.5,  # 0.5s, 1s, 2s
            status_forcelist=[500, 502, 503, 504],  # Retry on server errors
            allowed_methods=["GET", "POST"]  # Retry safe methods
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def post(self, path: str, data: dict) -> dict:
        """POST request with retry."""
        url = f"{self.base_url}{path}"
        try:
            response = self.session.post(url, json=data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.ConnectionError as e:
            logger.error(f"Connection failed: {e}")
            raise ServerConnectionError(f"Cannot connect to server: {self.base_url}")
        except requests.Timeout:
            logger.error(f"Request timeout: {url}")
            raise ServerTimeoutError(f"Server did not respond in {self.timeout}s")

    def get(self, path: str) -> dict:
        """GET request with retry."""
        url = f"{self.base_url}{path}"
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.ConnectionError as e:
            logger.error(f"Connection failed: {e}")
            raise ServerConnectionError(f"Cannot connect to server: {self.base_url}")
```

---

## 7. Launcher 健康检查（IA-3）

### 7.1 启动时验证

**文件**: `src/launcher/main_window.py`

```python
def __init__(self):
    super().__init__()

    self.http_client = HTTPClient(base_url="http://localhost:8080")

    # ⭐ Verify server connection on startup
    is_healthy, message = self._verify_server_health()
    if not is_healthy:
        self._show_server_error_dialog(message)
        return

    self._setup_ui()
    self._start_status_polling()

def _verify_server_health(self) -> tuple[bool, str]:
    """Verify server is reachable and compatible."""
    try:
        # Call /health endpoint
        health = self.http_client.get("/health")
        server_version = health.get("version", "unknown")

        # ⭐ Version compatibility check
        if not server_version.startswith("3."):
            return False, (
                f"Incompatible server version: {server_version}\n"
                f"Launcher requires server v3.x"
            )

        logger.info(f"✅ Connected to server v{server_version}")
        return True, f"Connected to server v{server_version}"

    except ServerConnectionError:
        return False, (
            "Cannot connect to server at http://localhost:8080\n\n"
            "Please start the server with:\n"
            "  mcp-server-docx --transport combined --port 8080"
        )
    except Exception as e:
        logger.exception(f"Health check failed: {e}")
        return False, f"Server health check failed: {str(e)}"

def _show_server_error_dialog(self, message: str):
    """Show error dialog and disable UI."""
    QMessageBox.critical(
        self,
        "Server Connection Failed",
        message,
        QMessageBox.StandardButton.Ok
    )
    # Disable file operations
    self.file_browser_btn.setEnabled(False)
    self.path_input.setEnabled(False)
```

---

## 8. STDIO 模式优雅降级（IA-4）

### 8.1 文档说明

**README.md 添加**:

```markdown
## Transport Modes

### Combined Mode (Recommended for Launcher)

```bash
mcp-server-docx --transport combined --port 8080
```

Enables:
- ✅ HTTP REST API for Launcher file management
- ✅ MCP endpoint for Claude integration
- ✅ Single unified server process

### STDIO Mode (For CLI Usage)

```bash
mcp-server-docx --transport stdio --file /path/to/doc.docx
```

Limitations:
- ❌ No Launcher support (no HTTP API)
- ✅ Must specify --file at startup
- ✅ Suitable for scripting and automation

**Note**: Launcher requires `--transport combined` mode.
```

### 8.2 Launcher 检测

```python
def _verify_server_health(self) -> tuple[bool, str]:
    try:
        health = self.http_client.get("/health")

        # ⭐ Check transport mode
        transport = health.get("transport")
        if transport != "http":
            return False, (
                f"Server is in {transport} mode, but Launcher requires HTTP mode.\n\n"
                f"Please restart server with:\n"
                f"  mcp-server-docx --transport combined --port 8080"
            )

        return True, "Connected"
    except:
        # ...
```

---

## 9. 路径验证安全性（IA-5）

### 9.1 增强的验证函数

**文件**: `src/docx_mcp_server/core/validators.py`

```python
import os
from pathlib import Path

def validate_path_safety(file_path: str) -> str:
    """
    Validate and normalize file path.

    Security checks:
    1. Resolve to absolute path (防止相对路径遍历)
    2. Validate extension (仅允许 .docx)
    3. Check path traversal (防止 ../ 攻击)

    Args:
        file_path: User-provided file path

    Returns:
        str: Normalized absolute path

    Raises:
        ValueError: If path is suspicious or invalid
    """
    # 1. Expand user home and resolve to absolute
    abs_path = os.path.abspath(os.path.expanduser(file_path))

    # 2. Validate extension
    if not abs_path.lower().endswith('.docx'):
        raise ValueError(
            f"Only .docx files are allowed. Got: {abs_path}"
        )

    # 3. Check for suspicious patterns (after normalization)
    # Note: After abspath(), ".." should be resolved
    # This is a defense-in-depth check
    if ".." in abs_path:
        raise ValueError(
            f"Suspicious path pattern detected: {abs_path}"
        )

    # 4. Optionally restrict to specific directories
    # allowed_dirs = [
    #     str(Path.home()),  # User's home directory
    #     os.getcwd()         # Current working directory
    # ]
    # if not any(abs_path.startswith(d) for d in allowed_dirs):
    #     raise ValueError(f"Path outside allowed directories: {abs_path}")

    return abs_path
```

---

## 10. 任务拆分修正

### 10.1 并行分组调整

**原任务计划问题**: T-002 依赖 T-001，但都在 Parallel Group 1

**修正后的分组**:

```
Phase 1: 基础设施（串行）
  T-001: 实现 GlobalState 管理器（线程安全版本）
    ↓
  T-002: 实现 FileController（依赖 T-001）

Phase 2: Server 端（并行）
  Parallel Group 2a:
    - T-003: 修改 Session Manager (添加 dirty tracking)
    - T-004: 创建 combined_server.py (FastAPI + MCP)

  Sequential after 2a:
    - T-005: 实现 HTTP API routes (依赖 T-004)
    - T-006: 修改 __main__.py (添加 combined 模式)

Phase 3: Launcher 端（并行）
  Parallel Group 3:
    - T-007: 实现 HTTPClient (带重试)
    - T-008: 实现文件选择 UI
    - T-009: 实现状态轮询
    - T-010: 实现未保存警告对话框

Phase 4: Breaking Change（串行）
  T-011: 移除 docx_list_files, docx_create_file
    ↓
  T-012: 修改 docx_create() (移除 file_path 参数)
    ↓
  T-013: 添加 --file CLI 参数支持
    ↓
  T-014: 更新所有单元测试
    ↓
  T-015: 更新所有 E2E 测试
    ↓
  T-016: 更新 README.md
    ↓
  T-017: 更新 CLAUDE.md
    ↓
  T-018: 创建迁移指南
```

---

## 11. 依赖更新清单

### 11.1 pyproject.toml 完整版本

```toml
[project]
name = "docx-mcp-server"
version = "3.0.0"
description = "MCP server for Microsoft Word document operations"
dependencies = [
    "mcp>=0.1.0",
    "python-docx>=1.1.0",
    "pywin32>=306 ; sys_platform == 'win32'",
    # HTTP API dependencies
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    # HTTP client for Launcher
    "requests>=2.31.0",
    "urllib3>=2.0.0"
]

[project.optional-dependencies]
gui = [
    "PyQt6>=6.6.0",
    "PyQt6-Qt6>=6.6.0",
    "PyQt6-sip>=13.6.0"
]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.21.0",  # For async FastAPI tests
    "httpx>=0.25.0"  # For FastAPI test client
]
```

---

## 12. 风险缓解措施

| 原风险 | 缓解措施 | 新增验证 |
|--------|---------|---------|
| FastMCP 能力不足 | 改用 FastAPI + MCP 挂载，已验证可行 | T-005 单元测试 |
| 线程安全问题 | GlobalState 加锁，Session 加锁 | T-019 并发测试 |
| 文件锁检测失败 | Best-effort + 用户警告 | 保持现状 |
| Breaking Change 摩擦 | v2.3 废弃警告 + 迁移指南 | T-018 |

---

## 13. 新增测试任务

| Task ID | 测试内容 | 类型 |
|---------|---------|------|
| T-019 | GlobalState 并发访问测试 | 单元测试 |
| T-020 | HTTPClient 重试逻辑测试 | 单元测试 |
| T-021 | Combined server 集成测试 | E2E |
| T-022 | Launcher 健康检查测试 | 单元测试 |
| T-023 | Path validation 安全测试 | 单元测试 |

---

## 附录 A: FastMCP 集成验证

### A.1 官方文档确认

**来源**: [FastMCP FastAPI Integration](https://gofastmcp.com/integrations/fastapi)

**关键代码**:
```python
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

# 1. Create FastAPI app
api = FastAPI()

# 2. Create MCP server
mcp = FastMCP("my-server")

# 3. Mount MCP into FastAPI
api.mount("/mcp", mcp.get_asgi_app(path="/mcp"))

# 4. Run with uvicorn
import uvicorn
uvicorn.run(api, host="0.0.0.0", port=8000)
```

**确认**: ✅ FastAPI 作为主应用，MCP 挂载为子应用

---

**文档版本**: v2 (Revision)
**修订时间**: 2026-01-26
**修订者**: System Architect
**审查状态**: Ready for Implementation
