---
feature: http-file-management
complexity: complex
version: 2
generated_at: 2026-01-26
revision_reason: Reflect design-revision-v2 changes (FastAPI architecture, thread safety, etc.)
---

# 任务拆分文档 v2: HTTP File Management

> **功能标识**: http-file-management
> **复杂度**: complex
> **版本**: v2 (Revision)
> **生成时间**: 2026-01-26
> **修订原因**: 反映 design-revision-v2 的架构修正

## 1. 任务概览

### 1.1 任务统计

- **总任务数**: 23（原 15 + 新增 8）
- **P0 任务**: 15
- **P1 任务**: 5
- **P2 任务**: 3
- **并行组数**: 4

### 1.2 修订摘要

| 变更类型 | 数量 | 详情 |
|---------|------|------|
| 架构修正 | 3 | T-004, T-005, T-006 (FastAPI + MCP 挂载) |
| 安全增强 | 2 | T-001 (线程安全), T-019 (路径验证) |
| Session 修正 | 1 | T-003 (dirty tracking) |
| Launcher 增强 | 2 | T-007 (重试), T-010 (健康检查) |
| Breaking Change | 5 | T-011 ~ T-018 (完整迁移路径) |
| 新增测试 | 5 | T-019 ~ T-023 |

### 1.3 依赖关系图（修订）

```
Phase 1: 基础设施（串行）- 2个任务
T-001: GlobalState Manager (线程安全版) ⭐
  ↓
T-002: FileController (依赖 T-001) ⭐

Phase 2: Server 端（并行 + 串行）- 4个任务
Parallel Group 2a:
├─ T-003: Session Manager (dirty tracking) ⭐
└─ T-004: combined_server.py (FastAPI + MCP) ⭐

Sequential after 2a:
T-005: HTTP API routes (依赖 T-004) ⭐
  ↓
T-006: __main__.py (添加 combined 模式) ⭐

Phase 3: Launcher 端（并行）- 4个任务 (Parallel Group 3)
├─ T-007: HTTPClient (带重试) ⭐
├─ T-008: 文件选择 UI
├─ T-009: 状态轮询
└─ T-010: 健康检查 ⭐

Phase 4: Breaking Change（串行）- 8个任务
T-011: 移除 docx_list_files, docx_create_file
  ↓
T-012: 修改 docx_create() (移除 file_path 参数) ⭐
  ↓
T-013: 添加 --file CLI 参数
  ↓
T-014: 更新单元测试 ⭐
  ↓
T-015: 更新 E2E 测试 ⭐
  ↓
T-016: 更新 README.md ⭐
  ↓
T-017: 更新 CLAUDE.md ⭐
  ↓
T-018: 创建迁移指南 ⭐

Phase 5: 安全增强（并行）- 2个任务 (Parallel Group 5)
├─ T-019: 路径验证增强 ⭐
└─ T-020: 依赖声明更新 ⭐

Phase 6: 新增测试（并行）- 5个任务 (Parallel Group 6)
├─ T-021: GlobalState 并发测试 ⭐
├─ T-022: HTTPClient 重试测试 ⭐
├─ T-023: Combined server 集成测试 ⭐
├─ T-024: Launcher 健康检查测试
└─ T-025: Path validation 安全测试

⭐ = 修订后的任务或新增任务
```

---

## 2. 任务详情

### Phase 1: 基础设施（串行）

#### T-001: GlobalState Manager（线程安全版）⭐ 修订

**优先级**: P0
**复杂度**: Standard
**预计工时**: 3 小时（原 2 小时）
**依赖**: 无
**并行组**: 1（串行）
**修订原因**: 添加线程安全（IA-1）

**描述**:
创建线程安全的全局状态管理器，在 HTTP 模式下保护并发访问。

**实施步骤**:
1. 创建文件 `src/docx_mcp_server/core/global_state.py`
2. 实现 GlobalState 类（使用 threading.Lock）
3. 添加属性访问器（@property + setter，带锁）
4. 实现 atomic() 上下文管理器
5. 创建全局单例 global_state
6. 添加日志记录

**关键代码**（参考 design-revision-v2.md §5.1）:
```python
import threading
from typing import Optional
from contextlib import contextmanager

class GlobalState:
    def __init__(self):
        self._lock = threading.Lock()
        self._active_file: Optional[str] = None
        self._active_session_id: Optional[str] = None

    @contextmanager
    def atomic(self):
        with self._lock:
            yield

    @property
    def active_file(self) -> Optional[str]:
        with self._lock:
            return self._active_file

    @active_file.setter
    def active_file(self, value: Optional[str]):
        with self._lock:
            self._active_file = value
```

**验收标准**:
- [ ] GlobalState 类实现完整（含线程锁）
- [ ] 所有属性访问器都是线程安全的
- [ ] atomic() 上下文管理器可用
- [ ] 全局单例可导入使用
- [ ] 状态变更有日志记录
- [ ] 单元测试通过（test_global_state.py）

