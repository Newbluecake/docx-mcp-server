# docx-mcp-server MCP 工具使用指南

**版本**: v3.0
**更新日期**: 2026-01-27
**适用对象**: Claude AI、MCP 客户端开发者、自动化脚本编写者

---

## 目录

1. [概述](#1-概述)
2. [快速开始](#2-快速开始)
3. [核心概念](#3-核心概念)
4. [工作流示例](#4-工作流示例)
5. [HTTP API 参考](#5-http-api-参考)
6. [MCP 工具参考](#6-mcp-工具参考)
7. [最佳实践](#7-最佳实践)
8. [故障排查](#8-故障排查)

---

## 1. 概述

### 1.1 什么是 docx-mcp-server？

docx-mcp-server 是一个基于 Model Context Protocol (MCP) 的服务器，为 Claude AI 和其他 MCP 客户端提供细粒度的 Microsoft Word (.docx) 文档操作能力。

**核心特性**:
- **会话管理**: 维护有状态的文档编辑会话，支持并发操作
- **原子化操作**: 精确控制段落、文本块、表格的每个元素
- **全局单文件模式**: 通过 HTTP API 集中管理活动文件
- **可视化响应**: 返回 Markdown 格式的响应，包含 ASCII 树状图
- **格式化支持**: 字体、对齐、颜色、样式等完整格式控制

### 1.2 架构概览 (v3.0)

```
┌─────────────────────┐
│  Launcher GUI       │  用户通过 GUI 选择文件
│  (File Browser)     │
└──────────┬──────────┘
           │ HTTP POST /api/file/switch
           ▼
┌─────────────────────┐
│  GlobalState        │  维护全局活动文件
│  active_file        │  (线程安全)
│  active_session_id  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Claude AI          │  调用 MCP 工具
│  (MCP Client)       │  docx_create() → session_id
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Session Manager    │  管理文档会话
│  - Document Object  │  - 对象注册表
│  - Object Registry  │  - 光标位置
│  - Cursor State     │  - 自动保存
└─────────────────────┘
```

**关键变化 (v2.x → v3.0)**:
- ❌ 移除: `docx_create(file_path=...)` 参数
- ❌ 移除: `docx_list_files()` 工具
- ✅ 新增: 全局单文件模式 (`global_state.active_file`)
- ✅ 新增: HTTP REST API (`/api/file/switch`, `/api/status`)
- ✅ 新增: Combined 传输模式 (FastAPI + MCP)

详见 [迁移指南](./migration-v2-to-v3.md)。

### 1.3 响应格式

所有 MCP 工具返回 **Markdown 格式**的响应（v2.0 更新），包含：

**成功响应示例**:
```markdown
# 操作结果: Insert Paragraph

**Status**: ✅ Success
**Element ID**: para_abc123
**Operation**: Insert Paragraph
**Position**: end:document_body

---

## 📄 Document Context

📄 Document Context (showing 3 elements around para_abc123)

  ┌─────────────────────────────────────┐
  │ Paragraph (para_xyz789)             │
  ├─────────────────────────────────────┤
  │ Previous paragraph text             │
  └─────────────────────────────────────┘

>>> [CURSOR] <<<

  ┌─────────────────────────────────────┐
  │ Paragraph (para_abc123) ⭐ CURRENT   │
  ├─────────────────────────────────────┤
  │ New paragraph text                  │
  └─────────────────────────────────────┘
```

**错误响应示例**:
```markdown
# 操作结果: Error

**Status**: ❌ Error
**Error Type**: SessionNotFound
**Message**: Session abc-123 not found or expired
```

**解析响应**:
```python
import re

# 提取元素 ID
match = re.search(r'\*\*Element ID\*\*:\s*(\w+)', response)
element_id = match.group(1) if match else None

# 检查状态
is_success = '**Status**: ✅ Success' in response
is_error = '**Status**: ❌ Error' in response
```

---

## 2. 快速开始

### 2.1 启动服务器

**推荐方式：Combined 模式**（同时提供 REST API 和 MCP）

```bash
# 启动服务器（默认 127.0.0.1:8080）
mcp-server-docx --transport combined

# 指定初始文件
mcp-server-docx --transport combined --file /path/to/document.docx

# 指定 host 和 port
mcp-server-docx --transport combined --host 0.0.0.0 --port 8080
```

**其他模式**:
- **STDIO 模式**（用于 Claude Desktop）: `mcp-server-docx --transport stdio`
- **SSE 模式**（HTTP Server-Sent Events）: `mcp-server-docx --transport sse`
- **Streamable HTTP 模式**: `mcp-server-docx --transport streamable-http`

### 2.2 使用 Launcher GUI 选择文件

**Windows 用户**:
1. 下载并运行 `DocxServerLauncher.exe`
2. 点击 "Browse" 按钮选择 .docx 文件
3. 点击 "Switch File" 按钮
4. Launcher 自动调用 `POST /api/file/switch` 设置活动文件

**命令行用户**:
```bash
# 通过 HTTP API 切换文件
curl -X POST http://127.0.0.1:8080/api/file/switch \
  -H "Content-Type: application/json" \
  -d '{"path": "/path/to/document.docx", "force": false}'
```

### 2.3 创建第一个会话

**步骤 1: 设置活动文件**（通过 Launcher 或 HTTP API）

**步骤 2: 创建会话**
```python
# 调用 MCP 工具
session_id = docx_create()
# 返回: "abc-123-def-456"
```

**步骤 3: 编辑文档**
```python
# 插入段落
para_id = docx_insert_paragraph(
    session_id,
    "Hello World",
    position="end:document_body"
)
# 返回: "para_abc123"
```

**步骤 4: 保存并关闭**
```python
# 保存文档
docx_save(session_id, "/path/to/output.docx")

# 关闭会话
docx_close(session_id)
```

### 2.4 完整示例

```python
# 1. 设置活动文件（通过 Launcher 或 HTTP API）
# 假设已通过 Launcher 选择了 template.docx

# 2. 创建会话
session_id = docx_create()

# 3. 读取内容
content = docx_read_content(session_id, max_paragraphs=10)

# 4. 查找并替换
docx_replace_text(session_id, "{{name}}", "Alice")
docx_replace_text(session_id, "{{date}}", "2026-01-27")

# 5. 添加新段落
para_id = docx_insert_paragraph(
    session_id,
    "This is a new paragraph",
    position="end:document_body"
)

# 6. 格式化段落
run_id = docx_insert_run(session_id, "Bold text", position=f"inside:{para_id}")
docx_set_font(session_id, run_id, bold=True, size=14, color_hex="FF0000")

# 7. 保存文档
docx_save(session_id, "./output.docx")

# 8. 关闭会话
docx_close(session_id)
```

---

## 3. 核心概念

### 3.1 全局活动文件 (global_state.active_file)

**什么是活动文件？**

v3.0 引入了全局单文件模式。服务器维护一个全局状态 `global_state.active_file`，表示当前正在操作的文件路径。

**为什么需要活动文件？**
- **集中管理**: 通过 Launcher GUI 或 HTTP API 统一管理文件选择
- **安全性**: 避免 Claude 直接操作文件路径，减少路径注入风险
- **简化 API**: `docx_create()` 不再需要 `file_path` 参数

**如何设置活动文件？**

| 方式 | 适用场景 | 示例 |
|------|---------|------|
| **Launcher GUI** | 交互式编辑 | 点击 "Browse" → "Switch File" |
| **HTTP API** | 自动化脚本 | `POST /api/file/switch` |
| **CLI 参数** | 服务器启动时 | `--file /path/to/doc.docx` |

**查询活动文件**:
```bash
curl http://127.0.0.1:8080/api/status
# 返回: {"activeFile": "/path/to/doc.docx", "activeSessionId": "abc-123"}
```

### 3.2 会话管理 (session_id)

**什么是会话？**

会话（Session）是一个独立的文档编辑上下文，包含：
- **Document 对象**: python-docx 的 Document 实例
- **对象注册表**: 元素 ID 到 Python 对象的映射
- **光标状态**: 当前操作位置
- **配置**: auto_save、backup_on_save 等

**会话生命周期**:
```
创建 (docx_create)
  ↓
操作 (docx_insert_*, docx_update_*, ...)
  ↓
保存 (docx_save)
  ↓
关闭 (docx_close)
```

**会话特性**:
- **独立性**: 每个会话互不干扰，支持并发操作
- **有状态**: 维护文档状态和对象注册表
- **自动过期**: 默认 1 小时无操作后自动清理
- **资源管理**: 关闭会话释放内存

**获取 session_id**:
```python
# 方式 1: 从 docx_create() 返回值提取
response = docx_create()
# 解析 Markdown 响应
match = re.search(r'\*\*Session ID\*\*:\s*(\S+)', response)
session_id = match.group(1) if match else None

# 方式 2: 查询服务器状态
status = requests.get("http://127.0.0.1:8080/api/status").json()
session_id = status.get("activeSessionId")
```

### 3.3 元素 ID 映射系统

**为什么需要元素 ID？**

python-docx 的对象（Paragraph、Run、Table）是临时的 Python 对象，没有稳定的标识符。元素 ID 系统提供了稳定的字符串 ID，用于跨工具调用引用对象。

**ID 前缀约定**:
| 前缀 | 对象类型 | 示例 |
|------|---------|------|
| `para_*` | 段落 (Paragraph) | `para_a1b2c3d4` |
| `run_*` | 文本块 (Run) | `run_x9y8z7w6` |
| `table_*` | 表格 (Table) | `table_m5n4o3p2` |
| `cell_*` | 单元格 (Cell) | `cell_q1r2s3t4` |

**使用示例**:
```python
# 创建段落，获取 ID
para_id = docx_insert_paragraph(session_id, "Text", position="end:document_body")
# 返回: "para_abc123"

# 使用 ID 引用段落
run_id = docx_insert_run(session_id, "More text", position=f"inside:{para_id}")
# 返回: "run_xyz789"

# 使用 ID 格式化
docx_set_font(session_id, run_id, bold=True)
```

**特殊 ID**（v2.3 新增）:
| 特殊 ID | 说明 | 更新时机 |
|---------|------|---------|
| `last_insert` | 最后插入的元素 | `docx_insert_*` 成功后 |
| `last_update` | 最后更新的元素 | `docx_update_*`、`docx_set_*` 成功后 |
| `cursor` | 光标位置 | `docx_cursor_move` 调用后 |

```python
# 使用特殊 ID
para_id = docx_insert_paragraph(session_id, "First", position="end:document_body")
# 插入到最后插入的元素之后
docx_insert_paragraph(session_id, "Second", position="after:last_insert")
```

### 3.4 Position 定位系统

**Position 格式**: `mode:target_id`

**支持的模式**:
| 模式 | 说明 | 示例 |
|------|------|------|
| `after:element_id` | 在元素之后插入 | `after:para_123` |
| `before:element_id` | 在元素之前插入 | `before:para_123` |
| `inside:element_id` | 在元素内部插入（末尾）| `inside:para_123` |
| `start:element_id` | 在元素内部开头插入 | `start:table_456` |
| `end:element_id` | 在元素内部末尾插入 | `end:document_body` |

**特殊目标**:
- `document_body`: 文档主体
- `last_insert`: 最后插入的元素
- `last_update`: 最后更新的元素
- `cursor`: 光标位置

**示例**:
```python
# 在文档末尾插入
docx_insert_paragraph(session_id, "Text", position="end:document_body")

# 在指定段落之后插入
docx_insert_paragraph(session_id, "Text", position="after:para_123")

# 在段落内部添加 Run
docx_insert_run(session_id, "Text", position="inside:para_123")

# 在表格单元格内添加段落
docx_insert_paragraph_to_cell(session_id, "Text", position="inside:cell_456")
```

---

## 4. 工作流示例

### 4.1 场景 1: 使用 Launcher GUI 编辑文档

**目标**: 通过 Launcher 选择模板文件，填充数据并保存。

**步骤**:

1. **启动服务器**（Combined 模式）
   ```bash
   mcp-server-docx --transport combined
   ```

2. **打开 Launcher GUI**
   - 运行 `DocxServerLauncher.exe`（Windows）
   - 或运行 `docx-server-launcher`（命令行）

3. **选择文件**
   - 点击 "Browse" 按钮
   - 选择 `template.docx`
   - 点击 "Switch File" 按钮
   - Launcher 自动调用 `POST /api/file/switch`

4. **创建会话并编辑**
   ```python
   # 创建会话（使用 Launcher 选择的文件）
   session_id = docx_create()

   # 查找并替换占位符
   docx_replace_text(session_id, "{{company}}", "Acme Corp")
   docx_replace_text(session_id, "{{date}}", "2026-01-27")

   # 添加新内容
   para_id = docx_insert_paragraph(
       session_id,
       "Additional notes",
       position="end:document_body"
   )

   # 保存
   docx_save(session_id, "./filled_template.docx")
   docx_close(session_id)
   ```

### 4.2 场景 2: 通过 HTTP API 自动化处理

**目标**: 编写脚本批量处理多个文档。

**步骤**:

1. **启动服务器**
   ```bash
   mcp-server-docx --transport combined --host 127.0.0.1 --port 8080
   ```

2. **编写自动化脚本**
   ```python
   import requests
   import os

   # 配置
   API_BASE = "http://127.0.0.1:8080"
   TEMPLATE_DIR = "./templates"
   OUTPUT_DIR = "./output"

   # 获取所有模板文件
   files = [f for f in os.listdir(TEMPLATE_DIR) if f.endswith(".docx")]

   for file in files:
       file_path = os.path.abspath(os.path.join(TEMPLATE_DIR, file))

       # 切换活动文件
       response = requests.post(f"{API_BASE}/api/file/switch", json={
           "path": file_path,
           "force": True
       })

       if response.status_code != 200:
           print(f"Failed to switch to {file}: {response.text}")
           continue

       # 创建会话
       session_id = docx_create()

       # 处理文档
       docx_replace_text(session_id, "{{year}}", "2026")
       docx_replace_text(session_id, "{{status}}", "Active")

       # 保存
       output_path = os.path.join(OUTPUT_DIR, file)
       docx_save(session_id, output_path)
       docx_close(session_id)

       print(f"Processed: {file}")
   ```

### 4.3 场景 3: 批量处理多个文件

**目标**: 对多个文档执行相同的操作。

```python
import requests
import os

API_BASE = "http://127.0.0.1:8080"
files = ["doc1.docx", "doc2.docx", "doc3.docx"]

for file in files:
    # 切换文件
    requests.post(f"{API_BASE}/api/file/switch", json={
        "path": os.path.abspath(file),
        "force": True
    })

    # 创建会话
    session_id = docx_create()

    # 添加页眉
    para_id = docx_insert_paragraph(
        session_id,
        "Confidential Document",
        position="start:document_body"
    )
    run_id = docx_insert_run(session_id, "Confidential", position=f"inside:{para_id}")
    docx_set_font(session_id, run_id, bold=True, color_hex="FF0000")

    # 保存
    docx_save(session_id, file)
    docx_close(session_id)
```

### 4.4 场景 4: 模板填充

**目标**: 从 JSON 数据填充 Word 模板。

```python
import json

# 加载数据
with open("data.json") as f:
    data = json.load(f)

# 切换到模板文件（通过 Launcher 或 HTTP API）
# 假设已设置 active_file = "invoice_template.docx"

# 创建会话
session_id = docx_create()

# 填充文本占位符
for key, value in data.items():
    docx_replace_text(session_id, f"{{{{{key}}}}}", str(value))

# 填充表格
table_id = docx_find_table(session_id, "Item")
if table_id:
    # 准备表格数据
    table_data = json.dumps([
        ["Item", "Quantity", "Price"],
        ["Product A", "10", "$100"],
        ["Product B", "5", "$50"]
    ])

    # 智能填充表格
    docx_smart_fill_table(
        session_id,
        table_id,
        table_data,
        has_header=True,
        auto_resize=True
    )

# 保存
docx_save(session_id, "./invoice_filled.docx")
docx_close(session_id)
```

---

## 5. HTTP API 参考

### 5.1 POST /api/file/switch

**功能**: 切换当前活动文件。

**请求**:
```http
POST /api/file/switch HTTP/1.1
Content-Type: application/json

{
  "path": "/absolute/path/to/document.docx",
  "force": false
}
```

**参数**:
- `path` (string, required): 文件的绝对路径
- `force` (boolean, optional): 是否强制切换（忽略未保存更改）。默认 `false`

**响应**:

**成功 (200 OK)**:
```json
{
  "status": "success",
  "message": "File switched successfully",
  "currentFile": "/absolute/path/to/document.docx",
  "sessionId": "abc-123-def-456"
}
```

**文件不存在 (404 Not Found)**:
```json
{
  "status": "error",
  "message": "File not found: /path/to/nonexistent.docx"
}
```

**有未保存更改 (409 Conflict)**:
```json
{
  "status": "error",
  "message": "Active session has unsaved changes. Use force=true to override.",
  "hasUnsavedChanges": true
}
```

**示例**:
```bash
curl -X POST http://127.0.0.1:8080/api/file/switch \
  -H "Content-Type: application/json" \
  -d '{"path": "/home/user/document.docx", "force": false}'
```

### 5.2 GET /api/status

**功能**: 获取服务器状态和活动文件信息。

**请求**:
```http
GET /api/status HTTP/1.1
```

**响应 (200 OK)**:
```json
{
  "status": "running",
  "version": "3.0.0",
  "activeFile": "/path/to/document.docx",
  "activeSessionId": "abc-123-def-456",
  "hasUnsavedChanges": false,
  "activeSessions": 1,
  "uptime": 3600.5
}
```

**字段说明**:
- `status`: 服务器状态（"running"）
- `version`: 服务器版本
- `activeFile`: 当前活动文件路径（null 表示无活动文件）
- `activeSessionId`: 当前活动会话 ID（null 表示无活动会话）
- `hasUnsavedChanges`: 是否有未保存更改
- `activeSessions`: 活动会话数量
- `uptime`: 服务器运行时间（秒）

**示例**:
```bash
curl http://127.0.0.1:8080/api/status
```

### 5.3 POST /api/session/close

**功能**: 关闭指定会话。

**请求**:
```http
POST /api/session/close HTTP/1.1
Content-Type: application/json

{
  "sessionId": "abc-123-def-456"
}
```

**响应 (200 OK)**:
```json
{
  "status": "success",
  "message": "Session closed successfully"
}
```

**示例**:
```bash
curl -X POST http://127.0.0.1:8080/api/session/close \
  -H "Content-Type: application/json" \
  -d '{"sessionId": "abc-123-def-456"}'
```

### 5.4 GET /health

**功能**: 健康检查端点。

**请求**:
```http
GET /health HTTP/1.1
```

**响应 (200 OK)**:
```json
{
  "status": "healthy"
}
```

**示例**:
```bash
curl http://127.0.0.1:8080/health
```

---


## 6. MCP 工具参考

docx-mcp-server 提供 **54 个 MCP 工具**，按功能领域分为 11 个模块。

### 6.1 工具分类概览

| 模块 | 工具数量 | 说明 |
|------|---------|------|
| **Session Tools** | 6 | 会话管理（创建、保存、关闭）|
| **Content Tools** | 4 | 内容读取和搜索 |
| **Paragraph Tools** | 6 | 段落操作（插入、更新、删除）|
| **Run Tools** | 3 | 文本块操作（字体、样式）|
| **Table Tools** | 13 | 表格操作（创建、填充、行列管理）|
| **Format Tools** | 6 | 格式化（对齐、边距、格式刷）|
| **Advanced Tools** | 3 | 高级编辑（文本替换、图片插入）|
| **Cursor Tools** | 2 | 光标定位 |
| **Copy Tools** | 2 | 复制与元数据 |
| **Composite Tools** | 5 | 复合工具（高层操作）|
| **System Tools** | 3 | 系统状态和日志 |
| **History Tools** | 1 | 历史记录 |

### 6.2 Session Tools（会话管理）

#### 6.2.1 docx_create

**功能**: 创建新的文档会话。

**参数**:
- `auto_save` (bool, optional): 启用自动保存。默认 `False`
- `backup_on_save` (bool, optional): 保存时创建备份。默认 `False`
- `backup_dir` (str, optional): 备份目录路径
- `backup_suffix` (str, optional): 备份文件后缀

**返回**: Markdown 格式响应，包含 `session_id`

**重要说明**:
- **v3.0 Breaking Change**: 移除了 `file_path` 参数
- 文件通过 `global_state.active_file` 管理
- 使用 Launcher GUI 或 HTTP API 设置活动文件

**示例**:
```python
# 创建空白文档会话
session_id = docx_create()

# 创建会话并启用自动保存
session_id = docx_create(auto_save=True)

# 创建会话并启用备份
session_id = docx_create(
    backup_on_save=True,
    backup_dir="./backups",
    backup_suffix=".bak"
)
```

**工作流**:
```
1. 通过 Launcher 或 HTTP API 设置 active_file
   ↓
2. 调用 docx_create()
   ↓
3. 服务器加载 active_file（如果存在）
   ↓
4. 返回 session_id
```

#### 6.2.2 docx_save

**功能**: 保存文档到磁盘。

**参数**:
- `session_id` (str, required): 会话 ID
- `file_path` (str, required): 保存路径（绝对或相对）
- `backup` (bool, optional): 是否创建备份。默认 `False`
- `backup_dir` (str, optional): 备份目录
- `backup_suffix` (str, optional): 备份后缀

**返回**: Markdown 格式响应，包含保存路径

**示例**:
```python
# 保存到指定路径
docx_save(session_id, "./output.docx")

# 保存并创建备份
docx_save(session_id, "./output.docx", backup=True, backup_dir="./backups")
```

**注意事项**:
- 如果文件已存在，将被覆盖
- 在 `auto_save` 模式下，每次修改后自动调用
- 支持 Live Preview（如果文件在 Word 中打开，会自动刷新）

#### 6.2.3 docx_close

**功能**: 关闭会话并释放资源。

**参数**:
- `session_id` (str, required): 会话 ID

**返回**: Markdown 格式响应

**示例**:
```python
docx_close(session_id)
```

**重要**:
- 未保存的更改将丢失，务必先调用 `docx_save()`
- 关闭后的会话无法重新打开，需创建新会话

#### 6.2.4 docx_get_context

**功能**: 获取会话上下文信息。

**参数**:
- `session_id` (str, required): 会话 ID

**返回**: Markdown 格式响应，包含：
- `last_created_id`: 最后创建的元素 ID
- `last_accessed_id`: 最后访问的元素 ID
- `file_path`: 文件路径
- `auto_save`: 是否启用自动保存

**示例**:
```python
context = docx_get_context(session_id)
```

#### 6.2.5 docx_list_sessions

**功能**: 列出所有活动会话。

**参数**: 无

**返回**: Markdown 格式响应，包含会话列表

**示例**:
```python
sessions = docx_list_sessions()
```

#### 6.2.6 docx_cleanup_sessions

**功能**: 清理过期或空闲会话。

**参数**:
- `max_idle_seconds` (int, optional): 最大空闲时间（秒）。默认使用服务器配置

**返回**: Markdown 格式响应，包含清理数量

**示例**:
```python
# 清理空闲超过 30 分钟的会话
result = docx_cleanup_sessions(max_idle_seconds=1800)
```

### 6.3 Content Tools（内容读取）

#### 6.3.1 docx_read_content

**功能**: 读取文档内容（支持分页）。

**参数**:
- `session_id` (str, required): 会话 ID
- `max_paragraphs` (int, optional): 最大段落数。默认全部
- `start_from` (int, optional): 起始段落索引（0-based）。默认 0
- `include_tables` (bool, optional): 是否包含表格。默认 `False`
- `return_json` (bool, optional): 是否返回 JSON 格式。默认 `False`
- `include_ids` (bool, optional): 是否包含元素 ID。默认 `True`

**返回**: 文本内容或 JSON 格式数据

**示例**:
```python
# 读取全部内容
content = docx_read_content(session_id)

# 读取前 10 段
content = docx_read_content(session_id, max_paragraphs=10)

# 读取第 10-20 段
content = docx_read_content(session_id, max_paragraphs=10, start_from=10)

# 包含表格
content = docx_read_content(session_id, include_tables=True)
```

**用途**:
- 预览文档内容
- 提取文本用于分析
- 验证文档生成结果
- 分页读取大文档（减少 token 使用）

#### 6.3.2 docx_find_paragraphs

**功能**: 查找包含指定文本的段落。

**参数**:
- `session_id` (str, required): 会话 ID
- `query` (str, required): 搜索文本
- `max_results` (int, optional): 最大结果数。默认全部
- `return_context` (bool, optional): 是否返回上下文。默认 `False`

**返回**: Markdown 格式响应，包含匹配的段落 ID 列表

**示例**:
```python
# 查找包含 "TODO" 的段落
results = docx_find_paragraphs(session_id, "TODO")

# 限制结果数量
results = docx_find_paragraphs(session_id, "TODO", max_results=5)
```

**用途**:
- 查找占位符（如 `{{name}}`）
- 定位需要编辑的段落
- 验证文本是否存在

#### 6.3.3 docx_extract_template_structure

**功能**: 提取文档结构（标题、段落、表格）。

**参数**:
- `session_id` (str, required): 会话 ID
- `max_depth` (int, optional): 最大深度。默认无限制
- `include_content` (bool, optional): 是否包含内容。默认 `True`
- `max_items_per_type` (int, optional): 每种类型的最大项数

**返回**: JSON 格式的文档结构

**示例**:
```python
# 提取完整结构
structure = docx_extract_template_structure(session_id)

# 只提取标题和表格（不包含段落内容）
structure = docx_extract_template_structure(
    session_id,
    include_content=False,
    max_items_per_type=10
)
```

**用途**:
- 分析模板结构
- 生成文档大纲
- 识别占位符位置

#### 6.3.4 docx_get_structure_summary

**功能**: 获取轻量级文档结构摘要（v2.0 新增）。

**参数**:
- `session_id` (str, required): 会话 ID
- `max_headings` (int, optional): 最大标题数。默认 10
- `max_tables` (int, optional): 最大表格数。默认 5
- `max_paragraphs` (int, optional): 最大段落数。默认 0（不包含）
- `include_content` (bool, optional): 是否包含内容。默认 `False`

**返回**: JSON 格式的摘要

**示例**:
```python
# 只获取标题和表格（减少 90% token 使用）
summary = docx_get_structure_summary(
    session_id,
    max_headings=10,
    max_tables=5,
    max_paragraphs=0
)
```

**用途**:
- 快速了解文档结构
- 减少 token 使用
- 生成文档目录

### 6.4 Paragraph Tools（段落操作）

#### 6.4.1 docx_insert_paragraph

**功能**: 插入新段落。

**参数**:
- `session_id` (str, required): 会话 ID
- `text` (str, required): 段落文本
- `position` (str, required): 插入位置（如 `end:document_body`）
- `style` (str, optional): 段落样式（如 `Body Text`）

**返回**: Markdown 格式响应，包含 `para_id`

**示例**:
```python
# 在文档末尾插入
para_id = docx_insert_paragraph(
    session_id,
    "Hello World",
    position="end:document_body"
)

# 在指定段落之后插入
para_id = docx_insert_paragraph(
    session_id,
    "New paragraph",
    position="after:para_123"
)

# 使用样式
para_id = docx_insert_paragraph(
    session_id,
    "Body text",
    position="end:document_body",
    style="Body Text"
)
```

#### 6.4.2 docx_insert_heading

**功能**: 插入标题。

**参数**:
- `session_id` (str, required): 会话 ID
- `text` (str, required): 标题文本
- `position` (str, required): 插入位置
- `level` (int, optional): 标题级别（1-9）。默认 1

**返回**: Markdown 格式响应，包含 `para_id`

**示例**:
```python
# 插入一级标题
heading_id = docx_insert_heading(
    session_id,
    "Chapter 1",
    position="end:document_body",
    level=1
)

# 插入二级标题
heading_id = docx_insert_heading(
    session_id,
    "Section 1.1",
    position="after:para_123",
    level=2
)
```

#### 6.4.3 docx_update_paragraph_text

**功能**: 更新段落文本。

**参数**:
- `session_id` (str, required): 会话 ID
- `paragraph_id` (str, required): 段落 ID
- `new_text` (str, required): 新文本

**返回**: Markdown 格式响应

**示例**:
```python
docx_update_paragraph_text(session_id, "para_123", "Updated text")
```

**注意**: 此操作会清除段落的所有格式，只保留纯文本。

#### 6.4.4 docx_copy_paragraph

**功能**: 深拷贝段落（保留格式）。

**参数**:
- `session_id` (str, required): 会话 ID
- `paragraph_id` (str, required): 源段落 ID
- `position` (str, required): 插入位置

**返回**: Markdown 格式响应，包含新段落 ID

**示例**:
```python
# 复制段落到文档末尾
new_para_id = docx_copy_paragraph(
    session_id,
    "para_123",
    position="end:document_body"
)
```

#### 6.4.5 docx_delete

**功能**: 删除元素（段落、表格等）。

**参数**:
- `session_id` (str, required): 会话 ID
- `element_id` (str, optional): 元素 ID。如果为空，删除最后创建的元素

**返回**: Markdown 格式响应

**示例**:
```python
# 删除指定段落
docx_delete(session_id, element_id="para_123")

# 删除最后创建的元素
docx_delete(session_id)
```

#### 6.4.6 docx_insert_page_break

**功能**: 插入分页符。

**参数**:
- `session_id` (str, required): 会话 ID
- `position` (str, required): 插入位置

**返回**: Markdown 格式响应

**示例**:
```python
# 在文档末尾插入分页符
docx_insert_page_break(session_id, position="end:document_body")

# 在指定段落之后插入
docx_insert_page_break(session_id, position="after:para_123")
```

### 6.5 Run Tools（文本块操作）

#### 6.5.1 docx_insert_run

**功能**: 向段落添加文本块（Run）。

**参数**:
- `session_id` (str, required): 会话 ID
- `text` (str, required): 文本内容
- `position` (str, required): 插入位置（通常是 `inside:para_id`）

**返回**: Markdown 格式响应，包含 `run_id`

**示例**:
```python
# 向段落添加文本块
run_id = docx_insert_run(
    session_id,
    "Bold text",
    position="inside:para_123"
)
```

**用途**:
- 在段落中添加不同格式的文本
- 实现混合格式（如部分加粗、部分斜体）

#### 6.5.2 docx_update_run_text

**功能**: 更新 Run 的文本。

**参数**:
- `session_id` (str, required): 会话 ID
- `run_id` (str, required): Run ID
- `new_text` (str, required): 新文本

**返回**: Markdown 格式响应

**示例**:
```python
docx_update_run_text(session_id, "run_123", "Updated text")
```

#### 6.5.3 docx_set_font

**功能**: 设置 Run 的字体属性。

**参数**:
- `session_id` (str, required): 会话 ID
- `run_id` (str, required): Run ID
- `size` (float, optional): 字体大小（磅）
- `bold` (bool, optional): 是否加粗
- `italic` (bool, optional): 是否斜体
- `color_hex` (str, optional): 颜色（十六进制，不含 `#`）

**返回**: Markdown 格式响应

**示例**:
```python
# 设置加粗和字体大小
docx_set_font(session_id, "run_123", bold=True, size=14)

# 设置颜色
docx_set_font(session_id, "run_123", color_hex="FF0000")

# 组合设置
docx_set_font(
    session_id,
    "run_123",
    bold=True,
    italic=True,
    size=16,
    color_hex="0000FF"
)
```

### 6.6 Table Tools（表格操作）

#### 6.6.1 docx_insert_table

**功能**: 创建新表格。

**参数**:
- `session_id` (str, required): 会话 ID
- `rows` (int, required): 行数（≥ 1）
- `cols` (int, required): 列数（≥ 1）
- `position` (str, required): 插入位置

**返回**: Markdown 格式响应，包含 `table_id`

**示例**:
```python
# 创建 3x2 表格
table_id = docx_insert_table(
    session_id,
    rows=3,
    cols=2,
    position="end:document_body"
)
```

#### 6.6.2 docx_get_table

**功能**: 按索引获取表格。

**参数**:
- `session_id` (str, required): 会话 ID
- `index` (int, required): 表格索引（0-based）

**返回**: Markdown 格式响应，包含 `table_id`

**示例**:
```python
# 获取第一个表格
table_id = docx_get_table(session_id, index=0)
```

#### 6.6.3 docx_find_table

**功能**: 查找包含指定文本的表格。

**参数**:
- `session_id` (str, required): 会话 ID
- `text` (str, required): 搜索文本

**返回**: Markdown 格式响应，包含 `table_id`

**示例**:
```python
# 查找包含 "Employee" 的表格
table_id = docx_find_table(session_id, "Employee")
```

#### 6.6.4 docx_get_cell

**功能**: 获取表格单元格。

**参数**:
- `session_id` (str, required): 会话 ID
- `table_id` (str, required): 表格 ID
- `row` (int, required): 行索引（0-based）
- `col` (int, required): 列索引（0-based）

**返回**: Markdown 格式响应，包含 `cell_id`

**示例**:
```python
# 获取第一行第一列的单元格
cell_id = docx_get_cell(session_id, "table_123", row=0, col=0)
```

#### 6.6.5 docx_insert_paragraph_to_cell

**功能**: 向单元格添加段落。

**参数**:
- `session_id` (str, required): 会话 ID
- `text` (str, required): 段落文本
- `position` (str, required): 插入位置（通常是 `inside:cell_id`）

**返回**: Markdown 格式响应，包含 `para_id`

**示例**:
```python
# 向单元格添加段落
para_id = docx_insert_paragraph_to_cell(
    session_id,
    "Cell content",
    position="inside:cell_123"
)
```

#### 6.6.6 docx_insert_table_row

**功能**: 向表格末尾添加行。

**参数**:
- `session_id` (str, required): 会话 ID
- `position` (str, required): 插入位置（通常是 `end:table_id`）

**返回**: Markdown 格式响应

**示例**:
```python
# 向表格末尾添加行
docx_insert_table_row(session_id, position="end:table_123")
```

#### 6.6.7 docx_insert_table_col

**功能**: 向表格末尾添加列。

**参数**:
- `session_id` (str, required): 会话 ID
- `position` (str, required): 插入位置（通常是 `end:table_id`）

**返回**: Markdown 格式响应

**示例**:
```python
# 向表格末尾添加列
docx_insert_table_col(session_id, position="end:table_123")
```

#### 6.6.8 docx_insert_row_at

**功能**: 在指定位置插入行（v2.2 新增）。

**参数**:
- `session_id` (str, required): 会话 ID
- `table_id` (str, required): 表格 ID
- `position` (str, required): 插入位置（`after:N`, `before:N`, `start`, `end`）
- `row_index` (int, optional): 行索引（用于 after/before）
- `copy_format` (bool, optional): 是否复制格式。默认 `True`

**返回**: Markdown 格式响应

**示例**:
```python
# 在第 2 行之后插入
docx_insert_row_at(session_id, "table_123", position="after:2")

# 在表格开头插入
docx_insert_row_at(session_id, "table_123", position="start")
```

#### 6.6.9 docx_insert_col_at

**功能**: 在指定位置插入列（v2.2 新增）。

**参数**:
- `session_id` (str, required): 会话 ID
- `table_id` (str, required): 表格 ID
- `position` (str, required): 插入位置（`after:N`, `before:N`, `start`, `end`）
- `col_index` (int, optional): 列索引（用于 after/before）
- `copy_format` (bool, optional): 是否复制格式。默认 `True`

**返回**: Markdown 格式响应

**示例**:
```python
# 在第 1 列之后插入
docx_insert_col_at(session_id, "table_123", position="after:1")
```

#### 6.6.10 docx_delete_row

**功能**: 删除表格行（v2.2 新增）。

**参数**:
- `session_id` (str, required): 会话 ID
- `table_id` (str, required): 表格 ID
- `row_index` (int, required): 行索引（0-based）

**返回**: Markdown 格式响应

**示例**:
```python
# 删除第 2 行
docx_delete_row(session_id, "table_123", row_index=1)
```

#### 6.6.11 docx_delete_col

**功能**: 删除表格列（v2.2 新增）。

**参数**:
- `session_id` (str, required): 会话 ID
- `table_id` (str, required): 表格 ID
- `col_index` (int, required): 列索引（0-based）

**返回**: Markdown 格式响应

**示例**:
```python
# 删除第 1 列
docx_delete_col(session_id, "table_123", col_index=0)
```

#### 6.6.12 docx_fill_table

**功能**: 批量填充表格数据。

**参数**:
- `session_id` (str, required): 会话 ID
- `data` (str, required): JSON 格式的二维数组
- `table_id` (str, optional): 表格 ID。如果为空，使用最后创建的表格
- `start_row` (int, optional): 起始行索引。默认 0

**返回**: Markdown 格式响应

**示例**:
```python
import json

# 准备数据
data = json.dumps([
    ["Name", "Age", "City"],
    ["Alice", "30", "NYC"],
    ["Bob", "25", "LA"]
])

# 填充表格
docx_fill_table(session_id, data, table_id="table_123")

# 从第 2 行开始填充（跳过表头）
docx_fill_table(session_id, data, table_id="table_123", start_row=1)
```

#### 6.6.13 docx_copy_table

**功能**: 深拷贝表格（保留格式）。

**参数**:
- `session_id` (str, required): 会话 ID
- `table_id` (str, required): 源表格 ID
- `position` (str, required): 插入位置

**返回**: Markdown 格式响应，包含新表格 ID

**示例**:
```python
# 复制表格到文档末尾
new_table_id = docx_copy_table(
    session_id,
    "table_123",
    position="end:document_body"
)
```


### 6.7 Format Tools（格式化）

#### 6.7.1 docx_set_alignment

**功能**: 设置段落对齐方式。

**参数**:
- `session_id` (str, required): 会话 ID
- `paragraph_id` (str, required): 段落 ID
- `alignment` (str, required): 对齐方式（`left`, `center`, `right`, `justify`）

**返回**: Markdown 格式响应

**示例**:
```python
# 居中对齐
docx_set_alignment(session_id, "para_123", "center")

# 两端对齐
docx_set_alignment(session_id, "para_123", "justify")
```

#### 6.7.2 docx_set_properties

**功能**: 通用属性设置（JSON 格式）。

**参数**:
- `session_id` (str, required): 会话 ID
- `properties` (str, required): JSON 格式的属性字典
- `element_id` (str, optional): 元素 ID。如果为空，应用到最后创建的元素

**返回**: Markdown 格式响应

**示例**:
```python
import json

# 设置段落属性
properties = json.dumps({
    "alignment": "center",
    "line_spacing": 1.5
})
docx_set_properties(session_id, properties, element_id="para_123")
```

#### 6.7.3 docx_format_copy

**功能**: 复制格式（格式刷）。

**参数**:
- `session_id` (str, required): 会话 ID
- `source_id` (str, required): 源元素 ID
- `target_id` (str, required): 目标元素 ID

**返回**: Markdown 格式响应

**示例**:
```python
# 将 run_123 的格式复制到 run_456
docx_format_copy(session_id, source_id="run_123", target_id="run_456")

# 复制段落格式
docx_format_copy(session_id, source_id="para_123", target_id="para_456")
```

#### 6.7.4 docx_set_margins

**功能**: 设置页边距。

**参数**:
- `session_id` (str, required): 会话 ID
- `top` (float, optional): 上边距（英寸）
- `bottom` (float, optional): 下边距（英寸）
- `left` (float, optional): 左边距（英寸）
- `right` (float, optional): 右边距（英寸）

**返回**: Markdown 格式响应

**示例**:
```python
# 设置所有边距为 1 英寸
docx_set_margins(session_id, top=1.0, bottom=1.0, left=1.0, right=1.0)

# 只设置上下边距
docx_set_margins(session_id, top=0.5, bottom=0.5)
```

#### 6.7.5 docx_extract_format_template

**功能**: 提取元素的格式模板。

**参数**:
- `session_id` (str, required): 会话 ID
- `element_id` (str, required): 元素 ID

**返回**: JSON 格式的格式模板

**示例**:
```python
# 提取段落格式
template = docx_extract_format_template(session_id, "para_123")
```

#### 6.7.6 docx_apply_format_template

**功能**: 应用格式模板。

**参数**:
- `session_id` (str, required): 会话 ID
- `element_id` (str, required): 目标元素 ID
- `template_json` (str, required): JSON 格式的格式模板

**返回**: Markdown 格式响应

**示例**:
```python
# 提取格式
template = docx_extract_format_template(session_id, "para_123")

# 应用到其他段落
docx_apply_format_template(session_id, "para_456", template)
```

### 6.8 Advanced Tools（高级编辑）

#### 6.8.1 docx_replace_text

**功能**: 智能文本替换（支持跨 Run）。

**参数**:
- `session_id` (str, required): 会话 ID
- `old_text` (str, required): 要替换的文本
- `new_text` (str, required): 新文本
- `scope_id` (str, optional): 作用域元素 ID。如果为空，全文替换

**返回**: Markdown 格式响应，包含替换次数

**示例**:
```python
# 全文替换
docx_replace_text(session_id, "{{name}}", "Alice")

# 在指定段落内替换
docx_replace_text(session_id, "{{name}}", "Alice", scope_id="para_123")
```

**特性**:
- **Text Stitching**: 自动处理跨 Run 的文本（如 `{{na` 和 `me}}`）
- **格式保留**: 保留原有格式
- **智能匹配**: 支持部分匹配和完整匹配

#### 6.8.2 docx_batch_replace_text

**功能**: 批量文本替换。

**参数**:
- `session_id` (str, required): 会话 ID
- `replacements_json` (str, required): JSON 格式的替换映射
- `scope_id` (str, optional): 作用域元素 ID

**返回**: Markdown 格式响应，包含替换统计

**示例**:
```python
import json

# 准备替换映射
replacements = json.dumps({
    "{{name}}": "Alice",
    "{{date}}": "2026-01-27",
    "{{company}}": "Acme Corp"
})

# 批量替换
docx_batch_replace_text(session_id, replacements)
```

#### 6.8.3 docx_insert_image

**功能**: 插入图片。

**参数**:
- `session_id` (str, required): 会话 ID
- `image_path` (str, required): 图片文件路径
- `width` (float, optional): 宽度（英寸）
- `height` (float, optional): 高度（英寸）
- `position` (str, required): 插入位置

**返回**: Markdown 格式响应

**示例**:
```python
# 插入图片（自动缩放）
docx_insert_image(
    session_id,
    "/path/to/image.png",
    position="end:document_body"
)

# 指定尺寸
docx_insert_image(
    session_id,
    "/path/to/image.png",
    width=4.0,
    height=3.0,
    position="after:para_123"
)
```

### 6.9 Cursor Tools（光标定位）

#### 6.9.1 docx_cursor_get

**功能**: 获取当前光标位置。

**参数**:
- `session_id` (str, required): 会话 ID

**返回**: Markdown 格式响应，包含光标信息

**示例**:
```python
cursor_info = docx_cursor_get(session_id)
```

#### 6.9.2 docx_cursor_move

**功能**: 移动光标到指定位置。

**参数**:
- `session_id` (str, required): 会话 ID
- `element_id` (str, required): 目标元素 ID
- `position` (str, required): 位置（`before`, `after`, `inside`）

**返回**: Markdown 格式响应

**示例**:
```python
# 移动光标到段落之后
docx_cursor_move(session_id, element_id="para_123", position="after")

# 移动光标到表格内部
docx_cursor_move(session_id, element_id="table_456", position="inside")
```

### 6.10 Copy Tools（复制与元数据）

#### 6.10.1 docx_get_element_source

**功能**: 获取元素来源元数据。

**参数**:
- `session_id` (str, required): 会话 ID
- `element_id` (str, required): 元素 ID

**返回**: JSON 格式的元数据

**示例**:
```python
metadata = docx_get_element_source(session_id, "para_123")
```

#### 6.10.2 docx_copy_elements_range

**功能**: 复制元素区间。

**参数**:
- `session_id` (str, required): 会话 ID
- `start_id` (str, required): 起始元素 ID
- `end_id` (str, required): 结束元素 ID
- `position` (str, required): 插入位置

**返回**: Markdown 格式响应

**示例**:
```python
# 复制 para_123 到 para_456 之间的所有元素
docx_copy_elements_range(
    session_id,
    start_id="para_123",
    end_id="para_456",
    position="end:document_body"
)
```

### 6.11 Composite Tools（复合工具）⭐ 推荐优先使用

复合工具将多个原子操作组合成一个高层工具，大幅简化常见操作。

#### 6.11.1 docx_insert_formatted_paragraph

**功能**: 一步创建格式化段落。

**参数**:
- `session_id` (str, required): 会话 ID
- `text` (str, required): 段落文本
- `position` (str, required): 插入位置
- `bold` (bool, optional): 是否加粗。默认 `False`
- `italic` (bool, optional): 是否斜体。默认 `False`
- `size` (float, optional): 字体大小（磅）
- `color_hex` (str, optional): 颜色（十六进制，不含 `#`）
- `alignment` (str, optional): 对齐方式
- `style` (str, optional): 段落样式

**返回**: 段落 ID

**示例**:
```python
# 创建加粗红色居中文本
para_id = docx_insert_formatted_paragraph(
    session_id,
    "Important Notice",
    position="end:document_body",
    bold=True,
    size=16,
    color_hex="FF0000",
    alignment="center"
)
```

**效果**: 4 次调用 → 1 次调用

#### 6.11.2 docx_quick_edit

**功能**: 查找并编辑段落。

**参数**:
- `session_id` (str, required): 会话 ID
- `search_text` (str, required): 搜索文本
- `new_text` (str, optional): 新文本
- `bold` (bool, optional): 是否加粗
- `italic` (bool, optional): 是否斜体
- `size` (float, optional): 字体大小
- `color_hex` (str, optional): 颜色

**返回**: 编辑结果

**示例**:
```python
# 查找并编辑
docx_quick_edit(
    session_id,
    search_text="TODO",
    new_text="DONE",
    bold=True,
    color_hex="00FF00"
)
```

**效果**: N+1 次调用 → 1 次调用

#### 6.11.3 docx_get_structure_summary

**功能**: 轻量级结构提取。

**参数**:
- `session_id` (str, required): 会话 ID
- `max_headings` (int, optional): 最大标题数。默认 10
- `max_tables` (int, optional): 最大表格数。默认 5
- `max_paragraphs` (int, optional): 最大段落数。默认 0
- `include_content` (bool, optional): 是否包含内容。默认 `False`

**返回**: JSON 格式的摘要

**示例**:
```python
# 只获取标题和表格（减少 90% token 使用）
summary = docx_get_structure_summary(
    session_id,
    max_headings=10,
    max_tables=5,
    max_paragraphs=0
)
```

**效果**: Token 使用减少 90%

#### 6.11.4 docx_smart_fill_table

**功能**: 智能表格填充（自动扩展行）。

**参数**:
- `session_id` (str, required): 会话 ID
- `table_identifier` (str, required): 表格 ID 或搜索文本
- `data` (str, required): JSON 格式的二维数组
- `has_header` (bool, optional): 是否有表头。默认 `False`
- `auto_resize` (bool, optional): 是否自动扩展行。默认 `True`

**返回**: 填充结果

**示例**:
```python
import json

data = json.dumps([
    ["Name", "Age", "City"],
    ["Alice", "30", "NYC"],
    ["Bob", "25", "LA"]
])

# 通过文本查找表格并填充
docx_smart_fill_table(
    session_id,
    "Employee",  # 查找包含 "Employee" 的表格
    data,
    has_header=True,
    auto_resize=True
)
```

**效果**: 自动扩展行，无需手动计算

#### 6.11.5 docx_format_range

**功能**: 批量格式化范围。

**参数**:
- `session_id` (str, required): 会话 ID
- `start_text` (str, required): 起始文本
- `end_text` (str, required): 结束文本
- `bold` (bool, optional): 是否加粗
- `italic` (bool, optional): 是否斜体
- `size` (float, optional): 字体大小
- `color_hex` (str, optional): 颜色

**返回**: 格式化结果

**示例**:
```python
# 格式化从 "Chapter 1" 到 "Chapter 2" 之间的所有文本
docx_format_range(
    session_id,
    start_text="Chapter 1",
    end_text="Chapter 2",
    bold=True,
    size=14
)
```

### 6.12 System Tools（系统状态）

#### 6.12.1 docx_server_status

**功能**: 获取服务器状态和环境信息。

**参数**: 无

**返回**: JSON 格式的服务器状态

**示例**:
```python
status = docx_server_status()
```

**返回字段**:
- `status`: 服务器状态
- `version`: 版本号
- `cwd`: 当前工作目录
- `os_name`: 操作系统名称
- `python_version`: Python 版本
- `active_sessions`: 活动会话数
- `uptime_seconds`: 运行时间（秒）

#### 6.12.2 docx_get_log_level

**功能**: 获取当前日志级别。

**参数**: 无

**返回**: Markdown 格式响应，包含日志级别

**示例**:
```python
level = docx_get_log_level()
```

#### 6.12.3 docx_set_log_level

**功能**: 设置日志级别。

**参数**:
- `level` (str, required): 日志级别（`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`）

**返回**: Markdown 格式响应

**示例**:
```python
# 设置为 DEBUG 级别
docx_set_log_level("DEBUG")

# 设置为 INFO 级别
docx_set_log_level("INFO")
```

### 6.13 History Tools（历史记录）

#### 6.13.1 docx_get_history

**功能**: 获取会话操作历史。

**参数**:
- `session_id` (str, required): 会话 ID
- `max_entries` (int, optional): 最大条目数。默认全部

**返回**: JSON 格式的历史记录

**示例**:
```python
# 获取最近 10 条操作
history = docx_get_history(session_id, max_entries=10)
```

---

## 7. 最佳实践

### 7.1 文件管理策略

#### 推荐方式：使用 Launcher GUI

**优点**:
- 可视化文件选择
- 自动调用 HTTP API
- 支持文件状态监控
- 未保存更改提醒

**工作流**:
```
1. 启动服务器（Combined 模式）
   ↓
2. 打开 Launcher GUI
   ↓
3. 浏览并选择文件
   ↓
4. 点击 "Switch File"
   ↓
5. 在 Claude 中调用 docx_create()
```

#### 自动化场景：使用 HTTP API

**适用场景**:
- 批量处理脚本
- CI/CD 管道
- 定时任务

**示例**:
```python
import requests

def switch_file(file_path):
    response = requests.post("http://127.0.0.1:8080/api/file/switch", json={
        "path": file_path,
        "force": True
    })
    return response.status_code == 200

# 批量处理
for file in files:
    if switch_file(file):
        session_id = docx_create()
        # 处理文档...
        docx_save(session_id, file)
        docx_close(session_id)
```

### 7.2 会话生命周期管理

#### 标准工作流

```python
# 1. 创建会话
session_id = docx_create()

try:
    # 2. 执行操作
    para_id = docx_insert_paragraph(session_id, "Text", position="end:document_body")
    docx_set_font(session_id, run_id, bold=True)

    # 3. 保存文档
    docx_save(session_id, "./output.docx")

finally:
    # 4. 关闭会话（确保资源释放）
    docx_close(session_id)
```

#### 自动保存模式

```python
# 启用自动保存（需要先设置 active_file）
session_id = docx_create(auto_save=True)

# 每次修改后自动保存到 active_file
para_id = docx_insert_paragraph(session_id, "Text", position="end:document_body")
# 自动保存已触发

docx_close(session_id)
```

#### 备份策略

```python
# 启用备份
session_id = docx_create(
    backup_on_save=True,
    backup_dir="./backups",
    backup_suffix=".bak"
)

# 保存时自动创建备份
docx_save(session_id, "./output.docx")
# 备份文件: ./backups/output.docx.bak

docx_close(session_id)
```

### 7.3 错误处理

#### 解析 Markdown 响应

```python
import re

def is_success(response):
    return '**Status**: ✅ Success' in response

def is_error(response):
    return '**Status**: ❌ Error' in response

def extract_element_id(response):
    match = re.search(r'\*\*Element ID\*\*:\s*(\w+)', response)
    return match.group(1) if match else None

def extract_error_type(response):
    match = re.search(r'\*\*Error Type\*\*:\s*(\w+)', response)
    return match.group(1) if match else None

# 使用示例
response = docx_insert_paragraph(session_id, "Text", position="end:document_body")

if is_success(response):
    para_id = extract_element_id(response)
    print(f"Created paragraph: {para_id}")
else:
    error_type = extract_error_type(response)
    print(f"Error: {error_type}")
```

#### 常见错误类型

| 错误类型 | 说明 | 解决方案 |
|---------|------|---------|
| `SessionNotFound` | 会话不存在或已过期 | 重新创建会话 |
| `ElementNotFound` | 元素 ID 不存在 | 检查 ID 是否正确 |
| `InvalidElementType` | 元素类型不匹配 | 确认元素类型 |
| `ValidationError` | 参数验证失败 | 检查参数格式 |
| `FileNotFound` | 文件不存在 | 检查文件路径 |
| `SpecialIdNotInitialized` | 特殊 ID 未初始化 | 先执行相应操作 |

#### 错误处理模式

```python
def safe_insert_paragraph(session_id, text, position):
    """安全的段落插入（带错误处理）"""
    response = docx_insert_paragraph(session_id, text, position)

    if is_error(response):
        error_type = extract_error_type(response)

        if error_type == "SessionNotFound":
            # 重新创建会话
            session_id = docx_create()
            response = docx_insert_paragraph(session_id, text, position)
        elif error_type == "ValidationError":
            # 使用默认位置
            response = docx_insert_paragraph(session_id, text, "end:document_body")
        else:
            raise ValueError(f"Unhandled error: {error_type}")

    return extract_element_id(response)
```

### 7.4 性能优化

#### 使用复合工具

```python
# ❌ 不推荐：多次调用
para_id = docx_insert_paragraph(session_id, "", position="end:document_body")
run_id = docx_insert_run(session_id, "Text", position=f"inside:{para_id}")
docx_set_font(session_id, run_id, bold=True, size=14)
docx_set_alignment(session_id, para_id, "center")

# ✅ 推荐：使用复合工具
para_id = docx_insert_formatted_paragraph(
    session_id,
    "Text",
    position="end:document_body",
    bold=True,
    size=14,
    alignment="center"
)
```

#### 批量操作

```python
# ❌ 不推荐：逐个替换
docx_replace_text(session_id, "{{name}}", "Alice")
docx_replace_text(session_id, "{{date}}", "2026-01-27")
docx_replace_text(session_id, "{{company}}", "Acme Corp")

# ✅ 推荐：批量替换
import json
replacements = json.dumps({
    "{{name}}": "Alice",
    "{{date}}": "2026-01-27",
    "{{company}}": "Acme Corp"
})
docx_batch_replace_text(session_id, replacements)
```

#### 分页读取大文档

```python
# ❌ 不推荐：一次读取全部（可能超出 token 限制）
content = docx_read_content(session_id)

# ✅ 推荐：分页读取
page_size = 50
page = 0

while True:
    content = docx_read_content(
        session_id,
        max_paragraphs=page_size,
        start_from=page * page_size
    )

    if not content or content == "[Empty Document]":
        break

    # 处理内容...
    page += 1
```

#### 使用轻量级结构摘要

```python
# ❌ 不推荐：提取完整结构（token 使用高）
structure = docx_extract_template_structure(session_id)

# ✅ 推荐：使用轻量级摘要（token 减少 90%）
summary = docx_get_structure_summary(
    session_id,
    max_headings=10,
    max_tables=5,
    max_paragraphs=0,
    include_content=False
)
```

### 7.5 Position 定位技巧

#### 使用特殊 ID

```python
# 连续插入（使用 last_insert）
para1_id = docx_insert_paragraph(session_id, "First", position="end:document_body")
para2_id = docx_insert_paragraph(session_id, "Second", position="after:last_insert")
para3_id = docx_insert_paragraph(session_id, "Third", position="after:last_insert")
```

#### 使用光标定位

```python
# 移动光标到指定位置
docx_cursor_move(session_id, element_id="para_123", position="after")

# 使用光标位置插入
docx_insert_paragraph(session_id, "Text", position="after:cursor")
```

#### 相对定位

```python
# 在段落之前插入
docx_insert_paragraph(session_id, "Before", position="before:para_123")

# 在段落之后插入
docx_insert_paragraph(session_id, "After", position="after:para_123")

# 在容器内部插入
docx_insert_run(session_id, "Text", position="inside:para_123")
```

---

## 8. 故障排查

### 8.1 常见问题

#### Q1: 调用 docx_create() 返回 "No active file" 错误

**原因**: 未设置 `global_state.active_file`

**解决方案**:
1. 使用 Launcher GUI 选择文件
2. 或通过 HTTP API 切换文件：
   ```bash
   curl -X POST http://127.0.0.1:8080/api/file/switch \
     -H "Content-Type: application/json" \
     -d '{"path": "/path/to/file.docx"}'
   ```
3. 或启动服务器时指定文件：
   ```bash
   mcp-server-docx --transport combined --file /path/to/file.docx
   ```

#### Q2: 会话过期（SessionNotFound）

**原因**: 会话空闲超过 1 小时自动清理

**解决方案**:
- 重新创建会话：`session_id = docx_create()`
- 或调整会话 TTL（修改服务器配置）

#### Q3: 元素 ID 不存在（ElementNotFound）

**原因**: 
- 元素已被删除
- ID 拼写错误
- 使用了错误的会话

**解决方案**:
- 检查 ID 是否正确
- 确认元素未被删除
- 使用 `docx_get_context()` 查看可用元素

#### Q4: Position 格式错误（ValidationError）

**原因**: Position 格式不正确

**正确格式**: `mode:target_id`

**示例**:
```python
# ✅ 正确
position="after:para_123"
position="end:document_body"

# ❌ 错误
position="para_123"  # 缺少 mode
position="after"     # 缺少 target_id
```

#### Q5: 文件切换失败（409 Conflict）

**原因**: 当前会话有未保存更改

**解决方案**:
1. 保存当前会话：`docx_save(session_id, path)`
2. 或强制切换：
   ```bash
   curl -X POST http://127.0.0.1:8080/api/file/switch \
     -H "Content-Type: application/json" \
     -d '{"path": "/path/to/file.docx", "force": true}'
   ```

### 8.2 调试技巧

#### 启用 DEBUG 日志

```python
# 设置日志级别为 DEBUG
docx_set_log_level("DEBUG")

# 执行操作
para_id = docx_insert_paragraph(session_id, "Text", position="end:document_body")

# 查看详细日志
```

#### 查看服务器状态

```python
# 获取服务器状态
status = docx_server_status()
print(status)

# 查看活动会话
sessions = docx_list_sessions()
print(sessions)
```

#### 查看会话上下文

```python
# 获取会话上下文
context = docx_get_context(session_id)
print(context)

# 查看最后创建的元素
# 从 context 中提取 last_created_id
```

#### 查看 HTTP API 状态

```bash
# 查看活动文件和会话
curl http://127.0.0.1:8080/api/status

# 健康检查
curl http://127.0.0.1:8080/health
```

### 8.3 常见错误代码

| HTTP 状态码 | 说明 | 解决方案 |
|-----------|------|---------|
| 200 | 成功 | - |
| 400 | 请求参数错误 | 检查请求格式 |
| 404 | 文件或资源不存在 | 检查文件路径 |
| 409 | 冲突（有未保存更改）| 保存或使用 force=true |
| 500 | 服务器内部错误 | 查看服务器日志 |

### 8.4 获取帮助

- **GitHub Issues**: [提交问题](https://github.com/your-org/docx-mcp-server/issues)
- **开发文档**: [CLAUDE.md](../CLAUDE.md)
- **迁移指南**: [migration-v2-to-v3.md](./migration-v2-to-v3.md)
- **API 参考**: [README.md](../README.md)

---

## 附录

### A. 工具快速参考表

| 工具 | 功能 | 常用参数 |
|------|------|---------|
| `docx_create` | 创建会话 | `auto_save`, `backup_on_save` |
| `docx_save` | 保存文档 | `session_id`, `file_path` |
| `docx_close` | 关闭会话 | `session_id` |
| `docx_insert_paragraph` | 插入段落 | `session_id`, `text`, `position` |
| `docx_insert_formatted_paragraph` | 插入格式化段落 | `session_id`, `text`, `position`, `bold`, `size` |
| `docx_replace_text` | 文本替换 | `session_id`, `old_text`, `new_text` |
| `docx_insert_table` | 创建表格 | `session_id`, `rows`, `cols`, `position` |
| `docx_smart_fill_table` | 智能填充表格 | `session_id`, `table_identifier`, `data` |
| `docx_read_content` | 读取内容 | `session_id`, `max_paragraphs` |
| `docx_find_paragraphs` | 查找段落 | `session_id`, `query` |

### B. Position 模式速查

| 模式 | 说明 | 示例 |
|------|------|------|
| `after:ID` | 在元素之后 | `after:para_123` |
| `before:ID` | 在元素之前 | `before:para_123` |
| `inside:ID` | 在元素内部（末尾）| `inside:para_123` |
| `start:ID` | 在元素内部（开头）| `start:table_456` |
| `end:ID` | 在元素内部（末尾）| `end:document_body` |

### C. 特殊 ID 速查

| 特殊 ID | 说明 | 更新时机 |
|---------|------|---------|
| `last_insert` | 最后插入的元素 | `docx_insert_*` 成功后 |
| `last_update` | 最后更新的元素 | `docx_update_*`, `docx_set_*` 成功后 |
| `cursor` | 光标位置 | `docx_cursor_move` 调用后 |
| `document_body` | 文档主体 | 始终可用 |

### D. 错误类型速查

| 错误类型 | 说明 | 常见原因 |
|---------|------|---------|
| `SessionNotFound` | 会话不存在 | 会话过期或 ID 错误 |
| `ElementNotFound` | 元素不存在 | 元素已删除或 ID 错误 |
| `InvalidElementType` | 元素类型不匹配 | 对错误类型调用操作 |
| `ValidationError` | 参数验证失败 | 参数格式错误 |
| `FileNotFound` | 文件不存在 | 文件路径错误 |
| `SpecialIdNotInitialized` | 特殊 ID 未初始化 | 未执行相应操作 |

---

**文档版本**: v3.0
**最后更新**: 2026-01-27
**维护者**: docx-mcp-server 开发团队

