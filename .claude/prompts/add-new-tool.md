# Prompt: 添加新 MCP 工具

## 使用场景

当需要为 docx-mcp-server 添加新的文档操作功能时使用此模板。

## Prompt 模板

```
我需要为 docx-mcp-server 添加一个新工具：

功能描述：[描述新工具的功能，例如：添加图片到文档]

工具名称：docx_[operation_name]

参数：
- session_id: str (必需)
- [其他参数及类型]

返回值：[描述返回什么，element_id 或成功消息]

请帮我：
1. 在 src/docx_mcp_server/server.py 中实现这个工具
2. 在 tests/unit/ 中创建对应的单元测试
3. 更新 README.md 的工具列表
```

## 实现检查清单

实现新工具时，确保：

- [ ] 使用 `@mcp.tool()` 装饰器
- [ ] 添加完整的文档字符串（Args、Returns）
- [ ] 验证 session_id 存在性
- [ ] 如果创建新对象，使用 `session.register_object()`
- [ ] 使用明确的错误消息
- [ ] 编写至少 2 个单元测试（正常流程 + 错误处理）
- [ ] 更新 README.md

## 示例

### 需求
添加插入图片的功能

### 实现
```python
@mcp.tool()
def docx_insert_image(session_id: str, image_path: str, position: str, width_inches: float = None) -> str:
    """
    在文档中插入图片。

    Args:
        session_id: 会话 ID
        image_path: 图片文件的绝对路径
        position: 插入位置
        width_inches: 图片宽度（英寸），保持宽高比

    Returns:
        str: 成功消息
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    try:
        if width_inches:
            session.document.add_picture(image_path, width=Inches(width_inches))
        else:
            session.document.add_picture(image_path)
        return f"Picture added from {image_path}"
    except FileNotFoundError:
        raise ValueError(f"Image file not found: {image_path}")
```

### 测试
```python
def test_insert_image():
    session_id = docx_create()
    result = docx_insert_image(session_id, "/path/to/test.png", position="end:document_body", width_inches=3.0)
    assert "Picture added" in result
    docx_close(session_id)
```
