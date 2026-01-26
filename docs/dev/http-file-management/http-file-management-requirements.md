---
feature: http-file-management
complexity: complex
generated_by: clarify
generated_at: 2026-01-26T10:30:00Z
version: 1
---

# 需求文档: HTTP File Management

> **功能标识**: http-file-management
> **复杂度**: complex
> **生成方式**: clarify
> **生成时间**: 2026-01-26T10:30:00Z

## 1. 概述

### 1.1 一句话描述
重构 docx-mcp-server 的文件管理架构，从"Claude 主动选择文件"改为"Launcher 集中管理文件，Server 操作当前活跃文件"，通过 HTTP API 实现 Launcher 和 Server 的解耦通信。

### 1.2 核心价值
**问题**：
- 当前 `docx_list_files` 和 `docx_create_file` 接口导致 Claude 需要管理文件路径，增加交互复杂度
- 多 session 并发管理复杂，容易出现状态混乱
- Launcher 和 MCP Server 耦合，无法灵活切换文件

**价值**：
- **简化 Claude 交互**：Claude 无需知道文件路径，始终操作"当前文件"
- **职责分离**：Launcher 负责文件选择，Server 负责文档操作
- **架构清晰**：全局单文件模式，状态管理简单可靠
- **灵活性提升**：支持 Launcher UI 切换文件 + CLI 模式备选

### 1.3 目标用户
- **主要用户**：使用 docx-server-launcher 的交互式用户（通过 GUI 选择文件）
- **次要用户**：CLI 用户（通过 `--file` 参数直接指定文件）

---

## 2. 需求与用户故事

### 2.1 需求清单

| ID | 需求点 | 优先级 | 用户故事 |
|----|--------|--------|----------|
| R-001 | 移除文件管理接口 | P0 | As a developer, I want to remove `docx_list_files` and `docx_create_file`, so that Claude no longer manages file paths |
| R-002 | 全局活跃文件状态 | P0 | As a Server, I want to maintain a single "active file" state, so that all operations target the current file |
| R-003 | docx_create() 无参数 | P0 | As Claude, I want to call `docx_create()` without arguments, so that it automatically opens the active file |
| R-004 | HTTP 文件切换 API | P0 | As Launcher, I want to call `POST /api/file/switch {path, force}`, so that I can change the active file |
| R-005 | HTTP 状态查询 API | P0 | As Launcher, I want to call `GET /api/status`, so that I can display current file and session state |
| R-006 | CLI --file 参数 | P1 | As a CLI user, I want to use `--file=path/to/doc.docx`, so that I can operate without Launcher |
| R-007 | Launcher 文件选择 UI | P0 | As a user, I want multiple ways to select files (browser/recent/drag/input), so that I can quickly switch files |
| R-008 | 未保存修改保护 | P0 | As a user, I want to be warned when switching files with unsaved changes, so that I don't lose work |
| R-009 | 错误处理 | P0 | As Launcher, I want clear error responses (404/403/423/409), so that I can show meaningful messages to users |
| R-010 | Breaking Change 执行 | P0 | As a maintainer, I want to remove all old `docx_create(file_path)` usage, so that the codebase is clean |

### 2.2 验收标准

#### R-001: 移除文件管理接口
- **WHEN** 查看 MCP tools 列表, **THEN** 系统 **SHALL NOT** 包含 `docx_list_files` 和 `docx_create_file`
- **WHEN** 搜索代码库, **THEN** 系统 **SHALL NOT** 包含这两个函数的实现

#### R-002: 全局活跃文件状态
- **WHEN** Server 启动且未指定 --file, **THEN** 系统 **SHALL** 将 active_file 设为 None
- **WHEN** Launcher 调用 POST /api/file/switch, **THEN** 系统 **SHALL** 更新 active_file 为新路径
- **WHEN** 存在旧 session, **THEN** 系统 **SHALL** 根据 force 参数决定是否关闭

#### R-003: docx_create() 无参数
- **WHEN** Claude 调用 `docx_create()`, **THEN** 系统 **SHALL** 打开 active_file（如果已设置）
- **WHEN** active_file 为 None, **THEN** 系统 **SHALL** 返回错误 "No active file set. Use Launcher or --file to specify a file."
- **WHEN** 调用 `docx_create(file_path)`, **THEN** 系统 **SHALL** 返回错误 "file_path parameter is removed. Use Launcher or --file instead."

