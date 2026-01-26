---
feature: http-file-management
complexity: complex
version: 1
generated_at: 2026-01-26
---

# 任务拆分文档: HTTP File Management

> **功能标识**: http-file-management
> **复杂度**: complex
> **版本**: v1
> **生成时间**: 2026-01-26

## 1. 任务概览

### 1.1 任务统计

- **总任务数**: 15
- **P0 任务**: 11
- **P1 任务**: 4
- **并行组数**: 3

### 1.2 依赖关系图

```
Phase 1: Server 核心重构 (并行组 1)
├─ T-001: 创建 Global State Manager
├─ T-002: 创建 File Controller
└─ T-003: 修改 Session Manager

Phase 2: HTTP API 实现 (依赖 Phase 1)
├─ T-004: 实现 HTTP API Routes
├─ T-005: 集成 FastAPI/fastmcp
└─ T-006: 实现错误处理

Phase 3: MCP Tools 重构 (依赖 Phase 1)
├─ T-007: 修改 docx_create() 工具
├─ T-008: 移除旧文件管理接口
└─ T-009: 添加 CLI --file 参数

Phase 4: Launcher 集成 (并行组 2, 依赖 Phase 2)
├─ T-010: 创建 HTTP Client
├─ T-011: 修改 Launcher Window
└─ T-012: 实现状态轮询

Phase 5: 测试与文档 (并行组 3, 依赖 Phase 3, 4)
├─ T-013: 编写单元测试
├─ T-014: 编写集成测试
└─ T-015: 更新文档和迁移指南
```

---

## 2. 任务详情

### Phase 1: Server 核心重构

#### T-001: 创建 Global State Manager

**优先级**: P0
**复杂度**: Simple
**预计工时**: 2 小时
**依赖**: 无
**并行组**: 1

**描述**:
创建全局状态管理器，维护 active_file 和 active_session_id。

**实施步骤**:
1. 创建文件 `src/docx_mcp_server/core/global_state.py`
2. 实现 GlobalState 类（dataclass）
3. 添加方法：set_active_file(), clear_active_file(), set_active_session(), get_status()
4. 创建全局单例 global_state
5. 添加日志记录

**验收标准**:
- [ ] GlobalState 类实现完整
- [ ] 全局单例可导入使用
- [ ] 状态变更有日志记录
- [ ] 单元测试通过（test_global_state.py）

**测试用例**:
```python
def test_set_active_file():
    global_state.set_active_file("/path/to/doc.docx")
    assert global_state.active_file == "/path/to/doc.docx"

def test_clear_active_file():
    global_state.set_active_file("/path/to/doc.docx")
    global_state.clear_active_file()
    assert global_state.active_file is None
    assert global_state.active_session_id is None
```

---

#### T-002: 创建 File Controller

**优先级**: P0
**复杂度**: Complex
**预计工时**: 6 小时
**依赖**: T-001
**并行组**: 1

**描述**:
实现文件切换逻辑，包括完整性检查、session 管理、错误处理。

**实施步骤**:
1. 创建文件 `src/docx_mcp_server/api/file_controller.py`
2. 实现 FileController 类
3. 实现 switch_file() 方法：
   - 路径安全验证
   - 文件存在性检查
   - 权限检查
   - 文件锁定检查
   - 未保存修改检查
   - Session 关闭逻辑
4. 实现 get_status() 方法
5. 实现 close_session() 方法
6. 定义自定义异常：FileLockError, UnsavedChangesError

**验收标准**:
- [ ] switch_file() 实现所有检查逻辑
- [ ] 错误场景正确抛出异常（404/403/423/409）
- [ ] get_status() 返回正确状态
- [ ] close_session() 支持 save 参数
- [ ] 单元测试覆盖所有场景

