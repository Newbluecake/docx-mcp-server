# Prompt: 性能优化

## 使用场景

当遇到性能问题时使用此指南：
- 内存占用过高
- 会话响应变慢
- 大文档处理缓慢

## 优化策略

### 1. 对象注册优化

**问题**：每个对象都注册会导致内存膨胀

**解决方案**：
```
请分析哪些对象真正需要注册：

需要注册：
- 后续会引用的对象（段落、表格、单元格）
- 需要修改的对象（Run 用于格式化）

不需要注册：
- 一次性操作的结果
- 不会再次访问的临时对象

示例：
# 不好
run_id = docx_add_run(session_id, para_id, "text")  # 如果不需要格式化，不必返回 ID

# 好
docx_add_run_simple(session_id, para_id, "text")  # 返回 "Success"，不注册对象
```

### 2. 会话清理策略

**添加主动清理工具**：
```python
@mcp.tool()
def docx_cleanup_sessions() -> str:
    """清理所有过期会话"""
    session_manager.cleanup_expired()
    return f"Active sessions: {len(session_manager.sessions)}"
```

### 3. 批量操作优化

**问题**：逐个添加大量段落效率低

**解决方案**：
```
请添加批量操作工具：

@mcp.tool()
def docx_add_paragraphs_batch(session_id: str, texts: list[str]) -> str:
    """批量添加段落，不返回 ID"""
    session = session_manager.get_session(session_id)
    for text in texts:
        session.document.add_paragraph(text)
    return f"Added {len(texts)} paragraphs"
```

### 4. 配置优化

**开发环境**（`config/dev.yaml`）：
```yaml
session:
  ttl_seconds: 1800  # 30 分钟，快速释放
  max_sessions: 10   # 限制并发会话
  max_objects_per_session: 1000  # 限制对象数量
```

**生产环境**（`config/prod.yaml`）：
```yaml
session:
  ttl_seconds: 3600  # 1 小时
  max_sessions: 50
  max_objects_per_session: 5000
```

## 性能监控

### 添加监控工具

```python
@mcp.tool()
def docx_stats() -> str:
    """获取服务器统计信息"""
    total_sessions = len(session_manager.sessions)
    total_objects = sum(
        len(s.object_registry) for s in session_manager.sessions.values()
    )
    return f"""
    Active sessions: {total_sessions}
    Total objects: {total_objects}
    Avg objects per session: {total_objects / total_sessions if total_sessions > 0 else 0:.1f}
    """
```

## 大文档处理最佳实践

### 策略 1：分段保存

```python
# 每处理 100 个段落就保存一次
for i, text in enumerate(large_text_list):
    docx_add_paragraph(session_id, text)
    if i % 100 == 0:
        docx_save(session_id, f"/tmp/checkpoint_{i}.docx")
```

### 策略 2：使用简化工具

```
请为大文档场景添加简化工具：

@mcp.tool()
def docx_add_content_simple(session_id: str, content: str) -> str:
    """添加纯文本内容，不注册对象，适合大文档"""
    session = session_manager.get_session(session_id)
    for line in content.split('\n'):
        session.document.add_paragraph(line)
    return "Content added"
```

### 策略 3：及时关闭会话

```python
# 完成后立即关闭
docx_save(session_id, output_path)
docx_close(session_id)  # 释放内存
```

## Prompt 模板

```
我遇到了性能问题：

场景：[描述使用场景，如：生成 100 页的报告]

问题表现：
- 内存占用：[如：2GB]
- 响应时间：[如：每个操作 5 秒]

请帮我：
1. 分析性能瓶颈
2. 提供优化方案
3. 添加性能监控工具
```

## 性能基准

**正常指标**：
- 单会话内存：< 50MB
- 对象注册：< 1000 个/会话
- 操作响应：< 100ms

**需要优化的信号**：
- 单会话内存：> 200MB
- 对象注册：> 5000 个/会话
- 操作响应：> 1s