**测试用例**:
```python
def test_thread_safe_access():
    import threading

    def writer():
        for i in range(100):
            global_state.active_file = f"/file{i}.docx"

    threads = [threading.Thread(target=writer) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Should not crash or corrupt data
    assert global_state.active_file is not None
```

**风险**:
- 低：threading.Lock 是标准库，成熟可靠

---

#### T-002: FileController

**优先级**: P0
**复杂度**: Standard
**预计工时**: 4 小时
**依赖**: T-001
**并行组**: 1（串行，必须在 T-001 之后）

**描述**:
实现文件切换逻辑控制器，处理错误检查和 session 生命周期。

**实施步骤**:
1. 创建文件 `src/docx_mcp_server/api/file_controller.py`
2. 实现 FileController.switch_file() 方法
3. 实现 FileController.get_status() 方法
4. 实现 FileController.close_session() 方法
5. 实现辅助方法：_is_file_locked(), _has_unsaved_changes()
6. 定义自定义异常：FileLockError, UnsavedChangesError

**关键代码**（参考 design-revision-v2.md §3.1.2）:
```python
from docx_mcp_server.core.global_state import global_state

class FileController:
    @staticmethod
    def switch_file(file_path: str, force: bool = False) -> dict:
        # 1. Validate path
        validate_path_safety(file_path)

        # 2-4. Check file exists, permissions, lock

        # 5. Check unsaved changes
        if global_state.active_session_id:
            session = session_manager.get_session(global_state.active_session_id)
            if session and session.has_unsaved_changes():
                if not force:
                    raise UnsavedChangesError(...)

        # 6. Close active session
        if global_state.active_session_id:
            session_manager.close_session(global_state.active_session_id)

        # 7. Set new active file
        global_state.active_file = file_path
        global_state.active_session_id = None

        return {"currentFile": file_path, "sessionId": None}
```

**验收标准**:
- [ ] switch_file() 实现所有检查（存在、权限、锁定、未保存）
- [ ] 错误返回正确的异常类型
- [ ] get_status() 返回正确的状态信息
- [ ] 单元测试通过（test_file_controller.py）

**测试用例**:
```python
def test_switch_file_not_found():
    with pytest.raises(FileNotFoundError):
        FileController.switch_file("/nonexistent.docx")

def test_switch_file_unsaved_changes():
    # Setup: create session with changes
    global_state.active_file = "/old.docx"
    session_id = session_manager.create_session("/old.docx")
    global_state.active_session_id = session_id
    session = session_manager.get_session(session_id)
    session.mark_dirty()

    # Should raise UnsavedChangesError
    with pytest.raises(UnsavedChangesError):
        FileController.switch_file("/new.docx", force=False)

    # With force=True, should succeed
    result = FileController.switch_file("/new.docx", force=True)
    assert result["currentFile"] == "/new.docx"
```

---

### Phase 2: Server 端

#### T-003: Session Manager（dirty tracking）⭐ 修订

**优先级**: P0
**复杂度**: Standard
**预计工时**: 3 小时（原 2 小时）
**依赖**: T-001
**并行组**: 2a（与 T-004 并行）
**修订原因**: 修正未保存检测逻辑（CI-3）

**描述**:
修改 Session 类，添加显式的 dirty tracking，修正 has_unsaved_changes() 逻辑。

**实施步骤**:
1. 修改文件 `src/docx_mcp_server/core/session.py`
2. 添加字段：`_is_dirty`, `_last_save_commit_index`, `_lock`
3. 实现方法：mark_dirty(), has_unsaved_changes(), mark_saved()
4. 修改 `docx_save()` 调用 mark_saved()
5. 修改所有修改工具（docx_insert_*, docx_update_*, etc.）调用 mark_dirty()

**关键代码**（参考 design-revision-v2.md §3.2）:
```python
@dataclass
class Session:
    session_id: str
    document: Document
    # ... 其他字段 ...

    # ⭐ New fields
    _is_dirty: bool = False
    _last_save_commit_index: int = -1
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def mark_dirty(self):
        with self._lock:
            self._is_dirty = True

    def has_unsaved_changes(self) -> bool:
        with self._lock:
            return (
                self._is_dirty or
                len(self.history_stack) > self._last_save_commit_index + 1
            )

    def mark_saved(self):
        with self._lock:
            self._is_dirty = False
            self._last_save_commit_index = len(self.history_stack) - 1
```

**触发点修改**:
```python
# 在 docx_save() 中
def docx_save(session_id: str, file_path: str) -> str:
    # ... 保存逻辑 ...
    session.document.save(file_path)
    session.mark_saved()  # ⭐ 清除 dirty flag
    return create_success_response(...)

# 在所有修改工具中
def docx_insert_paragraph(session_id: str, text: str, position: str) -> str:
    # ... 插入逻辑 ...
    session.mark_dirty()  # ⭐ 标记为 dirty
    return create_context_aware_response(...)
```

