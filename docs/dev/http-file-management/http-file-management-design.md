---
feature: http-file-management
complexity: complex
version: 1
generated_at: 2026-01-26
---

# 技术设计文档: HTTP File Management

> **功能标识**: http-file-management
> **复杂度**: complex
> **版本**: v1
> **生成时间**: 2026-01-26

## 1. 概述

### 1.1 设计目标

重构 docx-mcp-server 的文件管理架构，实现以下核心目标：

1. **职责分离**: Launcher 负责文件选择，Server 负责文档操作
2. **简化交互**: Claude 无需管理文件路径，始终操作"当前活跃文件"
3. **全局单文件**: 维护全局 active_file 状态，避免多 session 混乱
4. **HTTP 解耦**: 通过 RESTful API 实现 Launcher 和 Server 的通信
5. **Breaking Change**: 移除 `docx_create(file_path)` 参数，强制使用新架构

### 1.2 架构原则

- **Single Source of Truth**: active_file 作为全局唯一文件状态
- **Fail-Fast**: 文件切换前进行完整性检查（存在性、权限、锁定）
- **User Protection**: 未保存修改时强制用户确认
- **Backward Incompatible**: 不保留旧接口，清晰的版本升级路径

---

## 2. 系统架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interaction Layer                    │
├─────────────────────────────────────────────────────────────┤
│  Launcher GUI (PyQt6)                                        │
│  - File Browser                                              │
│  - Recent Files List                                         │
│  - Drag & Drop Support                                       │
│  - Status Display                                            │
│  - Unsaved Changes Dialog                                    │
└─────────────────┬───────────────────────────────────────────┘
                  │ HTTP REST API (JSON)
                  │ - POST /api/file/switch
                  │ - GET /api/status
                  │ - POST /api/session/close
                  ↓
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server (fastmcp)                      │
├─────────────────────────────────────────────────────────────┤
│  HTTP API Layer                                              │
│  ├─ FileController (new)                                     │
│  │   ├─ switch_file()                                        │
│  │   ├─ get_status()                                         │
│  │   └─ close_session()                                      │
│  └─ Error Handlers (404/403/423/409)                         │
├─────────────────────────────────────────────────────────────┤
│  Global State Manager (new)                                  │
│  ├─ active_file: Optional[str]                               │
│  ├─ active_session: Optional[Session]                        │
│  └─ file_lock_checker: FileLockChecker                       │
├─────────────────────────────────────────────────────────────┤
│  Session Manager (modified)                                  │
│  ├─ create_session(file_path) → session_id                   │
│  ├─ close_session(session_id, save=False)                    │
│  └─ has_unsaved_changes(session_id) → bool                   │
├─────────────────────────────────────────────────────────────┤
│  MCP Tools Layer (modified)                                  │
│  ├─ docx_create() - NO file_path parameter                   │
│  ├─ docx_save(session_id, file_path)                         │
│  ├─ docx_close(session_id)                                   │
│  └─ [REMOVED] docx_list_files, docx_create_file              │
└─────────────────────────────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────┐
│                    File System                               │
│  - Local .docx files                                         │
│  - File permissions                                          │
│  - File locks (OS-level)                                     │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 数据流

#### 2.2.1 文件切换流程

```
User selects file in Launcher
    ↓
Launcher → POST /api/file/switch {path, force=false}
    ↓
Server: FileController.switch_file()
    ├─ Validate file path (security check)
    ├─ Check file exists (404 if not)
    ├─ Check file permissions (403 if denied)
    ├─ Check file lock (423 if locked)
    ├─ Check unsaved changes
    │   ├─ If has_unsaved && !force → 409 Conflict
    │   └─ If has_unsaved && force → proceed
    ├─ Close active_session (if exists)
    ├─ Set active_file = path
    └─ Return 200 OK {currentFile, sessionId=null}
    ↓
Launcher updates UI
    ↓
Claude calls docx_create()
    ↓
Server creates session for active_file
    ↓
active_session = new Session(active_file)
```

#### 2.2.2 状态同步流程

```
Launcher starts status polling (every 2s)
    ↓
Launcher → GET /api/status
    ↓
Server returns:
{
  "currentFile": "/path/to/doc.docx",
  "sessionId": "abc-123",
  "hasUnsaved": true,
  "serverVersion": "3.0.0"
}
    ↓
Launcher updates status bar
```

---

## 3. 组件设计