#### R-004: HTTP 文件切换 API
- **WHEN** Launcher 调用 `POST /api/file/switch {path: "/path/to/doc.docx"}`, **THEN** 系统 **SHALL**:
  - 检查文件是否存在（不存在返回 404）
  - 检查文件权限（无权限返回 403）
  - 检查文件是否被锁定（锁定返回 423）
  - 检查当前 session 是否有未保存修改（有修改且 force=false 返回 409）
  - 关闭旧 session（如有）
  - 设置 active_file 为新路径
  - 返回 200 OK 和新状态

#### R-005: HTTP 状态查询 API
- **WHEN** Launcher 调用 `GET /api/status`, **THEN** 系统 **SHALL** 返回:
  ```json
  {
    "currentFile": "/path/to/doc.docx" | null,
    "sessionId": "abc-123" | null,
    "hasUnsaved": true | false,
    "serverVersion": "2.3.0"
  }
  ```

#### R-006: CLI --file 参数
- **WHEN** 启动命令包含 `--file=/path/to/doc.docx`, **THEN** 系统 **SHALL** 设置 active_file 为该路径
- **WHEN** 文件不存在, **THEN** 系统 **SHALL** 退出并显示错误信息

#### R-007: Launcher 文件选择 UI
- **WHEN** 用户点击"选择文件"按钮, **THEN** Launcher **SHALL** 打开系统文件浏览器，过滤 .docx 文件
- **WHEN** 用户拖拽 .docx 文件到窗口, **THEN** Launcher **SHALL** 调用 API 切换到该文件
- **WHEN** Launcher 启动, **THEN** 系统 **SHALL** 显示最近打开的 5-10 个文件列表
- **WHEN** 用户在路径输入框输入路径, **THEN** Launcher **SHALL** 提供自动补全（基于最近文件）

#### R-008: 未保存修改保护
- **WHEN** 切换文件且 hasUnsaved=true 且 force=false, **THEN** Server **SHALL** 返回 409 Conflict:
  ```json
  {
    "error": "Unsaved changes exist",
    "code": 409,
    "currentFile": "/path/to/old.docx",
    "message": "Call with force=true to discard changes"
  }
  ```
- **WHEN** Launcher 收到 409, **THEN** Launcher **SHALL** 显示对话框询问用户: "Save changes to old.docx?"（选项：保存并切换 / 丢弃并切换 / 取消）

#### R-009: 错误处理
- **WHEN** 文件不存在, **THEN** Server **SHALL** 返回 `404 Not Found {error: "File not found: /path"}`
- **WHEN** 文件被锁定, **THEN** Server **SHALL** 返回 `423 Locked {error: "File is locked by another process"}`
- **WHEN** 权限不足, **THEN** Server **SHALL** 返回 `403 Forbidden {error: "Permission denied"}`

#### R-010: Breaking Change 执行
- **WHEN** 搜索代码库中 `docx_create(`, **THEN** 系统 **SHALL** 只找到无参数调用 `docx_create()`
- **WHEN** 查看 CHANGELOG, **THEN** 系统 **SHALL** 包含 Breaking Change 说明和迁移指南

---

## 3. 功能验收清单

| ID | 功能点 | 验收步骤 | 优先级 | 关联需求 | 通过 |
|----|--------|----------|--------|----------|------|
| F-001 | Server 全局单文件状态 | 1. 启动 Server<br>2. active_file 初始为 None<br>3. 调用 API 切换文件<br>4. active_file 更新 | P0 | R-002 | ☐ |
| F-002 | docx_create() 无参数 | 1. 设置 active_file<br>2. 调用 docx_create()<br>3. 返回 session_id<br>4. Session 指向 active_file | P0 | R-003 | ☐ |
| F-003 | docx_create(path) 报错 | 1. 调用 docx_create("/path")<br>2. 返回错误信息 | P0 | R-003, R-010 | ☐ |
| F-004 | POST /api/file/switch | 1. 调用 API 切换文件<br>2. 检查错误场景（404/403/423/409）<br>3. 成功返回新状态 | P0 | R-004, R-009 | ☐ |
| F-005 | GET /api/status | 1. 调用 API 查询状态<br>2. 返回 currentFile, sessionId, hasUnsaved | P0 | R-005 | ☐ |
| F-006 | CLI --file 启动 | 1. 使用 --file=/path 启动<br>2. active_file 设置正确<br>3. docx_create() 直接可用 | P1 | R-006 | ☐ |
| F-007 | Launcher 文件浏览器 | 1. 点击"选择文件"<br>2. 文件对话框打开<br>3. 选择文件后 API 调用成功 | P0 | R-007 | ☐ |
| F-008 | Launcher 最近文件 | 1. Launcher 启动<br>2. 显示最近文件列表<br>3. 点击列表项切换文件 | P0 | R-007 | ☐ |
| F-009 | Launcher 拖拽支持 | 1. 拖拽 .docx 文件到窗口<br>2. API 调用成功<br>3. 文件切换 | P0 | R-007 | ☐ |
| F-010 | Launcher 路径输入 | 1. 在输入框输入路径<br>2. 自动补全显示<br>3. 回车切换文件 | P0 | R-007 | ☐ |
| F-011 | 未保存修改警告 | 1. 修改文档未保存<br>2. 切换文件 force=false<br>3. 返回 409<br>4. Launcher 显示对话框 | P0 | R-008 | ☐ |
| F-012 | force=true 强制切换 | 1. 未保存修改存在<br>2. 切换文件 force=true<br>3. 直接切换成功 | P0 | R-008 | ☐ |
| F-013 | 文件不存在错误 | 1. 切换到不存在的文件<br>2. 返回 404<br>3. Launcher 显示错误 | P0 | R-009 | ☐ |
| F-014 | 文件锁定错误 | 1. 文件被其他程序打开<br>2. 切换文件<br>3. 返回 423 | P1 | R-009 | ☐ |
| F-015 | 权限不足错误 | 1. 文件只读或无权限<br>2. 切换文件<br>3. 返回 403 | P1 | R-009 | ☐ |
| F-016 | 旧接口移除 | 1. 搜索 docx_list_files<br>2. 搜索 docx_create_file<br>3. 搜索 docx_create(file_path)<br>4. 均不存在 | P0 | R-001, R-010 | ☐ |