**验收标准**:
- [ ] Session 类添加了 dirty tracking 字段和方法
- [ ] mark_saved() 在 docx_save() 中被调用
- [ ] mark_dirty() 在所有修改工具中被调用（约 20+ 处）
- [ ] has_unsaved_changes() 返回正确结果
- [ ] 单元测试通过（test_session_dirty_tracking.py）

**测试用例**:
```python
def test_dirty_flag_after_modification():
    session_id = docx_create()
    session = session_manager.get_session(session_id)

    # Initially clean
    assert not session.has_unsaved_changes()

    # Mark dirty
    session.mark_dirty()
    assert session.has_unsaved_changes()

    # Save clears dirty
    session.mark_saved()
    assert not session.has_unsaved_changes()

def test_dirty_flag_after_save():
    session_id = docx_create()
    docx_insert_paragraph(session_id, "Test", position="end:document_body")
    session = session_manager.get_session(session_id)

    # Should be dirty after insert
    assert session.has_unsaved_changes()

    # Save should clear dirty
    docx_save(session_id, "/tmp/test.docx")
    assert not session.has_unsaved_changes()
```

---

#### T-004: combined_server.py（FastAPI + MCP）⭐ 修订

**优先级**: P0
**复杂度**: Standard
**预计工时**: 4 小时（原 3 小时）
**依赖**: 无（仅需 import mcp）
**并行组**: 2a（与 T-003 并行）
**修订原因**: 正确的 FastMCP 集成架构（CI-1）

**描述**:
创建 FastAPI 主应用，挂载 MCP 服务器，实现正确的集成架构。

**实施步骤**:
1. 创建文件 `src/docx_mcp_server/combined_server.py`
2. 导入 FastAPI, uvicorn, mcp
3. 创建 FastAPI app 实例
4. 定义 Request/Response Pydantic 模型
5. 实现 /health 端点
6. 挂载 MCP: `app.mount("/mcp", mcp.get_asgi_app(path="/mcp"))`
7. 实现 run_combined_server() 函数

**关键代码**（参考 design-revision-v2.md §1.3）:
```python
from fastapi import FastAPI
from docx_mcp_server.server import mcp

app = FastAPI(
    title="Docx MCP Server",
    version="3.0.0"
)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "3.0.0",
        "transport": "http"
    }

# ⭐ Mount MCP at /mcp
app.mount("/mcp", mcp.get_asgi_app(path="/mcp"))

def run_combined_server(host: str = "127.0.0.1", port: int = 8080):
    import uvicorn
    uvicorn.run(app, host=host, port=port)
```

**验收标准**:
- [ ] FastAPI app 创建成功
- [ ] MCP 成功挂载到 /mcp 路径
- [ ] /health 端点可访问
- [ ] uvicorn 可启动服务器
- [ ] 集成测试通过（test_combined_server.py）

**测试用例**:
```python
from fastapi.testclient import TestClient
from docx_mcp_server.combined_server import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_mcp_mounted():
    # MCP endpoint should be accessible
    response = client.get("/mcp")
    # Should not return 404
    assert response.status_code != 404
```

---

#### T-005: HTTP API routes ⭐ 修订

**优先级**: P0
**复杂度**: Standard
**预计工时**: 4 小时（原 3 小时）
**依赖**: T-002, T-004
**并行组**: 无（串行，必须在 T-004 之后）
**修订原因**: 添加到 FastAPI app，而非独立 routes.py

**描述**:
在 combined_server.py 中添加 REST API 端点，调用 FileController。

**实施步骤**:
1. 在 `combined_server.py` 中添加 POST /api/file/switch 端点
2. 添加 GET /api/status 端点
3. 添加 POST /api/session/close 端点
4. 实现错误处理（捕获 FileNotFoundError, PermissionError, 等）
5. 添加 CORS 中间件（如需 web 客户端）

**关键代码**（参考 design-revision-v2.md §1.3）:
```python
from fastapi import HTTPException
from pydantic import BaseModel
from docx_mcp_server.api.file_controller import (
    FileController, FileLockError, UnsavedChangesError
)

class SwitchFileRequest(BaseModel):
    path: str
    force: bool = False

@app.post("/api/file/switch")
async def switch_file(request: SwitchFileRequest):
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
        raise HTTPException(status_code=409, detail={
            "error": "Unsaved changes exist",
            "currentFile": FileController.get_status()["currentFile"],
            "message": "Call with force=true to discard changes"
        })
```

