# Prompt: 调试会话问题

## 使用场景

当遇到会话相关的问题时使用此指南，例如：
- Session not found 错误
- Element ID 无效
- 会话意外过期

## 调试步骤

### 1. 验证会话是否存在

```
请帮我添加一个临时调试工具来检查会话状态：

@mcp.tool()
def docx_debug_info(session_id: str) -> str:
    session = session_manager.get_session(session_id)
    if not session:
        return f"Session {session_id} not found"

    return f"""
    Session ID: {session.session_id}
    Created: {session.created_at}
    Last accessed: {session.last_accessed}
    Registered objects: {len(session.object_registry)}
    Object IDs: {list(session.object_registry.keys())}
    """
```

### 2. 检查对象注册表

如果 element_id 无效，检查对象是否被正确注册：

```python
# 在工具中添加日志
import logging
logger = logging.getLogger(__name__)

@mcp.tool()
def docx_add_paragraph(session_id: str, text: str, style: str = None) -> str:
    session = session_manager.get_session(session_id)
    paragraph = session.document.add_paragraph(text, style=style)
    element_id = session.register_object(paragraph, "para")
    logger.debug(f"Registered paragraph: {element_id}")  # 添加日志
    return element_id
```

### 3. 检查会话超时配置

查看 `config/dev.yaml` 中的 `session_ttl_seconds` 设置。

如果操作时间较长，考虑：
- 增加超时时间
- 在长操作中定期"touch"会话

### 4. 验证对象类型

```python
obj = session.get_object(element_id)
if not obj:
    raise ValueError(f"Object {element_id} not found")

# 检查类型
if not hasattr(obj, 'expected_method'):
    raise ValueError(f"Object {element_id} is not the expected type")
```

## 常见问题

### Q: "Session not found" 但刚创建

**可能原因**：
- session_id 传递错误（复制粘贴问题）
- 会话已过期（检查时间戳）

**解决方法**：
```
请检查：
1. session_id 是否完整（UUID 格式）
2. 创建和使用之间的时间间隔
3. SessionManager 的 ttl_seconds 配置
```

### Q: Element ID 无效

**可能原因**：
- 对象未注册
- ID 拼写错误
- 跨会话使用 ID

**解决方法**：
```
请验证：
1. 创建对象的工具是否调用了 register_object()
2. element_id 是否来自正确的会话
3. 使用 docx_debug_info() 查看所有已注册对象
```

### Q: 会话频繁过期

**解决方法**：
```
请修改 config/dev.yaml：

session:
  ttl_seconds: 7200  # 增加到 2 小时
```

## Prompt 模板

```
我遇到了会话问题：

错误信息：[粘贴完整错误]

操作序列：
1. docx_create() -> session_id: xxx
2. docx_add_paragraph(session_id, "test") -> para_id: yyy
3. [出错的操作]

请帮我：
1. 分析可能的原因
2. 添加调试日志
3. 提供解决方案
```