**测试用例**:
```python
def test_switch_file_success():
    result = FileController.switch_file("/path/to/doc.docx")
    assert result["currentFile"] == "/path/to/doc.docx"

def test_switch_file_not_found():
    with pytest.raises(FileNotFoundError):
        FileController.switch_file("/nonexistent.docx")

def test_switch_file_unsaved_changes():
    # Setup session with changes
    with pytest.raises(UnsavedChangesError):
        FileController.switch_file("/new.docx", force=False)
```

---

#### T-003: 修改 Session Manager

**优先级**: P0
**复杂度**: Standard
**预计工时**: 3 小时
**依赖**: 无
**并行组**: 1

**描述**:
为 Session Manager 添加未保存修改追踪功能。

**实施步骤**:
1. 修改 `src/docx_mcp_server/core/session.py`
2. 添加方法 has_unsaved_changes() → bool
3. 实现逻辑：检查 history_stack 是否为空
4. 在 save() 方法中清空 history_stack
5. 更新相关文档字符串

**验收标准**:
- [ ] has_unsaved_changes() 方法实现
- [ ] save() 后 has_unsaved_changes() 返回 False
- [ ] 单元测试通过

**测试用例**:
```python
def test_has_unsaved_changes():
    session = Session(...)
    assert not session.has_unsaved_changes()

    # Simulate change
    session.history_stack.append(Commit())
    assert session.has_unsaved_changes()

    # Save
    session.document.save("test.docx")
    assert not session.has_unsaved_changes()
```

---

### Phase 2: HTTP API 实现

#### T-004: 实现 HTTP API Routes

**优先级**: P0
**复杂度**: Standard
**预计工时**: 4 小时
**依赖**: T-002
**并行组**: 无（串行）

**描述**:
使用 FastAPI 实现 HTTP API 端点。

**实施步骤**:
1. 创建文件 `src/docx_mcp_server/api/routes.py`
2. 定义 Pydantic models：SwitchFileRequest, CloseSessionRequest
3. 实现路由：
   - POST /api/file/switch
   - GET /api/status
   - POST /api/session/close
4. 异常到 HTTP 状态码的映射
5. 添加请求/响应日志

**验收标准**:
- [ ] 所有 API 端点实现
- [ ] Pydantic 验证正常工作
- [ ] 错误响应格式正确（404/403/423/409）
- [ ] 集成测试通过

**测试用例**:
```python
def test_api_switch_file(client):
    response = client.post("/api/file/switch", json={
        "path": "/path/to/doc.docx",
        "force": False
    })
    assert response.status_code == 200

def test_api_switch_file_not_found(client):
    response = client.post("/api/file/switch", json={
        "path": "/nonexistent.docx"
    })
    assert response.status_code == 404
```

---

#### T-005: 集成 FastAPI/fastmcp

**优先级**: P0
**复杂度**: Standard
**预计工时**: 4 小时
**依赖**: T-004
**并行组**: 无（串行）

**描述**:
将 FastAPI 路由集成到 MCP Server 中。

**实施步骤**:
1. 研究 fastmcp 的 HTTP 能力
2. 修改 `src/docx_mcp_server/server.py`
3. 注册 FastAPI router
4. 配置 CORS（如需要）
5. 测试 HTTP 服务器启动

**验收标准**:
- [ ] HTTP 服务器正常启动
- [ ] API 端点可访问
- [ ] MCP tools 和 HTTP API 共存
- [ ] 启动日志显示 HTTP 端口

**测试用例**:
```bash
# 启动服务器
uv run mcp-server-docx --transport sse --port 8080

# 测试 API
curl http://localhost:8080/api/status
```

---

#### T-006: 实现错误处理

**优先级**: P0
**复杂度**: Simple
**预计工时**: 2 小时
**依赖**: T-004
**并行组**: 无（串行）

**描述**:
统一错误处理和响应格式。

**实施步骤**:
1. 在 routes.py 中添加异常处理器
2. 确保所有错误返回一致的 JSON 格式
3. 添加错误日志记录
4. 测试所有错误场景