**验收标准**:
- [ ] /api/file/switch 端点实现并返回正确响应
- [ ] /api/status 端点实现并返回正确响应
- [ ] /api/session/close 端点实现并返回正确响应
- [ ] 错误返回正确的 HTTP 状态码（404/403/423/409）
- [ ] 集成测试通过（test_api_routes.py）

**测试用例**:
```python
def test_switch_file_success(test_file_path):
    response = client.post("/api/file/switch", json={
        "path": test_file_path,
        "force": False
    })
    assert response.status_code == 200
    data = response.json()
    assert data["currentFile"] == test_file_path

def test_switch_file_not_found():
    response = client.post("/api/file/switch", json={
        "path": "/nonexistent.docx",
        "force": False
    })
    assert response.status_code == 404

def test_get_status():
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "currentFile" in data
    assert "sessionId" in data
```

---

#### T-006: __main__.py (添加 combined 模式)

**优先级**: P0
**复杂度**: Simple
**预计工时**: 1 小时
**依赖**: T-005
**并行组**: 无（串行，必须在 T-005 之后）

**描述**:
修改主入口文件，添加 `--transport combined` 选项。

**实施步骤**:
1. 修改文件 `src/docx_mcp_server/__main__.py`
2. 添加 `--transport` 选项：choices 增加 "combined"
3. 添加 `--file` 参数（用于 CLI 模式）
4. 添加条件分支：if args.transport == "combined"
5. 导入并调用 run_combined_server()

**关键代码**（参考 design-revision-v2.md §1.4）:
```python
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--transport",
                        choices=["stdio", "sse", "streamable-http", "combined"],
                        default="stdio")
    parser.add_argument("--file", help="Default active file path")
    # ... 其他参数 ...

    args = parser.parse_args()

    # Set initial active file from CLI
    if args.file:
        from docx_mcp_server.core.global_state import global_state
        global_state.active_file = args.file

    if args.transport == "combined":
        from docx_mcp_server.combined_server import run_combined_server
        run_combined_server(host=args.host, port=args.port)
    elif args.transport == "stdio":
        mcp.run(transport="stdio")
    # ... 其他模式 ...
```

**验收标准**:
- [ ] `--transport combined` 参数可用
- [ ] `--file` 参数可设置初始活跃文件
- [ ] 启动 combined 模式成功
- [ ] 手动测试启动命令有效

**测试**:
```bash
# 手动测试
mcp-server-docx --transport combined --port 8080
curl http://localhost:8080/health
# 应返回 {"status": "healthy", ...}
```

---

### Phase 3: Launcher 端（并行）

#### T-007: HTTPClient（带重试）⭐ 修订

**优先级**: P0
**复杂度**: Standard
**预计工时**: 3 小时（原 2 小时）
**依赖**: 无
**并行组**: 3（与 T-008, T-009, T-010 并行）
**修订原因**: 添加重试逻辑（IA-2）

**描述**:
实现带重试机制的 HTTP 客户端，提高 Launcher 的鲁棒性。

**实施步骤**:
1. 修改文件 `src/launcher/http_client.py`
2. 导入 requests, urllib3.util.retry
3. 配置 Retry 策略（total=3, backoff_factor=0.5）
4. 创建 HTTPAdapter 并挂载到 session
5. 实现 get(), post() 方法
6. 添加自定义异常：ServerConnectionError, ServerTimeoutError

**关键代码**（参考 design-revision-v2.md §6.1）:
```python
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class HTTPClient:
    def __init__(self, base_url: str, timeout: float = 5.0, max_retries: int = 3):
        self.session = requests.Session()

        # ⭐ Configure retry
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount('http://', adapter)

    def post(self, path: str, data: dict) -> dict:
        try:
            response = self.session.post(f"{self.base_url}{path}", json=data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.ConnectionError:
            raise ServerConnectionError(...)
```

**验收标准**:
- [ ] HTTPClient 类实现完整
- [ ] 重试策略配置正确（3 次重试，指数退避）
- [ ] 错误返回自定义异常
- [ ] 单元测试通过（test_http_client_retry.py）

**测试用例**:
```python
def test_retry_on_500(monkeypatch):
    call_count = 0

    def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise requests.exceptions.HTTPError(response=Mock(status_code=500))
        return Mock(status_code=200, json=lambda: {"ok": True})

    monkeypatch.setattr("requests.Session.post", mock_post)

    client = HTTPClient("http://localhost:8080")
    result = client.post("/api/status", {})

    # Should retry 2 times, succeed on 3rd
    assert call_count == 3
    assert result["ok"] is True
```

---

#### T-008: 文件选择 UI

**优先级**: P0
**复杂度**: Standard
**预计工时**: 4 小时
**依赖**: 无
**并行组**: 3（与 T-007, T-009, T-010 并行）

**描述**:
实现 Launcher 的文件选择功能（浏览器、最近文件、拖拽、路径输入）。