### 3.1 Server 端组件

#### 3.1.1 Global State Manager (新增)

**文件**: `src/docx_mcp_server/core/global_state.py`

```python
from typing import Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class GlobalState:
    """Global state for active file management."""
    active_file: Optional[str] = None
    active_session_id: Optional[str] = None

    def set_active_file(self, file_path: str):
        """Set the active file path."""
        self.active_file = file_path
        logger.info(f"Active file set to: {file_path}")

    def clear_active_file(self):
        """Clear the active file."""
        self.active_file = None
        self.active_session_id = None
        logger.info("Active file cleared")

    def set_active_session(self, session_id: str):
        """Set the active session ID."""
        self.active_session_id = session_id
        logger.info(f"Active session set to: {session_id}")

    def get_status(self) -> dict:
        """Get current status."""
        return {
            "currentFile": self.active_file,
            "sessionId": self.active_session_id
        }

# Global singleton instance
global_state = GlobalState()
```

**职责**:
- 维护全局 active_file 和 active_session_id
- 提供线程安全的状态访问（单线程模式下简化）
- 日志记录状态变更

#### 3.1.2 File Controller (新增)

**文件**: `src/docx_mcp_server/api/file_controller.py`

```python
import os
import logging
from pathlib import Path
from typing import Optional
from docx_mcp_server.core.global_state import global_state
from docx_mcp_server.core.validators import validate_path_safety
from docx_mcp_server.server import session_manager

logger = logging.getLogger(__name__)

class FileController:
    """HTTP API controller for file management."""

    @staticmethod
    def switch_file(file_path: str, force: bool = False) -> dict:
        """
        Switch to a new active file.

        Args:
            file_path: Path to the .docx file
            force: If True, discard unsaved changes

        Returns:
            dict: {currentFile, sessionId}

        Raises:
            FileNotFoundError: File does not exist (404)
            PermissionError: No read/write permission (403)
            FileLockError: File is locked (423)
            UnsavedChangesError: Unsaved changes exist and force=False (409)
        """
        # 1. Validate path safety
        validate_path_safety(file_path)

        # 2. Check file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # 3. Check file permissions
        if not os.access(file_path, os.R_OK | os.W_OK):
            raise PermissionError(f"Permission denied: {file_path}")

        # 4. Check file lock (best effort)
        if FileController._is_file_locked(file_path):
            raise FileLockError(f"File is locked: {file_path}")

        # 5. Check unsaved changes
        if global_state.active_session_id:
            session = session_manager.get_session(global_state.active_session_id)
            if session and FileController._has_unsaved_changes(session):
                if not force:
                    raise UnsavedChangesError(
                        f"Unsaved changes exist in {global_state.active_file}"
                    )
                logger.warning(f"Discarding unsaved changes (force=True)")

        # 6. Close active session
        if global_state.active_session_id:
            session_manager.close_session(global_state.active_session_id)
            logger.info(f"Closed session: {global_state.active_session_id}")

        # 7. Set new active file
        global_state.set_active_file(file_path)
        global_state.active_session_id = None

        return {
            "currentFile": file_path,
            "sessionId": None
        }

    @staticmethod
    def get_status() -> dict:
        """Get current server status."""
        has_unsaved = False
        if global_state.active_session_id:
            session = session_manager.get_session(global_state.active_session_id)
            if session:
                has_unsaved = FileController._has_unsaved_changes(session)

        return {
            "currentFile": global_state.active_file,
            "sessionId": global_state.active_session_id,
            "hasUnsaved": has_unsaved,
            "serverVersion": "3.0.0"
        }

    @staticmethod
    def close_session(save: bool = False) -> dict:
        """Close the active session."""
        if not global_state.active_session_id:
            return {"success": True, "message": "No active session"}

        if save and global_state.active_file:
            session = session_manager.get_session(global_state.active_session_id)
            if session:
                session.document.save(global_state.active_file)
                logger.info(f"Saved before closing: {global_state.active_file}")

        session_manager.close_session(global_state.active_session_id)
        global_state.active_session_id = None

        return {"success": True}

    @staticmethod
    def _is_file_locked(file_path: str) -> bool:
        """Check if file is locked (best effort)."""
        try:
            # Try to open in exclusive mode
            with open(file_path, 'r+b') as f:
                pass
            return False
        except (IOError, OSError):
            return True

    @staticmethod
    def _has_unsaved_changes(session) -> bool:
        """Check if session has unsaved changes."""
        # Simple heuristic: check if any operations were performed
        # More sophisticated: track modification flag
        return len(session.history_stack) > 0

class FileLockError(Exception):
    """File is locked by another process."""
    pass

class UnsavedChangesError(Exception):
    """Unsaved changes exist."""
    pass
```