**验收标准**:
- [ ] 所有错误返回 JSON 格式
- [ ] 错误日志完整
- [ ] 错误响应包含 detail 字段
- [ ] 集成测试覆盖所有错误场景

---

### Phase 3: MCP Tools 重构

#### T-007: 修改 docx_create() 工具

**优先级**: P0
**复杂度**: Standard
**预计工时**: 3 小时
**依赖**: T-001
**并行组**: 无（串行）

**描述**:
移除 docx_create() 的 file_path 参数，改为使用 global_state.active_file。

**实施步骤**:
1. 修改 `src/docx_mcp_server/tools/session_tools.py`
2. 移除 file_path 参数
3. 添加 active_file 检查逻辑
4. 如果 active_file 为 None，返回错误
5. 创建 session 后更新 global_state.active_session_id
6. 更新文档字符串

**验收标准**:
- [ ] docx_create() 无参数
- [ ] active_file 为 None 时返回错误
- [ ] 成功创建 session 并更新 global_state
- [ ] 单元测试通过

**测试用例**:
```python
def test_docx_create_no_active_file():
    global_state.clear_active_file()
    result = docx_create()
    assert "error" in result.lower()

def test_docx_create_with_active_file():
    global_state.set_active_file("test.docx")
    result = docx_create()
    assert "session" in result.lower()
```

---

#### T-008: 移除旧文件管理接口

**优先级**: P0
**复杂度**: Simple
**预计工时**: 2 小时
**依赖**: T-007
**并行组**: 无（串行）

**描述**:
移除 docx_list_files 和 docx_create_file 工具。

**实施步骤**:
1. 从 `src/docx_mcp_server/tools/content_tools.py` 删除 docx_list_files
2. 删除 docx_create_file（如存在）
3. 从 `src/docx_mcp_server/server.py` 移除导出
4. 搜索并移除所有引用
5. 更新工具注册逻辑

**验收标准**:
- [ ] docx_list_files 完全移除
- [ ] docx_create_file 完全移除
- [ ] 代码库中无残留引用
- [ ] MCP tools 列表不包含这两个工具

**测试用例**:
```bash
# 搜索残留引用
grep -r "docx_list_files" src/
grep -r "docx_create_file" src/
# 应该无结果
```

---

#### T-009: 添加 CLI --file 参数

**优先级**: P1
**复杂度**: Simple
**预计工时**: 2 小时
**依赖**: T-001
**并行组**: 无（串行）

**描述**:
支持通过 CLI 参数设置 active_file。

**实施步骤**:
1. 修改 `src/docx_mcp_server/server.py` 的 main() 函数
2. 添加 --file 参数到 argparse
3. 启动时检查 --file 参数
4. 如果提供，验证文件存在性并设置 active_file
5. 添加日志记录

**验收标准**:
- [ ] --file 参数可用
- [ ] 文件不存在时退出并显示错误
- [ ] 文件存在时正确设置 active_file
- [ ] 启动日志显示 active_file

**测试用例**:
```bash
# 测试有效文件
uv run mcp-server-docx --file test.docx
# 应该启动成功

# 测试无效文件
uv run mcp-server-docx --file nonexistent.docx
# 应该退出并显示错误
```

---

### Phase 4: Launcher 集成

#### T-010: 创建 HTTP Client

**优先级**: P0
**复杂度**: Standard
**预计工时**: 3 小时
**依赖**: T-004
**并行组**: 2

**描述**:
创建 Launcher 的 HTTP 客户端，用于与 Server 通信。

**实施步骤**:
1. 创建文件 `src/docx_server_launcher/core/http_client.py`
2. 实现 HTTPClient 类
3. 实现方法：
   - switch_file(path, force)
   - get_status()
   - close_session(save)
4. 异常映射（404→FileNotFoundError, 409→UnsavedChangesError）
5. 添加超时和重试逻辑

**验收标准**:
- [ ] HTTPClient 类实现完整
- [ ] 所有方法正常工作
- [ ] 异常映射正确
- [ ] 单元测试通过（mock HTTP）