**实施步骤**:
1. 修改文件 `src/launcher/main_window.py`
2. 添加文件浏览按钮（QFileDialog）
3. 添加最近文件列表（QListWidget）
4. 实现拖拽支持（setAcceptDrops, dragEnterEvent, dropEvent）
5. 添加路径输入框（QLineEdit + 自动补全）
6. 连接信号：文件选择 → 调用 HTTPClient.post("/api/file/switch")

**验收标准**:
- [ ] 文件浏览器可打开并过滤 .docx 文件
- [ ] 最近文件列表显示并可点击切换
- [ ] 拖拽 .docx 文件可自动切换
- [ ] 路径输入框支持自动补全
- [ ] 手动测试所有交互功能正常

---

#### T-009: 状态轮询

**优先级**: P0
**复杂度**: Simple
**预计工时**: 2 小时
**依赖**: T-007
**并行组**: 3（与 T-007, T-008, T-010 并行）

**描述**:
实现 Launcher 的状态轮询，定期调用 GET /api/status 更新 UI。

**实施步骤**:
1. 在 `main_window.py` 中创建 QTimer
2. 连接 timeout 信号到 update_status() 方法
3. 实现 update_status()：调用 http_client.get("/api/status")
4. 解析响应，更新 UI（当前文件名、保存状态）
5. 设置轮询间隔（2 秒）

**验收标准**:
- [ ] QTimer 启动并定期触发
- [ ] 状态更新调用 API 成功
- [ ] UI 显示正确的文件名和保存状态
- [ ] 手动测试状态同步正确

---

#### T-010: Launcher 健康检查 ⭐ 新增

**优先级**: P1
**复杂度**: Simple
**预计工时**: 2 小时
**依赖**: T-007
**并行组**: 3（与 T-007, T-008, T-009 并行）
**新增原因**: 启动时验证服务器可用性（IA-3）

**描述**:
在 Launcher 启动时调用 /health 端点，验证服务器可用和版本兼容。

**实施步骤**:
1. 在 `main_window.py.__init__()` 中添加健康检查
2. 调用 http_client.get("/health")
3. 检查返回的 version 字段（必须是 3.x）
4. 检查 transport 字段（必须是 "http"）
5. 如失败，显示错误对话框并禁用 UI

**关键代码**（参考 design-revision-v2.md §7.1）:
```python
def _verify_server_health(self) -> tuple[bool, str]:
    try:
        health = self.http_client.get("/health")
        server_version = health.get("version", "unknown")

        if not server_version.startswith("3."):
            return False, f"Incompatible server version: {server_version}"

        return True, f"Connected to server v{server_version}"
    except ServerConnectionError:
        return False, "Cannot connect to server"
```

**验收标准**:
- [ ] 健康检查在启动时执行
- [ ] 版本不兼容时显示错误对话框
- [ ] 连接失败时显示错误对话框
- [ ] 测试通过（test_launcher_health_check.py）

---

### Phase 4: Breaking Change（串行）

#### T-011: 移除 docx_list_files, docx_create_file

**优先级**: P0
**复杂度**: Simple
**预计工时**: 1 小时
**依赖**: T-006（Server 端就绪）
**并行组**: 无（串行）

**描述**:
删除旧的文件管理接口。

**实施步骤**:
1. 删除 `src/docx_mcp_server/tools/content_tools.py` 中的 docx_list_files()
2. 删除 `src/docx_mcp_server/tools/content_tools.py` 中的 docx_create_file()
3. 从 __init__.py 中移除注册
4. 删除相关单元测试

**验收标准**:
- [ ] docx_list_files, docx_create_file 不存在于代码中
- [ ] MCP tools 列表中不包含这两个工具
- [ ] 相关测试已删除

---

#### T-012: 修改 docx_create()（移除 file_path 参数）⭐ 关键

**优先级**: P0
**复杂度**: Standard
**预计工时**: 3 小时
**依赖**: T-011
**并行组**: 无（串行）

**描述**:
修改 docx_create() 工具，移除 file_path 参数，改为使用 global_state.active_file。

**实施步骤**:
1. 修改文件 `src/docx_mcp_server/tools/session_tools.py`
2. 修改 docx_create() 函数签名：移除 file_path 参数
3. 添加检查：if not global_state.active_file: return error
4. 使用 global_state.active_file 创建 session
5. 更新 docstring 和错误消息

**关键代码**（参考 design-revision-v2.md §4.2）:
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

    session = session_manager.create_session(global_state.active_file)
    global_state.active_session_id = session.session_id

    return create_success_response(
        f"Session created for {global_state.active_file}",
        session_id=session.session_id
    )