---

## 4. 技术约束

### 4.1 技术栈
- **Server**: Python 3.11+, fastmcp (利用其 HTTP 能力)
- **HTTP API**: RESTful 风格，JSON 格式
- **Launcher**: PyQt6 (现有技术栈)
- **状态同步**: 轮询模式（GET /api/status，1-2 秒间隔）

### 4.2 架构设计

#### Server 端架构变更
```python
# 全局状态
active_file: Optional[str] = None
active_session: Optional[Session] = None

# 核心逻辑
def set_active_file(path: str, force: bool = False):
    if active_session and active_session.has_unsaved and not force:
        raise UnsavedChangesError()

    if active_session:
        session_manager.close_session(active_session.id)

    active_file = path
    active_session = None  # 等待 docx_create() 创建

def docx_create():
    if not active_file:
        raise NoActiveFileError()

    active_session = session_manager.create_session(active_file)
    return active_session.id
```

#### HTTP API 端点
```
POST /api/file/switch
  Body: {path: string, force?: boolean}
  Response: {currentFile: string, sessionId: string | null}
  Errors: 404, 403, 423, 409

GET /api/status
  Response: {currentFile: string | null, sessionId: string | null, hasUnsaved: boolean, serverVersion: string}

POST /api/session/close
  Body: {save?: boolean}
  Response: {success: boolean}
```

#### Launcher 端架构变更
```python
class LauncherWindow:
    def __init__(self):
        self.http_client = HTTPClient(base_url="http://localhost:8080")
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(2000)  # 2 秒轮询

    def switch_file(self, path: str, force: bool = False):
        try:
            response = self.http_client.post("/api/file/switch", {
                "path": path,
                "force": force
            })
            self.update_ui(response)
        except Conflict409:
            self.show_unsaved_dialog(path)

    def show_unsaved_dialog(self, new_path: str):
        # 弹出对话框：保存并切换 / 丢弃并切换 / 取消
        pass
```

### 4.3 集成点
- **fastmcp HTTP**：利用 fastmcp 的 HTTP 服务器能力（需要研究 fastmcp 文档）
- **Launcher ↔ Server**：HTTP REST API（JSON）
- **Session Manager**：需要增加 `has_unsaved` 状态追踪

### 4.4 性能要求
- API 响应时间 < 200ms（本地通信）
- 状态轮询不影响主线程（Launcher 使用异步或线程）
- 文件切换时 Session 清理及时（避免内存泄漏）

---

## 5. 排除项

- ❌ **多文件并发**：不支持同时操作多个文件，明确为全局单文件模式
- ❌ **WebSocket 实时推送**：使用轮询模式，不实现 WebSocket（简化架构）
- ❌ **向后兼容**：Breaking Change，不保留 `docx_create(file_path)` 接口
- ❌ **远程文件**：仅支持本地文件系统，不支持云存储或网络路径
- ❌ **Session 迁移**：切换文件时不支持保留旧 Session，直接关闭
- ❌ **Launcher 自动保存**：不实现 Launcher 自动保存功能，由用户决定