**职责**:
- 处理文件切换逻辑
- 执行完整性检查（存在性、权限、锁定）
- 管理 session 生命周期
- 提供状态查询接口

#### 3.1.3 HTTP API Routes (新增)

**文件**: `src/docx_mcp_server/api/routes.py`

```python
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from docx_mcp_server.api.file_controller import (
    FileController, FileLockError, UnsavedChangesError
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

class SwitchFileRequest(BaseModel):
    path: str
    force: bool = False

class CloseSessionRequest(BaseModel):
    save: bool = False

@router.post("/file/switch")
async def switch_file(request: SwitchFileRequest):
    """Switch to a new active file."""
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
                "error": str(e),
                "message": "Call with force=true to discard changes"
            }
        )

@router.get("/status")
async def get_status():
    """Get current server status."""
    return FileController.get_status()

@router.post("/session/close")
async def close_session(request: CloseSessionRequest):
    """Close the active session."""
    return FileController.close_session(request.save)
```

**职责**:
- 定义 HTTP API 端点
- 处理请求验证（Pydantic models）
- 异常到 HTTP 状态码的映射
- 日志记录 API 调用


#### 3.1.4 Modified Session Tools

**文件**: `src/docx_mcp_server/tools/session_tools.py`

**修改点**:

```python
# BEFORE (v2.x)
def docx_create(file_path: Optional[str] = None) -> str:
    """Create or load a document session."""
    if file_path:
        # Load existing file
        session = session_manager.create_session(file_path)
    else:
        # Create new document
        session = session_manager.create_session()
    return session.session_id

# AFTER (v3.0)
def docx_create() -> str:
    """
    Create a session for the active file.
    
    Raises:
        ValueError: If no active file is set
    """
    from docx_mcp_server.core.global_state import global_state
    
    if not global_state.active_file:
        raise ValueError(
            "No active file set. Use Launcher to select a file or "
            "start server with --file parameter."
        )
    
    # Create session for active file
    session = session_manager.create_session(global_state.active_file)
    global_state.set_active_session(session.session_id)
    
    logger.info(f"Session created for active file: {global_state.active_file}")
    return create_success_response(
        f"Session created for {global_state.active_file}",
        session_id=session.session_id
    )
```

**Breaking Changes**:
- 移除 `file_path` 参数
- 如果调用时传入参数，抛出 TypeError
- 依赖 global_state.active_file

#### 3.1.5 CLI Argument Handling

**文件**: `src/docx_mcp_server/server.py`

**修改点**:

```python
def main():
    parser = argparse.ArgumentParser(description="DOCX MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--file", type=str, help="Set active file on startup")
    # ... other arguments
    
    args = parser.parse_args()
    
    # Set active file if provided
    if args.file:
        from docx_mcp_server.core.global_state import global_state
        from docx_mcp_server.core.validators import validate_path_safety
        
        validate_path_safety(args.file)
        if not os.path.exists(args.file):
            logger.error(f"File not found: {args.file}")
            sys.exit(1)
        
        global_state.set_active_file(args.file)
        logger.info(f"Active file set from CLI: {args.file}")
    
    # Start server
    mcp.run(transport=args.transport, host=args.host, port=args.port)
```

**职责**:
- 解析 `--file` 参数
- 启动时设置 active_file
- 验证文件存在性

---

### 3.2 Launcher 端组件

#### 3.2.1 HTTP Client

**文件**: `src/docx_server_launcher/core/http_client.py`