```

**验收标准**:
- [ ] docx_create() 不再接受 file_path 参数
- [ ] 无 active_file 时返回错误
- [ ] 成功创建 session 并设置 active_session_id
- [ ] 单元测试更新并通过

---

#### T-013: 添加 --file CLI 参数

**优先级**: P0
**复杂度**: Simple
**预计工时**: 1 小时
**依赖**: T-012
**并行组**: 无（串行）

**描述**:
支持通过 CLI 参数设置初始活跃文件（已在 T-006 中部分实现，此任务补充测试和文档）。

**实施步骤**:
1. 验证 T-006 中的 --file 参数实现
2. 添加路径验证（调用 validate_path_safety）
3. 添加文件存在性检查
4. 更新帮助文本
5. 编写 CLI 测试

**验收标准**:
- [ ] `mcp-server-docx --file /path/to/doc.docx` 可正常启动
- [ ] 文件不存在时显示错误并退出
- [ ] 文件路径被设置到 global_state.active_file
- [ ] CLI 帮助文本准确

---

#### T-014 ~ T-018: 测试和文档更新

**这5个任务都是串行的，依赖于 T-013**

#### T-014: 更新单元测试 ⭐ 关键

**优先级**: P0
**复杂度**: Standard
**预计工时**: 4 小时
**依赖**: T-013
**并行组**: 无（串行）

**描述**:
更新所有使用 docx_create(file_path) 的单元测试。

**实施步骤**:
1. 搜索所有测试文件：`grep -r "docx_create(" tests/unit/ --include="*.py"`
2. 逐个修改，使用 global_state.set_active_file() 代替
3. 确保测试 setup/teardown 清理 global_state
4. 运行所有单元测试并修复失败

**预期影响**:
- 约 15-20 个测试文件需要修改
- 每个文件约 2-5 处修改点

**验收标准**:
- [ ] 所有单元测试通过
- [ ] 无 docx_create(file_path) 调用残留
- [ ] 测试 teardown 清理 global_state

---

#### T-015: 更新 E2E 测试 ⭐ 关键

**优先级**: P0
**复杂度**: Standard
**预计工时**: 3 小时
**依赖**: T-014
**并行组**: 无（串行）

**描述**:
更新 E2E 测试，使用新架构。

**实施步骤**:
1. 搜索 E2E 测试：`grep -r "docx_create(" tests/e2e/ --include="*.py"`
2. 修改测试 setup，先调用 API 设置 active_file 或使用 global_state
3. 运行所有 E2E 测试并修复失败

**验收标准**:
- [ ] 所有 E2E 测试通过
- [ ] 测试覆盖新的文件切换流程

---

#### T-016: 更新 README.md ⭐ 关键

**优先级**: P0
**复杂度**: Simple
**预计工时**: 2 小时
**依赖**: T-015
**并行组**: 无（串行）

**描述**:
更新 README.md，移除旧示例，添加新架构说明。

**实施步骤**:
1. 搜索 README.md 中的 docx_create(file_path) 示例
2. 替换为新的使用方式（Launcher 或 --file）
3. 添加 Transport Modes 说明（STDIO vs Combined）
4. 添加 Breaking Changes 警告

**验收标准**:
- [ ] 所有示例代码使用新 API
- [ ] 添加了迁移指南链接
- [ ] 文档清晰易懂

---

#### T-017: 更新 CLAUDE.md ⭐ 关键

**优先级**: P0
**复杂度**: Simple
**预计工时**: 2 小时
**依赖**: T-016
**并行组**: 无（串行）

**描述**:
更新 CLAUDE.md（Claude 的开发指南），反映新架构。

**实施步骤**:
1. 更新"常用工具组合"部分的示例
2. 添加全局单文件模式说明
3. 更新"快速参考"部分
4. 添加 HTTP API 使用说明

**验收标准**:
- [ ] 所有示例使用新 API
- [ ] 文档与代码实现一致

---

#### T-018: 创建迁移指南 ⭐ 关键

**优先级**: P0
**复杂度**: Standard
**预计工时**: 3 小时
**依赖**: T-017
**并行组**: 无（串行）

**描述**:
创建 v2 → v3 迁移指南，帮助用户升级。

**实施步骤**:
1. 创建文件 `docs/migration-v2-to-v3.md`
2. 列出所有 Breaking Changes
3. 提供代码对比示例（旧 vs 新）
4. 提供迁移检查清单
5. 添加常见问题 FAQ

**内容大纲**:
```markdown
# Migration Guide: v2.x → v3.0

## Breaking Changes

### 1. Removed Interfaces
- ❌ `docx_list_files(directory)` - REMOVED
- ❌ `docx_create_file(file_path)` - REMOVED
- ❌ `docx_create(file_path)` - Parameter removed

### 2. New File Management Flow

**Before (v2.x)**:
```python
session_id = docx_create(file_path="/path/to/doc.docx")
```

