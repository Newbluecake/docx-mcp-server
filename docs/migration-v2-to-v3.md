# docx-mcp-server v2.x → v3.0 迁移指南

## 概述

v3.0 版本引入了**全局单文件模式**和**HTTP API 文件管理**，重构了文件选择和会话创建的架构。这是一次重大的 Breaking Change，旨在简化文件管理并支持 GUI 启动器集成。

**发布日期**: 2026-01-26
**影响范围**: 所有使用 `docx_create()` 和 `docx_list_files()` 的代码

---

## Breaking Changes 列表

### 1. ❌ `docx_create(file_path=...)` 参数移除

**变更类型**: 函数签名变更（Breaking）

#### v2.x 旧 API
```python
# 创建空白文档
session_id = docx_create()

# 加载现有文档
session_id = docx_create(file_path="/path/to/template.docx")

# 启用自动保存
session_id = docx_create(file_path="/path/to/doc.docx", auto_save=True)
```

#### v3.0 新 API
```python
# 创建空白文档（无变化）
session_id = docx_create()

# 加载现有文档（新方式）
# 方式 1: 使用 Launcher GUI 选择文件
# Launcher 会调用 POST /api/file/switch 设置活动文件

# 方式 2: 使用 CLI 参数启动服务器
# mcp-server-docx --transport combined --file /path/to/template.docx

# 然后创建会话（使用全局活动文件）
session_id = docx_create()

# 启用自动保存（file_path 从全局状态获取）
session_id = docx_create(auto_save=True)
```

#### 迁移步骤

1. **识别所有 `docx_create(file_path=...)` 调用**
   ```bash
   grep -r "docx_create(file_path=" your_project/
   ```

2. **决定文件设置方式**
   - **交互式场景**: 使用 Launcher GUI（推荐）
   - **自动化脚本**: 使用 `--file` CLI 参数
   - **动态切换**: 调用 HTTP API `/api/file/switch`

3. **更新代码**
   ```python
   # 旧代码
   session_id = docx_create(file_path="/path/to/doc.docx")

   # 新代码（假设已通过 Launcher 或 CLI 设置文件）
   session_id = docx_create()
   ```

---

### 2. ❌ `docx_list_files()` 工具移除

**变更类型**: 工具移除（Breaking）

#### v2.x 旧 API
```python
import json

# 列出当前目录的 .docx 文件
files = json.loads(docx_list_files())
print(f"Found {len(files)} documents")

# 列出指定目录
files = json.loads(docx_list_files(directory="./templates"))
for filename in files:
    print(f"- {filename}")
```

#### v3.0 新方式
```python
# 使用 Launcher GUI 的文件浏览器
# - Launcher 提供可视化文件选择界面
# - 自动调用 /api/file/switch 设置活动文件
# - 无需编写文件列表代码

# 或者，如果需要编程方式列出文件
import os
files = [f for f in os.listdir("./templates") if f.endswith(".docx")]
```

#### 迁移步骤

1. **识别所有 `docx_list_files()` 调用**
   ```bash
   grep -r "docx_list_files" your_project/
   ```

2. **替换为合适的方案**
   - **交互式场景**: 使用 Launcher GUI 文件浏览器
   - **自动化脚本**: 使用 Python `os.listdir()` 或 `pathlib`

---

### 3. ✅ 新增 HTTP REST API

**变更类型**: 功能新增（非 Breaking）

v3.0 引入了 HTTP REST API，用于集中管理文件和会话：

#### API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/file/switch` | POST | 切换当前活动文件 |
| `/api/status` | GET | 获取服务器状态（活动文件、会话等）|
| `/api/session/close` | POST | 关闭指定会话 |
| `/health` | GET | 健康检查 |

#### 示例：通过 HTTP API 切换文件

```python
import requests

# 切换活动文件
response = requests.post("http://127.0.0.1:8080/api/file/switch", json={
    "path": "/path/to/document.docx",
    "force": False  # 如果有未保存更改，是否强制切换
})

if response.status_code == 200:
    data = response.json()
    print(f"Current file: {data['currentFile']}")
elif response.status_code == 409:
    # 有未保存更改
    print("Unsaved changes detected. Use force=true to override.")
elif response.status_code == 404:
    print("File not found")
```