```python
import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class HTTPClient:
    """HTTP client for communicating with MCP Server."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8080"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def switch_file(self, file_path: str, force: bool = False) -> Dict[str, Any]:
        """
        Switch to a new active file.
        
        Returns:
            dict: {currentFile, sessionId}
        
        Raises:
            FileNotFoundError: 404
            PermissionError: 403
            FileLockError: 423
            UnsavedChangesError: 409
        """
        response = self.session.post(
            f"{self.base_url}/api/file/switch",
            json={"path": file_path, "force": force}
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise FileNotFoundError(response.json()["detail"])
        elif response.status_code == 403:
            raise PermissionError(response.json()["detail"])
        elif response.status_code == 423:
            raise FileLockError(response.json()["detail"])
        elif response.status_code == 409:
            raise UnsavedChangesError(response.json()["detail"])
        else:
            raise RuntimeError(f"Unexpected error: {response.status_code}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current server status."""
        response = self.session.get(f"{self.base_url}/api/status")
        response.raise_for_status()
        return response.json()
    
    def close_session(self, save: bool = False) -> Dict[str, Any]:
        """Close the active session."""
        response = self.session.post(
            f"{self.base_url}/api/session/close",
            json={"save": save}
        )
        response.raise_for_status()
        return response.json()

class FileLockError(Exception):
    pass

class UnsavedChangesError(Exception):
    pass
```


#### 3.2.2 Launcher Window (Modified)

**文件**: `src/docx_server_launcher/gui/launcher_window.py`

**修改点**:

```python
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.QtCore import QTimer
from docx_server_launcher.core.http_client import HTTPClient, UnsavedChangesError

class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.http_client = HTTPClient()
        
        # Status polling timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(2000)  # Poll every 2 seconds
        
        self.setup_ui()
    
    def switch_file(self, file_path: str):
        """Switch to a new file."""
        try:
            result = self.http_client.switch_file(file_path, force=False)
            self.update_ui(result)
        except UnsavedChangesError as e:
            # Show unsaved changes dialog
            self.show_unsaved_dialog(file_path)
        except FileNotFoundError as e:
            QMessageBox.critical(self, "Error", f"File not found: {e}")
        except PermissionError as e:
            QMessageBox.critical(self, "Error", f"Permission denied: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to switch file: {e}")
    
    def show_unsaved_dialog(self, new_file_path: str):
        """Show dialog for unsaved changes."""
        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            "You have unsaved changes. What would you like to do?",
            QMessageBox.StandardButton.Save | 
            QMessageBox.StandardButton.Discard | 
            QMessageBox.StandardButton.Cancel
        )
        
        if reply == QMessageBox.StandardButton.Save:
            # Save and switch
            self.http_client.close_session(save=True)
            self.switch_file(new_file_path)
        elif reply == QMessageBox.StandardButton.Discard:
            # Discard and switch
            result = self.http_client.switch_file(new_file_path, force=True)
            self.update_ui(result)
    
    def update_status(self):
        """Poll server status."""
        try:
            status = self.http_client.get_status()
            self.status_label.setText(
                f"File: {status['currentFile'] or 'None'} | "
                f"Session: {status['sessionId'] or 'None'} | "
                f"Unsaved: {'Yes' if status['hasUnsaved'] else 'No'}"
            )
        except Exception as e:
            self.status_label.setText(f"Error: {e}")
```

**新增功能**:
- 状态轮询（2秒间隔）
- 未保存修改对话框
- 错误处理和用户提示


---

## 4. 接口设计

### 4.1 HTTP API 规范

#### 4.1.1 POST /api/file/switch

**请求**:
```json
{
  "path": "/absolute/path/to/document.docx",
  "force": false
}
```

**响应 (200 OK)**:
```json
{
  "currentFile": "/absolute/path/to/document.docx",
  "sessionId": null
}
```

**错误响应**:

| 状态码 | 场景 | 响应体 |
|--------|------|--------|
| 404 | 文件不存在 | `{"detail": "File not found: /path"}` |
| 403 | 权限不足 | `{"detail": "Permission denied"}` |
| 423 | 文件被锁定 | `{"detail": "File is locked by another process"}` |
| 409 | 未保存修改 | `{"detail": {"error": "Unsaved changes exist", "message": "Call with force=true"}}` |

#### 4.1.2 GET /api/status

**响应 (200 OK)**:
```json
{
  "currentFile": "/path/to/document.docx",
  "sessionId": "abc-123-def-456",
  "hasUnsaved": true,
  "serverVersion": "3.0.0"
}
```

#### 4.1.3 POST /api/session/close

**请求**:
```json
{
  "save": false
}
```

**响应 (200 OK)**:
```json
{
  "success": true,
  "message": "Session closed"
}
```

---

## 5. 数据设计

### 5.1 Global State

```python
@dataclass
class GlobalState:
    active_file: Optional[str] = None          # 当前活跃文件路径
    active_session_id: Optional[str] = None    # 当前活跃 session ID
```

