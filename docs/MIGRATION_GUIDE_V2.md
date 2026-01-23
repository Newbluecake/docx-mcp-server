# Markdown 响应格式迁移指南

**版本**: v2.0
**日期**: 2026-01-23
**状态**: 已完成

---

## 概述

docx-mcp-server v2.0 引入了重大变更：所有 MCP 工具现在返回 **Markdown 格式**的响应，替代了之前的 JSON 格式。这一变更带来了更好的可读性和可视化效果，同时保持了可解析性。

---

## 为什么改用 Markdown？

### 优势

1. **更好的可读性**：人类可以直接阅读响应内容
2. **ASCII 可视化**：使用 Unicode 框线字符展示文档结构
3. **上下文感知**：自动显示操作位置周围的文档元素
4. **Git diff 风格**：编辑操作显示修改前后的对比
5. **调试友好**：错误信息更清晰，易于理解

### 对比

| 特性 | JSON 格式 (v1.x) | Markdown 格式 (v2.0) |
|------|------------------|---------------------|
| 可读性 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 可视化 | ❌ | ✅ ASCII 图表 |
| 解析难度 | 简单 (json.loads) | 中等 (正则表达式) |
| 调试体验 | 一般 | 优秀 |
| 文件大小 | 小 | 中等 |

---

## 响应格式对比

### JSON 格式 (v1.x)

```json
{
  "status": "success",
  "message": "Paragraph created successfully",
  "data": {
    "element_id": "para_abc123",
    "cursor": {
      "element_id": "para_abc123",
      "position": "after",
      "parent_id": "document_body"
    }
  }
}
```

### Markdown 格式 (v2.0)

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

---

## 迁移步骤

### 1. 更新导入

**旧代码**:
```python
import json
```

**新代码**:
```python
import re
```

### 2. 更新响应解析

**旧代码**:
```python
result = docx_insert_paragraph(session_id, "Text", position="end:document_body")
data = json.loads(result)
para_id = data["data"]["element_id"]
```

**新代码**:
```python
result = docx_insert_paragraph(session_id, "Text", position="end:document_body")

# 提取元素 ID
match = re.search(r'\*\*Element ID\*\*:\s*(\w+)', result)
para_id = match.group(1) if match else None
```

### 3. 更新状态检查

**旧代码**:
```python
if data["status"] == "success":
    # 成功处理
else:
    # 错误处理
```

**新代码**:
```python
if '**Status**: ✅ Success' in result:
    # 成功处理
elif '**Status**: ❌ Error' in result:
    # 错误处理
```

### 4. 更新错误处理

**旧代码**:
```python
if data["status"] == "error":
    error_type = data["data"]["error_type"]
    error_msg = data["message"]
```

**新代码**:
```python
if '**Status**: ❌ Error' in result:
    # 提取错误类型
    match = re.search(r'\*\*Error Type\*\*:\s*(\w+)', result)
    error_type = match.group(1) if match else None

    # 提取错误消息
    match = re.search(r'\*\*Message\*\*:\s*(.+?)(?:\n|$)', result)
    error_msg = match.group(1) if match else "Unknown error"
```

---

## 辅助函数

为了简化迁移，我们提供了一组辅助函数（位于 `tests/helpers/markdown_extractors.py`）：

```python
from helpers import (
    extract_session_id,
    extract_element_id,
    extract_metadata_field,
    is_success,
    is_error
)

# 使用示例
result = docx_insert_paragraph(session_id, "Text", position="end:document_body")

if is_success(result):
    para_id = extract_element_id(result)
    print(f"Created paragraph: {para_id}")
else:
    error_type = extract_metadata_field(result, "error_type")
    print(f"Error: {error_type}")
```

### 可用函数

| 函数 | 说明 | 返回值 |
|------|------|--------|
| `extract_session_id(response)` | 提取 session ID | str 或 None |
| `extract_element_id(response)` | 提取 element ID | str 或 None |
| `extract_metadata_field(response, field_name)` | 提取任意元数据字段 | Any 或 None |
| `is_success(response)` | 检查是否成功 | bool |
| `is_error(response)` | 检查是否错误 | bool |
| `extract_error_message(response)` | 提取错误消息 | str 或 None |
| `has_metadata_field(response, field_name)` | 检查字段是否存在 | bool |

---

## 常见迁移场景

### 场景 1：创建文档

**旧代码**:
```python
result = docx_create()
data = json.loads(result)
session_id = data["data"]["session_id"]
```

**新代码**:
```python
result = docx_create()
session_id = extract_session_id(result)
```

### 场景 2：添加段落

**旧代码**:
```python
result = docx_insert_paragraph(session_id, "Text", position="end:document_body")
data = json.loads(result)
if data["status"] == "success":
    para_id = data["data"]["element_id"]
```

**新代码**:
```python
result = docx_insert_paragraph(session_id, "Text", position="end:document_body")
if is_success(result):
    para_id = extract_element_id(result)
```

### 场景 3：错误处理

**旧代码**:
```python
try:
    result = docx_update_paragraph_text(session_id, "invalid_id", "New text")
    data = json.loads(result)
    if data["status"] == "error":
        print(f"Error: {data['message']}")
except Exception as e:
    print(f"Exception: {e}")
```

