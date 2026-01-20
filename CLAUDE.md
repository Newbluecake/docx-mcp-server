# docx-mcp-server - Claude 开发指南

## 项目概述

docx-mcp-server 是一个基于 Model Context Protocol (MCP) 的服务器，为 Claude 提供细粒度的 Microsoft Word 文档操作能力。通过原子化的 API 设计，Claude 可以精确控制文档的每个元素。

### 核心目标

- **状态管理**：维护多个文档编辑会话，支持并发操作
- **原子化操作**：每个操作针对单一元素（段落、文本块、表格）
- **ID 映射系统**：将 python-docx 的内存对象映射为稳定的字符串 ID
- **MCP 协议兼容**：完全符合 MCP 规范，易于集成

## 核心架构

### 1. Session 管理机制

```
Client (Claude)
    ↓ docx_create()
SessionManager
    ↓ 创建 UUID
Session {
    session_id: "abc-123"
    document: Document()
    object_registry: {}
    last_accessed: timestamp
}
```

**关键特性**：
- 每个会话独立，互不干扰
- 自动过期机制（默认 1 小时）
- 支持显式关闭 `docx_close()`

**代码位置**：`src/docx_mcp_server/core/session.py`

### 2. 对象 ID 映射系统

这是本项目最关键的设计。python-docx 的对象（Paragraph、Run、Table）是临时的 Python 对象，没有稳定 ID。我们通过 `object_registry` 建立映射：

```python
# 创建段落时
paragraph = document.add_paragraph("Hello")
element_id = session.register_object(paragraph, "para")  # 返回 "para_a1b2c3d4"

# 后续操作时
paragraph = session.get_object("para_a1b2c3d4")
```

**ID 前缀约定**：
- `para_*` - 段落（Paragraph）
- `run_*` - 文本块（Run）
- `table_*` - 表格（Table）
- `cell_*` - 单元格（Cell）

### 3. 原子化操作设计

每个工具只做一件事，避免复杂的组合参数：

```python
# 不好的设计（过于复杂）
docx_add_formatted_paragraph(session_id, text, bold=True, size=14, alignment="center")

# 好的设计（原子化）
para_id = docx_add_paragraph(session_id, "Hello")
run_id = docx_add_run(session_id, para_id, "World")
docx_set_font(session_id, run_id, bold=True, size=14)
docx_set_alignment(session_id, para_id, "center")
```

**优势**：
- Claude 可以灵活组合操作
- 错误定位更精确
- 代码更易维护

## 开发指南

### 添加新工具

1. **在 `server.py` 中定义工具**

```python
@mcp.tool()
def docx_new_feature(session_id: str, param: str) -> str:
    """
    工具描述（Claude 会读取这个）

    Args:
        session_id: 会话 ID
        param: 参数说明

    Returns:
        str: 返回值说明
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    # 实现逻辑
    result = session.document.some_operation(param)

    # 如果创建了新对象，注册它
    if needs_tracking:
        return session.register_object(result, "prefix")

    return "Success message"
```

2. **编写单元测试**

在 `tests/unit/` 创建测试文件：

```python
def test_new_feature():
    session_id = docx_create()
    result = docx_new_feature(session_id, "test")
    assert "expected" in result
```

3. **更新文档**

- 在 `README.md` 的工具列表中添加
- 如果是重要功能，在本文件添加说明

### 测试策略

**单元测试**（`tests/unit/`）：
- 测试每个工具的基本功能
- 测试错误处理（无效 session_id、element_id）
- 测试边界条件

**E2E 测试**（`tests/e2e/`）：
- 模拟真实使用场景
- 测试工具组合使用
- 验证生成的 .docx 文件

**运行测试**：
```bash
./scripts/test.sh
```

### 调试技巧

1. **查看会话状态**

```python
# 在 server.py 临时添加
@mcp.tool()
def docx_debug_session(session_id: str) -> str:
    session = session_manager.get_session(session_id)
    return f"Objects: {list(session.object_registry.keys())}"
```

2. **检查对象类型**

```python
obj = session.get_object(element_id)
print(f"Type: {type(obj)}, Has add_run: {hasattr(obj, 'add_run')}")
```

3. **日志配置**

修改 `config/dev.yaml` 中的日志级别为 `DEBUG`

## MCP 协议注意事项

### 1. 工具命名规范

- 使用 `docx_` 前缀，避免与其他 MCP 服务器冲突
- 使用动词开头：`add`、`set`、`get`
- 保持简洁：`docx_add_paragraph` 而非 `docx_add_paragraph_to_document`

### 2. 错误处理

始终使用明确的错误消息：

```python
# 好的错误消息
raise ValueError(f"Session {session_id} not found or expired")
raise ValueError(f"Paragraph {para_id} not found in session")

# 不好的错误消息
raise Exception("Error")
```

### 3. 返回值设计

- 创建操作：返回 `element_id`
- 修改操作：返回成功消息
- 查询操作：返回数据或 `element_id`

### 4. 会话生命周期

```
创建 → 操作 → 保存 → 关闭
  ↓      ↓      ↓      ↓
create  add_*  save   close
        set_*
```

**重要**：提醒 Claude 在完成后调用 `docx_close()` 释放资源。

## 性能优化

### 1. 对象注册策略

不是所有对象都需要注册：

- **需要注册**：后续会引用的对象（段落、表格）
- **不需要注册**：一次性操作的结果

### 2. 会话清理

SessionManager 会自动清理过期会话，但在高负载场景下可以手动触发：

```python
session_manager.cleanup_expired()
```

### 3. 内存管理

- 限制单个会话的对象数量（考虑添加配置）
- 大文档操作完成后立即 `close`

## 贡献指南

### 代码风格

- 遵循 PEP 8
- 使用类型提示
- 文档字符串使用 Google 风格

### 提交规范

```
feat: 添加新工具 docx_add_image
fix: 修复表格单元格合并问题
docs: 更新 README 使用示例
test: 添加字体设置的单元测试
```

### Pull Request 流程

1. Fork 项目
2. 创建功能分支：`git checkout -b feat/new-tool`
3. 编写代码和测试
4. 运行 `./scripts/test.sh` 确保通过
5. 提交 PR，描述清楚改动内容

## 常见问题

### Q: 为什么不直接返回 python-docx 对象？

A: MCP 协议基于 JSON-RPC，无法传输 Python 对象。ID 映射是必需的。

### Q: 会话过期后数据会丢失吗？

A: 是的。必须在过期前调用 `docx_save()` 保存文件。

### Q: 可以同时编辑多个文档吗？

A: 可以。每个 `docx_create()` 创建独立的会话。

### Q: 如何处理大文档？

A: 考虑分批操作，及时保存，避免长时间持有会话。

## 相关资源

- [MCP 协议规范](https://modelcontextprotocol.io)
- [python-docx 文档](https://python-docx.readthedocs.io)
- [FastMCP 框架](https://github.com/jlowin/fastmcp)

## 快速参考

### 常用工具组合

**创建格式化文档**：
```python
session_id = docx_create()
para_id = docx_add_paragraph(session_id, "")
run_id = docx_add_run(session_id, para_id, "重要文本")
docx_set_font(session_id, run_id, bold=True, size=16, color_hex="FF0000")
docx_save(session_id, "/path/to/output.docx")
docx_close(session_id)
```

**创建表格**：
```python
table_id = docx_add_table(session_id, rows=3, cols=2)
cell_id = docx_get_cell(session_id, table_id, row=0, col=0)
docx_add_paragraph_to_cell(session_id, cell_id, "单元格内容")
```

---

**最后更新**：2026-01-20