**状态转换**:

```
[Initial State]
active_file = None
active_session_id = None
    ↓ (Launcher selects file OR CLI --file)
[File Selected]
active_file = "/path/to/doc.docx"
active_session_id = None
    ↓ (Claude calls docx_create())
[Session Active]
active_file = "/path/to/doc.docx"
active_session_id = "abc-123"
    ↓ (Launcher switches file)
[File Selected] (back to state 2)
```

### 5.2 Session Lifecycle

```
1. File Selected (via Launcher or CLI)
   → active_file set
   → active_session_id = None

2. docx_create() called
   → Session created for active_file
   → active_session_id set

3. Document operations
   → Session modified
   → has_unsaved = True

4. File switch requested
   → Check has_unsaved
   → If unsaved && !force → 409 error
   → If unsaved && force → close session, discard changes
   → If saved → close session normally

5. New file selected
   → Repeat from step 1
```


---

## 6. 安全考量

### 6.1 路径安全

**威胁**: 路径遍历攻击（Path Traversal）

**防护措施**:
```python
def validate_path_safety(file_path: str):
    """Validate file path to prevent path traversal attacks."""
    # 1. Resolve to absolute path
    abs_path = os.path.abspath(file_path)
    
    # 2. Check for suspicious patterns
    if ".." in file_path or file_path.startswith("/"):
        raise ValueError("Suspicious path pattern detected")
    
    # 3. Ensure .docx extension
    if not abs_path.endswith(".docx"):
        raise ValueError("Only .docx files are allowed")
    
    return abs_path
```

### 6.2 文件权限

**检查点**:
- 读权限（os.R_OK）
- 写权限（os.W_OK）
- 文件锁定状态（best effort）

**实现**:
```python
if not os.access(file_path, os.R_OK | os.W_OK):
    raise PermissionError("Insufficient permissions")
```

### 6.3 并发控制

**策略**: 全局单文件模式，避免并发冲突

**保护机制**:
- 文件切换时强制关闭旧 session
- 文件锁定检测（防止外部程序同时打开）


---

## 7. 迁移策略

### 7.1 Breaking Changes

#### 7.1.1 移除的接口

| 接口 | 状态 | 替代方案 |
|------|------|----------|
| `docx_list_files(directory)` | 移除 | 使用 Launcher 文件浏览器 |
| `docx_create_file(file_path)` | 移除 | 使用 Launcher 选择文件 |
| `docx_create(file_path)` | 移除参数 | 先通过 Launcher 选择，再调用 `docx_create()` |

#### 7.1.2 修改的接口

```python
# v2.x
docx_create(file_path="/path/to/doc.docx")  # ❌ 不再支持

# v3.0
# 1. 通过 Launcher 选择文件（或 CLI --file）
# 2. 调用 docx_create() 无参数
docx_create()  # ✅ 新方式
```

### 7.2 迁移步骤

#### 7.2.1 代码迁移

**步骤 1**: 搜索并移除旧接口调用

```bash
# 搜索需要修改的代码
grep -r "docx_list_files" src/
grep -r "docx_create_file" src/
grep -r "docx_create(" src/ | grep "file_path"
```

**步骤 2**: 更新测试用例

```python
# BEFORE
def test_create_with_file():
    session_id = docx_create(file_path="test.docx")
    assert session_id

# AFTER
def test_create_with_active_file():
    from docx_mcp_server.core.global_state import global_state
    global_state.set_active_file("test.docx")
    session_id = docx_create()
    assert session_id
```

**步骤 3**: 更新文档

- README.md: 更新工具列表和使用示例
- CLAUDE.md: 更新开发指南
- CHANGELOG.md: 添加 Breaking Changes 说明

#### 7.2.2 版本发布

**版本号**: v3.0.0（主版本升级，表示 Breaking Change）

**发布清单**:
- [ ] 更新 VERSION 常量
- [ ] 更新 CHANGELOG.md
- [ ] 更新 README.md
- [ ] 更新 CLAUDE.md
- [ ] 创建 Git tag: v3.0.0
- [ ] 发布 Release Notes


---

## 8. 测试策略

### 8.1 单元测试

#### 8.1.1 Global State Tests

**文件**: `tests/unit/test_global_state.py`