**After (v3.0)**:
```python
# Option 1: Use Launcher (GUI)
# 1. Start server: mcp-server-docx --transport combined --port 8080
# 2. Open Launcher, select file
# 3. Claude calls: docx_create()

# Option 2: CLI mode
# 1. Start server: mcp-server-docx --file /path/to/doc.docx
# 2. Claude calls: docx_create()
```

## Migration Checklist
- [ ] Update server startup command to use --transport combined or --file
- [ ] Update all docx_create() calls (remove file_path parameter)
- [ ] Install Launcher if using GUI mode
...
```

**验收标准**:
- [ ] 迁移指南完整、准确
- [ ] 包含代码示例
- [ ] 用户可据此顺利迁移

---

### Phase 5: 安全增强（并行）

#### T-019: 路径验证增强 ⭐ 新增

**优先级**: P0
**复杂度**: Simple
**预计工时**: 2 小时
**依赖**: T-002
**并行组**: 5（与 T-020 并行）
**新增原因**: 安全性增强（IA-5）

**描述**:
实现增强的路径验证函数，防止路径遍历攻击。

**实施步骤**:
1. 创建文件 `src/docx_mcp_server/core/validators.py`
2. 实现 validate_path_safety() 函数
3. 在 FileController.switch_file() 中调用
4. 编写安全测试用例

**关键代码**（参考 design-revision-v2.md §9.1）:
```python
def validate_path_safety(file_path: str) -> str:
    # 1. Expand and normalize
    abs_path = os.path.abspath(os.path.expanduser(file_path))

    # 2. Validate extension
    if not abs_path.lower().endswith('.docx'):
        raise ValueError("Only .docx files allowed")

    # 3. Check suspicious patterns
    if ".." in abs_path:
        raise ValueError("Suspicious path pattern")

    return abs_path
```

**验收标准**:
- [ ] 函数实现完整
- [ ] 拒绝非 .docx 文件
- [ ] 拒绝路径遍历尝试
- [ ] 安全测试通过

---

#### T-020: 依赖声明更新 ⭐ 新增

**优先级**: P0
**复杂度**: Simple
**预计工时**: 1 小时
**依赖**: 无
**并行组**: 5（与 T-019 并行）
**新增原因**: 添加缺失的依赖（CI-2）

**描述**:
更新 pyproject.toml，添加 FastAPI 相关依赖。

**实施步骤**:
1. 修改 `pyproject.toml`
2. 添加 dependencies: fastapi, uvicorn, pydantic, requests
3. 更新 version 为 3.0.0
4. 运行 `uv pip install -e .` 验证

**验收标准**:
- [ ] 所有新依赖已声明
- [ ] version bump 到 3.0.0
- [ ] uv pip install 成功

---

### Phase 6: 新增测试（并行）

#### T-021 ~ T-025: 新增测试任务

这5个任务都是新增的，用于验证新功能和修正。

#### T-021: GlobalState 并发测试 ⭐ 新增

**优先级**: P1
**复杂度**: Standard
**预计工时**: 2 小时
**依赖**: T-001
**并行组**: 6（5个任务并行）

**描述**:
测试 GlobalState 的线程安全性。

**测试用例**:
```python
import threading

def test_concurrent_writes():
    def writer(thread_id):
        for i in range(100):
            global_state.active_file = f"/file_{thread_id}_{i}.docx"

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Should not crash or corrupt data
    assert global_state.active_file is not None