**测试用例**:
```python
def test_http_client_switch_file(mock_requests):
    client = HTTPClient()
    result = client.switch_file("/path/to/doc.docx")
    assert result["currentFile"] == "/path/to/doc.docx"

def test_http_client_unsaved_changes(mock_requests):
    mock_requests.post.return_value.status_code = 409
    client = HTTPClient()
    with pytest.raises(UnsavedChangesError):
        client.switch_file("/new.docx")
```

---

#### T-011: 修改 Launcher Window

**优先级**: P0
**复杂度**: Complex
**预计工时**: 6 小时
**依赖**: T-010
**并行组**: 2

**描述**:
修改 Launcher UI，集成文件切换和状态显示功能。

**实施步骤**:
1. 修改 `src/docx_server_launcher/gui/launcher_window.py`
2. 添加 HTTPClient 实例
3. 实现 switch_file() 方法
4. 实现 show_unsaved_dialog() 对话框
5. 更新 UI 状态显示
6. 添加错误提示（QMessageBox）

**验收标准**:
- [ ] 文件选择后调用 API
- [ ] 未保存修改时显示对话框
- [ ] 错误场景显示友好提示
- [ ] UI 状态实时更新
- [ ] 手动测试通过

**测试用例**:
```python
# 手动测试清单
- [ ] 选择文件成功切换
- [ ] 未保存修改时显示对话框
- [ ] 选择"保存并切换"正常工作
- [ ] 选择"丢弃并切换"正常工作
- [ ] 选择"取消"保持当前文件
- [ ] 文件不存在时显示错误
```

---

#### T-012: 实现状态轮询

**优先级**: P0
**复杂度**: Standard
**预计工时**: 3 小时
**依赖**: T-010
**并行组**: 2

**描述**:
实现 Launcher 的状态轮询机制，每 2 秒更新一次。

**实施步骤**:
1. 在 LauncherWindow 中添加 QTimer
2. 设置 2 秒间隔
3. 实现 update_status() 方法
4. 调用 http_client.get_status()
5. 更新 UI 状态栏
6. 添加错误处理（网络断开）

**验收标准**:
- [ ] 状态每 2 秒更新一次
- [ ] 状态栏显示正确信息
- [ ] 网络错误时显示友好提示
- [ ] 不阻塞主线程
- [ ] 手动测试通过

**测试用例**:
```python
# 手动测试清单
- [ ] 启动后状态栏显示"None"
- [ ] 选择文件后状态栏更新
- [ ] Claude 创建 session 后显示 session ID
- [ ] 修改文档后显示"Unsaved: Yes"
- [ ] 保存后显示"Unsaved: No"
```

---

### Phase 5: 测试与文档

#### T-013: 编写单元测试

**优先级**: P0
**复杂度**: Standard
**预计工时**: 4 小时
**依赖**: T-001, T-002, T-003, T-007
**并行组**: 3

**描述**:
为所有新增和修改的模块编写单元测试。

**实施步骤**:
1. 创建测试文件：
   - tests/unit/test_global_state.py
   - tests/unit/test_file_controller.py
   - tests/unit/test_session_manager.py
   - tests/unit/test_session_tools.py
2. 编写测试用例覆盖所有场景
3. 使用 pytest fixtures 简化测试
4. 确保测试覆盖率 > 80%

**验收标准**:
- [ ] 所有单元测试通过
- [ ] 测试覆盖率 > 80%
- [ ] 边界条件测试完整
- [ ] Mock 使用正确

---

#### T-014: 编写集成测试

**优先级**: P0
**复杂度**: Standard
**预计工时**: 4 小时
**依赖**: T-004, T-005, T-010, T-011
**并行组**: 3

**描述**:
编写 HTTP API 和 Launcher 集成测试。

**实施步骤**:
1. 创建测试文件：
   - tests/integration/test_api.py
   - tests/integration/test_launcher_integration.py