```python
def test_set_active_file():
    global_state.set_active_file("/path/to/doc.docx")
    assert global_state.active_file == "/path/to/doc.docx"

def test_clear_active_file():
    global_state.set_active_file("/path/to/doc.docx")
    global_state.clear_active_file()
    assert global_state.active_file is None
```

#### 8.1.2 File Controller Tests

**文件**: `tests/unit/test_file_controller.py`

```python
def test_switch_file_success():
    result = FileController.switch_file("/path/to/doc.docx")
    assert result["currentFile"] == "/path/to/doc.docx"

def test_switch_file_not_found():
    with pytest.raises(FileNotFoundError):
        FileController.switch_file("/nonexistent.docx")

def test_switch_file_unsaved_changes():
    # Setup: create session with changes
    global_state.set_active_file("/old.docx")
    session = session_manager.create_session("/old.docx")
    global_state.set_active_session(session.session_id)
    # Simulate changes
    session.history_stack.append(Commit())
    
    # Test: switch without force should raise
    with pytest.raises(UnsavedChangesError):
        FileController.switch_file("/new.docx", force=False)
    
    # Test: switch with force should succeed
    result = FileController.switch_file("/new.docx", force=True)
    assert result["currentFile"] == "/new.docx"
```

### 8.2 集成测试

#### 8.2.1 HTTP API Tests

**文件**: `tests/integration/test_api.py`

```python
def test_api_switch_file(client):
    response = client.post("/api/file/switch", json={
        "path": "/path/to/doc.docx",
        "force": False
    })
    assert response.status_code == 200
    assert response.json()["currentFile"] == "/path/to/doc.docx"

def test_api_get_status(client):
    response = client.get("/api/status")
    assert response.status_code == 200
    assert "currentFile" in response.json()
    assert "sessionId" in response.json()
```

### 8.3 E2E 测试

#### 8.3.1 Launcher Integration

**文件**: `tests/e2e/test_launcher_integration.py`

```python
def test_launcher_file_selection():
    # 1. Start server
    # 2. Start launcher
    # 3. Select file via launcher
    # 4. Verify server status updated
    # 5. Call docx_create()
    # 6. Verify session created
    pass
```


---

## 9. 实施计划

### 9.1 开发阶段

| 阶段 | 任务 | 预计工作量 | 依赖 |
|------|------|-----------|------|
| Phase 1 | Server 核心重构 | 2-3 天 | - |
| Phase 2 | HTTP API 实现 | 1-2 天 | Phase 1 |
| Phase 3 | Launcher 集成 | 2-3 天 | Phase 2 |
| Phase 4 | 测试与文档 | 1-2 天 | Phase 3 |
| Phase 5 | 迁移与发布 | 1 天 | Phase 4 |

**总计**: 7-11 天

### 9.2 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| fastmcp HTTP 能力不足 | 中 | 高 | 提前验证，准备 FastAPI 备选方案 |
| 文件锁定检测不可靠 | 高 | 低 | 使用 best-effort 策略，用户提示 |
| 测试覆盖不足 | 中 | 中 | 优先编写核心路径测试 |
| 用户迁移阻力 | 低 | 中 | 提供详细迁移指南和示例 |

---

## 10. 总结

### 10.1 核心变更

1. **架构变更**: 从"Claude 管理文件"到"Launcher 管理文件"
2. **接口变更**: 移除 `docx_create(file_path)` 参数
3. **通信方式**: 新增 HTTP REST API
4. **状态管理**: 全局单文件模式

### 10.2 预期收益

- **简化交互**: Claude 无需管理文件路径，减少 token 消耗
- **职责清晰**: Launcher 负责文件选择，Server 负责文档操作
- **用户体验**: 统一的文件选择界面，支持拖拽、最近文件等
- **可靠性**: 未保存修改保护，避免数据丢失

### 10.3 技术债务

- 文件锁定检测依赖 OS 行为，可能不可靠
- 状态轮询（2秒）可能有延迟，未来可考虑 WebSocket
- 单文件模式限制了并发能力，未来可扩展为多文件模式

---

## 11. 附录

### 11.1 参考资料

- [fastmcp Documentation](https://github.com/jlowin/fastmcp)
- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [python-docx Documentation](https://python-docx.readthedocs.io/)

### 11.2 相关文档

- `http-file-management-requirements.md`: 需求文档
- `http-file-management-tasks.md`: 任务拆分文档（待生成）

---

**文档版本**: v1
**最后更新**: 2026-01-26
**作者**: AI Architect
**审查状态**: Draft
