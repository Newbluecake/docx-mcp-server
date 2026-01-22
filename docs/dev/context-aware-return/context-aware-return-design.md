# 技术设计: Context Aware Return

## 1. 系统架构

### 1.1 现有架构分析
目前工具函数直接返回字符串（如 `element_id` 或 `Success message`）。最近的更改已在部分工具中通过拼接字符串（`f"{id}\n\n{context}"`）的方式加入了上下文信息，但这种非结构化的返回方式解析困难，且不统一。

### 1.2 目标架构
引入统一的响应格式化层，所有修改文档状态的工具将返回标准化的 JSON 字符串。

```python
{
  "status": "success",
  "message": "Paragraph created successfully",
  "data": {
    "element_id": "para_a1b2c3d4",
    "cursor": {
      "element_id": "para_a1b2c3d4",
      "position": "after",
      "context": "Cursor: after Paragraph para_a1b2c3d4\n..."
    }
  }
}
```

## 2. 组件设计

### 2.1 ResponseFormatter
在 `src/docx_mcp_server/core/response.py` 中定义响应结构和辅助函数。

```python
from dataclasses import dataclass, asdict
import json

@dataclass
class ToolResponse:
    status: str
    message: str
    data: dict

    def to_json(self) -> str:
        return json.dumps(asdict(self))
```

### 2.2 统一工具装饰器 (可选)
为了减少重复代码，可以设计一个装饰器 `@context_aware`，自动处理 Session 获取、异常捕获和 Context 注入。但考虑到工具参数各异，直接在工具内部调用 `ResponseFormatter` 可能更灵活。

### 2.3 上下文获取优化
`Session.get_cursor_context()` 保持不变，但其输出将被嵌入到 JSON 的 `data.cursor.context` 字段中，而不是直接拼接到消息末尾。

## 3. 接口变更

| 工具 | 当前返回 | 新返回 (JSON Schema) |
|------|----------|-------------------|
| `docx_add_paragraph` | `id` / `id\n\nContext` | `{status, data: {element_id, cursor}}` |
| `docx_add_table` | `id` / `id\n\nContext` | `{status, data: {element_id, cursor}}` |
| `docx_update_*` | `Message` / `Msg\n\nContext` | `{status, data: {element_id, changed_fields, cursor}}` |
| `docx_cursor_move` | `Msg\n\nContext` | `{status, data: {cursor}}` |

## 4. 兼容性策略
由于返回类型从 `str` (ID) 变为 `str` (JSON)，这对期望直接获取 ID 的客户端是破坏性变更。
策略：
- 这是一个明确的功能升级，要求客户端（Agent）能够解析 JSON。
- 在 `CLAUDE.md` 中更新文档，说明工具现在返回结构化数据。

## 5. 安全考量
- 确保 JSON 序列化时处理好特殊字符。
- 错误信息（Traceback）不应直接暴露在 `message` 中，应记录日志，返回友好提示。