2. 使用 TestClient 测试 API
3. 测试完整工作流：
   - 文件选择 → API 调用 → docx_create() → 文档操作
4. 测试错误场景

**验收标准**:
- [ ] 所有集成测试通过
- [ ] 完整工作流测试通过
- [ ] 错误场景测试通过

---

#### T-015: 更新文档和迁移指南

**优先级**: P0
**复杂度**: Standard
**预计工时**: 4 小时
**依赖**: T-008
**并行组**: 3

**描述**:
更新所有相关文档，提供迁移指南。

**实施步骤**:
1. 更新 README.md：
   - 移除 docx_list_files, docx_create_file
   - 更新 docx_create() 说明
   - 添加 HTTP API 文档
2. 更新 CLAUDE.md：
   - 更新开发指南
   - 添加 HTTP API 章节
3. 更新 CHANGELOG.md：
   - 添加 v3.0.0 Breaking Changes
4. 创建 MIGRATION.md：
   - v2.x → v3.0 迁移步骤
   - 代码示例对比

**验收标准**:
- [ ] README.md 更新完整
- [ ] CLAUDE.md 更新完整
- [ ] CHANGELOG.md 包含 Breaking Changes
- [ ] MIGRATION.md 清晰易懂
- [ ] 所有示例代码可运行

---

## 3. 并行执行计划

### 并行组 1: Server 核心重构（Phase 1）

可并行执行：
- T-001: 创建 Global State Manager
- T-003: 修改 Session Manager

串行执行：
- T-002: 创建 File Controller（依赖 T-001）

### 并行组 2: Launcher 集成（Phase 4）

可并行执行（依赖 Phase 2 完成）：
- T-010: 创建 HTTP Client
- T-012: 实现状态轮询（依赖 T-010）

串行执行：
- T-011: 修改 Launcher Window（依赖 T-010）

### 并行组 3: 测试与文档（Phase 5）

可并行执行（依赖 Phase 3, 4 完成）：
- T-013: 编写单元测试
- T-014: 编写集成测试
- T-015: 更新文档和迁移指南

---

## 4. 风险与缓解

| 任务 | 风险 | 缓解措施 |
|------|------|----------|
| T-005 | fastmcp HTTP 能力不足 | 提前验证，准备 FastAPI 备选方案 |
| T-002 | 文件锁定检测不可靠 | 使用 best-effort 策略，添加用户提示 |
| T-011 | UI 复杂度高 | 分步实现，优先核心功能 |
| T-014 | 集成测试环境复杂 | 使用 Docker 或虚拟环境隔离 |

---

## 5. 验收清单

### 功能验收

- [ ] F-001: Server 全局单文件状态正常工作
- [ ] F-002: docx_create() 无参数正常工作
- [ ] F-003: docx_create(path) 报错
- [ ] F-004: POST /api/file/switch 正常工作
- [ ] F-005: GET /api/status 正常工作
- [ ] F-006: CLI --file 启动正常工作
- [ ] F-007: Launcher 文件浏览器正常工作
- [ ] F-008: Launcher 最近文件列表正常工作
- [ ] F-009: Launcher 拖拽支持正常工作
- [ ] F-010: Launcher 路径输入正常工作
- [ ] F-011: 未保存修改警告正常工作
- [ ] F-012: force=true 强制切换正常工作
- [ ] F-013: 文件不存在错误正常处理
- [ ] F-014: 文件锁定错误正常处理
- [ ] F-015: 权限不足错误正常处理
- [ ] F-016: 旧接口完全移除

### 测试验收

- [ ] 单元测试覆盖率 > 80%
- [ ] 所有集成测试通过
- [ ] 手动测试清单完成

### 文档验收

- [ ] README.md 更新完整
- [ ] CLAUDE.md 更新完整
- [ ] CHANGELOG.md 包含 Breaking Changes
- [ ] MIGRATION.md 清晰易懂

---

**文档版本**: v1
**最后更新**: 2026-01-26
**作者**: AI Architect
**审查状态**: Draft