#### 示例：查询服务器状态

```python
response = requests.get("http://127.0.0.1:8080/api/status")
status = response.json()

print(f"Active file: {status['activeFile']}")
print(f"Active session: {status['activeSessionId']}")
print(f"Has unsaved changes: {status.get('hasUnsavedChanges', False)}")
```

---

### 4. ✅ 新增 Combined 传输模式

**变更类型**: 功能新增（非 Breaking）

v3.0 新增 `combined` 传输模式，同时提供 REST API 和 MCP Server：

```bash
# 启动 Combined 模式
mcp-server-docx --transport combined

# 指定初始文件
mcp-server-docx --transport combined --file /path/to/document.docx

# 指定 host 和 port
mcp-server-docx --transport combined --host 0.0.0.0 --port 8080
```

**Combined 模式特性**：
- **REST API**: 监听在 `/api/*`
- **MCP Server**: 挂载在 `/mcp`
- **Health Check**: `/health` 端点

---

## 迁移场景示例

### 场景 1: 交互式文档编辑

**v2.x 旧代码**:
```python
import json

# 列出文件
files = json.loads(docx_list_files(directory="./templates"))
print("Available templates:")
for i, file in enumerate(files):
    print(f"{i+1}. {file}")

# 用户选择
choice = int(input("Select template: ")) - 1
file_path = f"./templates/{files[choice]}"

# 加载文档
session_id = docx_create(file_path=file_path)

# 编辑...
docx_replace_text(session_id, "{{name}}", "Alice")

# 保存
docx_save(session_id, "./output.docx")
docx_close(session_id)
```

**v3.0 新代码**:
```python
# 方式 1: 使用 Launcher GUI（推荐）
# 1. 打开 Launcher，浏览并选择模板文件
# 2. Launcher 自动调用 /api/file/switch 设置活动文件
# 3. 在代码中直接创建会话

# 创建会话（使用 Launcher 选择的文件）
session_id = docx_create()

# 编辑...
docx_replace_text(session_id, "{{name}}", "Alice")

# 保存
docx_save(session_id, "./output.docx")
docx_close(session_id)
```

---

### 场景 2: 自动化批处理

**v2.x 旧代码**:
```python
import json

# 列出所有模板
files = json.loads(docx_list_files(directory="./templates"))

for file in files:
    file_path = f"./templates/{file}"

    # 加载文档
    session_id = docx_create(file_path=file_path)

    # 处理...
    docx_replace_text(session_id, "{{year}}", "2026")

    # 保存
    output_path = f"./output/{file}"
    docx_save(session_id, output_path)
    docx_close(session_id)
```

**v3.0 新代码**:
```python
import os
import requests

# 使用标准 Python 列出文件
files = [f for f in os.listdir("./templates") if f.endswith(".docx")]

for file in files:
    file_path = f"./templates/{file}"

    # 通过 HTTP API 切换活动文件
    response = requests.post("http://127.0.0.1:8080/api/file/switch", json={
        "path": os.path.abspath(file_path),
        "force": True
    })

    if response.status_code != 200:
        print(f"Failed to switch to {file}")
        continue

    # 创建会话（使用刚切换的文件）
    session_id = docx_create()

    # 处理...
    docx_replace_text(session_id, "{{year}}", "2026")

    # 保存
    output_path = f"./output/{file}"
    docx_save(session_id, output_path)
    docx_close(session_id)
```

---

### 场景 3: 测试代码更新

**v2.x 旧测试代码**:
```python
import pytest
from docx_mcp_server.server import docx_create, docx_save, docx_close

def test_template_loading(tmp_path):
    # 创建测试文件
    template_path = tmp_path / "template.docx"
    doc = Document()
    doc.add_paragraph("Hello {{name}}")
    doc.save(str(template_path))

    # 测试加载
    session_id = docx_create(file_path=str(template_path))
    # ... 测试逻辑 ...
    docx_close(session_id)
```