**新代码**:
```python
result = docx_update_paragraph_text(session_id, "invalid_id", "New text")
if is_error(result):
    error_msg = extract_error_message(result)
    print(f"Error: {error_msg}")
```

### 场景 4：提取多个字段

**旧代码**:
```python
result = docx_get_context(session_id)
data = json.loads(result)
session_id = data["session_id"]
auto_save = data["auto_save"]
backup_on_save = data["backup_on_save"]
```

**新代码**:
```python
result = docx_get_context(session_id)
session_id = extract_metadata_field(result, "session_id")
auto_save = extract_metadata_field(result, "auto_save")
backup_on_save = extract_metadata_field(result, "backup_on_save")
```

---

## 测试迁移

### 更新测试文件

**旧测试**:
```python
def test_create_paragraph():
    session_id = docx_create()
    result = docx_insert_paragraph(session_id, "Test", position="end:document_body")
    data = json.loads(result)

    assert data["status"] == "success"
    assert "para_" in data["data"]["element_id"]
```

**新测试**:
```python
def test_create_paragraph():
    session_response = docx_create()
    session_id = extract_session_id(session_response)

    result = docx_insert_paragraph(session_id, "Test", position="end:document_body")

    assert is_success(result)
    para_id = extract_element_id(result)
    assert para_id.startswith("para_")
```

---

## 性能考虑

### 解析性能

| 操作 | JSON (v1.x) | Markdown (v2.0) | 差异 |
|------|-------------|-----------------|------|
| 解析时间 | ~0.1ms | ~0.3ms | +200% |
| 内存占用 | 小 | 中等 | +50% |
| 响应大小 | 小 | 大 | +100-300% |

**建议**：
- 对于性能敏感的场景，考虑缓存提取结果
- 使用编译后的正则表达式（`re.compile()`）提高性能
- 仅在需要时提取字段，避免不必要的解析

### 优化示例

```python
import re

# 编译正则表达式（一次性）
ELEMENT_ID_PATTERN = re.compile(r'\*\*Element ID\*\*:\s*(\w+)')
STATUS_SUCCESS_PATTERN = re.compile(r'\*\*Status\*\*:\s*✅ Success')

# 使用编译后的模式（多次）
def extract_element_id_fast(response):
    match = ELEMENT_ID_PATTERN.search(response)
    return match.group(1) if match else None

def is_success_fast(response):
    return STATUS_SUCCESS_PATTERN.search(response) is not None
```

---

## 故障排除

### 问题 1：提取不到元素 ID

**症状**：`extract_element_id()` 返回 `None`

**原因**：
- 响应格式不正确
- 工具返回了错误响应
- 字段名称拼写错误

**解决方案**：
```python
result = docx_insert_paragraph(session_id, "Text", position="end:document_body")
print(result)  # 打印完整响应查看格式

# 检查是否成功
if is_success(result):
    para_id = extract_element_id(result)
    if para_id is None:
        print("Warning: Element ID not found in response")
```

### 问题 2：正则表达式不匹配

**症状**：自定义正则表达式无法匹配字段

**原因**：
- 字段名称格式不正确
- 使用了错误的正则模式

**解决方案**：
```python
# 字段名称会自动转换为 Title Case
# 例如：error_type -> Error Type

# 正确的模式
pattern = r'\*\*Error Type\*\*:\s*(\w+)'

# 使用辅助函数更安全
error_type = extract_metadata_field(result, "error_type")
```

### 问题 3：测试失败

**症状**：迁移后测试失败

**原因**：
- 断言检查了 JSON 特定的字段
- 使用了 `json.loads()` 解析

**解决方案**：
1. 更新所有 `json.loads()` 调用
2. 使用辅助函数替代直接字段访问
3. 更新断言以检查 Markdown 格式

---

## 向后兼容性

**重要**：v2.0 **不向后兼容** v1.x 的 JSON 格式。

如果你需要同时支持两个版本：

```python
def extract_element_id_compat(response):
    """兼容 JSON 和 Markdown 格式"""
    # 尝试 Markdown 格式
    match = re.search(r'\*\*Element ID\*\*:\s*(\w+)', response)
    if match:
        return match.group(1)

    # 尝试 JSON 格式
    try:
        data = json.loads(response)
        return data.get("data", {}).get("element_id")
    except:
        return None
```

---

## 迁移检查清单

- [ ] 更新所有 `json.loads()` 调用
- [ ] 替换 `data["status"]` 检查为 `is_success()` / `is_error()`
- [ ] 替换 `data["data"]["element_id"]` 为 `extract_element_id()`
- [ ] 更新错误处理逻辑
- [ ] 更新测试文件
- [ ] 运行完整测试套件
- [ ] 更新文档和示例代码
- [ ] 通知团队成员关于格式变更

---

## 获取帮助

- **测试辅助函数**: `tests/helpers/markdown_extractors.py`
- **开发指南**: `CLAUDE.md`
- **API 文档**: `README.md`
- **问题反馈**: GitHub Issues

---

**最后更新**: 2026-01-23
**维护者**: AI Team