---

## 6. 风险与挑战

### 6.1 技术风险
| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| fastmcp HTTP 能力未知 | 高 | 优先研究 fastmcp 文档，若不支持则回退到 FastAPI/Flask |
| Session 状态追踪复杂 | 中 | 设计清晰的 Session 生命周期状态机 |
| 文件锁定检测不可靠 | 低 | 使用 try-except 捕获文件打开错误，返回 423 |

### 6.2 迁移风险
| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Breaking Change 导致用户不满 | 高 | 提供详细迁移指南，发布 v3.0 主版本，更新 CHANGELOG |
| 现有测试失效 | 中 | 系统性更新单元测试和 E2E 测试 |
| 文档过时 | 中 | 同步更新 README.md, CLAUDE.md, API 文档 |

---

## 7. 下一步

### 7.1 开发流程
本功能属于 **complex 级别**，建议走完整 SDD 流程：

1. ✅ **阶段 0**: 需求澄清（当前文档）
2. **阶段 1**: 技术设计（在新会话执行 `/clouditera:dev:spec-dev http-file-management --skip-requirements`）
   - 生成 design.md（系统架构、模块设计、数据流）
   - 生成 tasks.md（任务拆解、依赖关系、并行分组）
3. **阶段 2**: 实施开发（TDD 流程）
   - 按 tasks.md 顺序实施
   - 单元测试先行
   - 集成测试验证
4. **阶段 3**: 审查与发布
   - 代码审查
   - 更新文档
   - 发布 v3.0

### 7.2 立即行动

#### 选项 1: 创建 Worktree 并继续（推荐）
```bash
# 在当前会话继续
# Claude 将自动创建 worktree 并执行 spec-dev
```

#### 选项 2: 创建 Worktree，稍后执行
```bash
# 手动创建 worktree
git worktree add .worktrees/feature/http-file-management-20260126

# 在新终端执行
cd .worktrees/feature/http-file-management-20260126
/clouditera:dev:spec-dev http-file-management --skip-requirements
```

#### 选项 3: 在主工作区继续
```bash
# 不推荐，会污染主分支
/clouditera:dev:spec-dev http-file-management --skip-requirements --no-worktree
```

---

## 8. 附录

### 8.1 API 错误码汇总

| HTTP 状态码 | 场景 | 响应示例 |
|------------|------|----------|
| 200 OK | 操作成功 | `{currentFile: "...", sessionId: "..."}` |
| 404 Not Found | 文件不存在 | `{error: "File not found: /path/to/file.docx"}` |
| 403 Forbidden | 权限不足 | `{error: "Permission denied"}` |
| 423 Locked | 文件被锁定 | `{error: "File is locked by another process"}` |
| 409 Conflict | 未保存修改 | `{error: "Unsaved changes exist", message: "Call with force=true to discard"}` |
| 500 Internal Server Error | 内部错误 | `{error: "Internal server error", detail: "..."}` |

### 8.2 Launcher UI 线框图（简化）

```
┌─────────────────────────────────────────────┐
│  Docx Server Launcher                       │
├─────────────────────────────────────────────┤
│  Current File: /path/to/document.docx   📝  │
│  Status: ● Active  |  Unsaved: Yes          │
├─────────────────────────────────────────────┤
│  ┌─────────────────────────────────────┐    │
│  │ File Path: [/path/to/document.docx] │📂  │
│  └─────────────────────────────────────┘    │
├─────────────────────────────────────────────┤
│  Recent Files:                              │
│  • document.docx       (2 min ago)          │
│  • report-2025.docx    (1 hour ago)         │
│  • template.docx       (yesterday)          │
├─────────────────────────────────────────────┤
│  [Select File] [Save] [Close Session]       │
└─────────────────────────────────────────────┘
   ↑ 支持拖拽 .docx 文件
```

### 8.3 迁移指南（草稿）

#### v2.x → v3.0 Breaking Changes

**移除的接口**：
```python
# ❌ 不再可用
docx_list_files(directory)
docx_create_file(file_path)
docx_create(file_path)  # 有参数版本

# ✅ 新接口
docx_create()  # 无参数，操作 active file
```

**迁移步骤**：
1. 移除所有 `docx_list_files` 调用，改用 Launcher 文件选择
2. 移除所有 `docx_create_file` 调用
3. 将 `docx_create(path)` 改为：
   - 先通过 Launcher 选择文件
   - 再调用 `docx_create()`

---

**文档版本**: v1
**最后更新**: 2026-01-26
**负责人**: [待分配]
**审查状态**: Draft