**v3.0 新测试代码**:
```python
import pytest
from docx_mcp_server.server import docx_create, docx_save, docx_close
from docx_mcp_server.core.global_state import global_state

def test_template_loading(tmp_path):
    # 创建测试文件
    template_path = tmp_path / "template.docx"
    doc = Document()
    doc.add_paragraph("Hello {{name}}")
    doc.save(str(template_path))

    # 设置全局活动文件
    global_state.active_file = str(template_path)

    # 测试加载
    session_id = docx_create()
    # ... 测试逻辑 ...
    docx_close(session_id)

    # 清理
    global_state.active_file = None
```

**或使用测试辅助函数**:
```python
from tests.helpers import create_session_with_file, clear_active_file

def test_template_loading(tmp_path):
    # 创建测试文件
    template_path = tmp_path / "template.docx"
    doc = Document()
    doc.add_paragraph("Hello {{name}}")
    doc.save(str(template_path))

    # 使用辅助函数（内部设置 global_state.active_file）
    session_response = create_session_with_file(str(template_path))
    session_id = extract_session_id(session_response)

    # ... 测试逻辑 ...
    docx_close(session_id)

    # 清理
    clear_active_file()
```

---

## 迁移检查清单

### 代码层面

- [ ] 搜索并替换所有 `docx_create(file_path=...)` 调用
- [ ] 移除所有 `docx_list_files()` 调用
- [ ] 决定文件设置方式（Launcher / CLI / HTTP API）
- [ ] 更新单元测试（使用 `global_state.active_file` 或测试辅助函数）
- [ ] 更新 E2E 测试
- [ ] 更新文档和示例代码

### 部署层面

- [ ] 更新服务器启动脚本（考虑使用 `--transport combined`）
- [ ] 如果使用自动化脚本，添加 `--file` 参数或 HTTP API 调用
- [ ] 更新 CI/CD 管道（如涉及）
- [ ] 通知团队成员 Breaking Changes

### 用户体验层面

- [ ] 安装或更新 Launcher GUI（如适用）
- [ ] 培训用户使用新的文件选择方式
- [ ] 更新用户手册和内部文档

---

## 常见问题

### Q1: 为什么移除 `file_path` 参数？

**A**: 为了支持 Launcher GUI 集中管理文件，避免 Claude 直接操作文件路径。新架构将文件管理和文档操作解耦，提高了灵活性和安全性。

### Q2: 我的自动化脚本怎么办？

**A**: 使用 `--file` CLI 参数或 HTTP API `/api/file/switch`。两种方式都支持编程式文件切换。

### Q3: 能否同时操作多个文件？

**A**: v3.0 采用全局单文件模式，每次只能操作一个活动文件。如需操作多个文件，需要：
1. 切换文件（HTTP API 或 CLI 重启）
2. 创建会话
3. 处理完成后关闭会话
4. 重复上述步骤

### Q4: 测试代码如何快速迁移？

**A**: 使用提供的测试辅助函数：
```python
from tests.helpers import create_session_with_file, clear_active_file

# 代替 docx_create(file_path=X)
session_response = create_session_with_file("/path/to/file.docx")
```

### Q5: HTTP API 的安全性如何？

**A**:
- 默认绑定 `127.0.0.1`（仅本机访问）
- 支持路径安全检查（`validate_path_safety`）
- 检查文件权限（只读/只写检测）
- 检查文件锁（避免并发冲突）
- 未保存更改保护（需 `force=true` 覆盖）

### Q6: 如何回退到 v2.x？

**A**:
```bash
pip install docx-mcp-server==2.x.x
```
建议在充分测试后再升级到 v3.0。

---

## 获取帮助

- **GitHub Issues**: [提交问题](https://github.com/your-org/docx-mcp-server/issues)
- **迁移指南**: [docs/migration-v2-to-v3.md](./migration-v2-to-v3.md)
- **开发文档**: [CLAUDE.md](../CLAUDE.md)

---

**更新日期**: 2026-01-26
**版本**: v3.0.0