```

**验收标准**:
- [ ] 并发测试通过，无竞态条件
- [ ] 无数据损坏

---

#### T-022: HTTPClient 重试测试 ⭐ 新增

**优先级**: P1
**复杂度**: Standard
**预计工时**: 2 小时
**依赖**: T-007
**并行组**: 6

**描述**:
测试 HTTPClient 的重试逻辑。

**测试用例**:
```python
def test_retry_on_500(monkeypatch):
    call_count = 0

    def mock_request(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise requests.HTTPError(response=Mock(status_code=500))
        return Mock(status_code=200, json=lambda: {"ok": True})

    monkeypatch.setattr("requests.Session.request", mock_request)

    client = HTTPClient("http://localhost:8080")
    result = client.get("/api/status")

    assert call_count == 3  # Retried twice, succeeded on 3rd
```

**验收标准**:
- [ ] 重试测试通过
- [ ] 指数退避验证正确

---

#### T-023: Combined server 集成测试 ⭐ 新增

**优先级**: P1
**复杂度**: Standard
**预计工时**: 3 小时
**依赖**: T-005
**并行组**: 6

**描述**:
端到端测试 FastAPI + MCP 集成。

**测试用例**:
```python
from fastapi.testclient import TestClient

def test_combined_endpoints():
    # Test REST API
    response = client.post("/api/file/switch", json={"path": "/test.docx"})
    assert response.status_code == 200

    # Test MCP endpoint
    response = client.get("/mcp")
    assert response.status_code != 404
```

**验收标准**:
- [ ] REST API 端点可访问
- [ ] MCP 端点可访问
- [ ] 两者互不干扰

---

#### T-024: Launcher 健康检查测试

**优先级**: P2
**复杂度**: Simple
**预计工时**: 1 小时
**依赖**: T-010
**并行组**: 6

**描述**:
测试 Launcher 启动时的健康检查。

**验收标准**:
- [ ] 服务器不可用时显示错误
- [ ] 版本不兼容时显示错误
- [ ] 健康检查通过时正常启动

---

#### T-025: Path validation 安全测试

**优先级**: P2
**复杂度**: Simple
**预计工时**: 1 小时
**依赖**: T-019
**并行组**: 6

**描述**:
测试路径验证的安全性。

**测试用例**:
```python
def test_reject_path_traversal():
    with pytest.raises(ValueError):
        validate_path_safety("../../etc/passwd.docx")

def test_reject_non_docx():
    with pytest.raises(ValueError):
        validate_path_safety("/path/to/malware.exe")
```

**验收标准**:
- [ ] 拒绝路径遍历
- [ ] 拒绝非 .docx 文件
- [ ] 正常路径通过

---

## 3. 并行执行计划

### 3.1 并行分组汇总

| Group | 任务 | 预计时间 | 可并行执行 |
|-------|------|---------|-----------|
| Phase 1 (串行) | T-001, T-002 | 7h | ❌ 必须串行 |
| Group 2a | T-003, T-004 | 4h | ✅ 并行执行 |
| Sequential after 2a | T-005, T-006 | 5h | ❌ 必须串行 |
| Group 3 | T-007, T-008, T-009, T-010 | 4h | ✅ 并行执行 |
| Phase 4 (串行) | T-011 ~ T-018 | 17h | ❌ 必须串行 |
| Group 5 | T-019, T-020 | 2h | ✅ 并行执行 |
| Group 6 | T-021 ~ T-025 | 3h | ✅ 并行执行 |

**总预计时间**（串行执行）: ~42 小时
**并行优化后时间**: ~35 小时（节省 ~17%）

### 3.2 关键路径

```
Critical Path (最长路径):
T-001 (3h) → T-002 (4h) → T-005 (4h) → T-006 (1h) → T-011~T-018 (17h)
= 29 小时（关键路径）

Non-Critical Paths (可并行):
- T-003 (3h) - 并行于 T-004
- T-007~T-010 (最长 4h) - 并行执行
- T-019, T-020 (2h) - 并行执行
- T-021~T-025 (3h) - 并行执行
```

---

## 4. 风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| FastMCP 集成失败 | 低 | 高 | 已验证官方文档，架构正确 |
| Breaking Change 迁移复杂 | 中 | 中 | 提供详细迁移指南（T-018）|
| 线程安全 bug | 低 | 高 | 添加并发测试（T-021）|
| 测试更新遗漏 | 中 | 中 | 系统性搜索和清单检查（T-014, T-015）|
| 文档过时 | 中 | 低 | 强制更新 README/CLAUDE.md（T-016, T-017）|

---

## 5. 验收标准汇总

### 5.1 功能验收

- [ ] F-001: Server 全局单文件状态正常工作
- [ ] F-002: docx_create() 无参数可用
- [ ] F-003: docx_create(path) 返回错误
- [ ] F-004: POST /api/file/switch 所有场景正常
- [ ] F-005: GET /api/status 返回正确状态
- [ ] F-006: CLI --file 启动正常
- [ ] F-007 ~ F-010: Launcher UI 功能完整
- [ ] F-011 ~ F-012: 未保存修改警告正常
- [ ] F-013 ~ F-015: 错误处理正确
- [ ] F-016: 旧接口完全移除

### 5.2 测试验收

- [ ] 所有单元测试通过（包括新增的 5 个测试任务）
- [ ] 所有 E2E 测试通过
- [ ] 并发测试通过
- [ ] 安全测试通过

### 5.3 文档验收

- [ ] README.md 更新完整
- [ ] CLAUDE.md 更新完整
- [ ] 迁移指南清晰易懂
- [ ] pyproject.toml 依赖完整

---

## 6. 预计里程碑

| 里程碑 | 任务范围 | 预计完成 | 交付物 |
|--------|---------|---------|--------|
| M1: Server 基础设施 | T-001 ~ T-006 | Day 3 | GlobalState, FileController, HTTP API |
| M2: Launcher 集成 | T-007 ~ T-010 | Day 5 | 文件选择 UI, 状态轮询 |
| M3: Breaking Change | T-011 ~ T-018 | Day 8 | 旧接口移除, 迁移指南 |
| M4: 测试与发布 | T-019 ~ T-025 | Day 10 | 完整测试覆盖, v3.0 发布 |

---

**文档版本**: v2 (Revision)
**修订时间**: 2026-01-26
**修订者**: Task Planner
**状态**: Ready for Execution
