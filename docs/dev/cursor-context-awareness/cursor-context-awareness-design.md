# 技术设计: Cursor Context Awareness

## 1. 架构设计

### 1.1 核心组件变更

本功能的核心逻辑将集中在 `Session` 类中，作为核心基础设施提供给各个工具使用。

#### Session 类扩展

```python
class Session:
    # ... 现有属性 ...

    # 新增：反向 ID 映射缓存 (用于快速查找元素 ID)
    # key: id(element._element) (lxml 元素的内存地址), value: element_id
    _element_id_cache: Dict[int, str] = field(default_factory=dict)

    def get_cursor_context(self, num_before: int = 2, num_after: int = 2) -> str:
        """获取光标周围的上下文信息"""
        # 实现逻辑...

    def _get_element_id(self, element: Any, auto_register: bool = True) -> str:
        """获取元素的 ID，如果不存在且 auto_register=True 则注册"""
        # 实现逻辑...

    def _get_siblings(self, parent: Any) -> List[Any]:
        """获取父容器下的所有子元素序列"""
        # 实现逻辑...
```

### 1.2 元素 ID 查找机制

由于 `python-docx` 的对象是 `lxml` 元素的包装器，不同的包装器实例可能指向同一个底层 XML 元素。为了准确映射 ID，我们将使用底层 `_element` 的内存地址作为唯一标识。

1. **注册时**：在 `register_object` 中，记录 `id(obj._element) -> obj_id` 到 `_element_id_cache`。
2. **查找时**：通过 `id(element._element)` 在缓存中查找。
3. **未命中**：如果元素未注册（如光标周围的现有元素），则自动调用 `register_object` 生成新 ID，以确保用户可以立即引用上下文中的元素。

### 1.3 上下文获取算法

1. **定位父容器**：
   - 从 `cursor.parent_id` 获取父对象。
   - 如果 cursor 无父 ID（文档开头），则使用 `document._body`。

2. **获取兄弟元素列表**：
   - 对于 `Document` 或 `Cell`，遍历其 `content` 元素（段落和表格）。
   - 利用 `python-docx` 的 `iter_child_elements()` (如果存在) 或直接遍历 `_element` 的子节点并封装回 `python-docx` 对象。
   - *优化*：为避免重复封装，优先在 `object_registry` 中查找已知对象。

3. **定位当前元素索引**：
   - 遍历兄弟列表，通过 `_element` 比较找到 `cursor.element_id` 对应的对象索引。

4. **截取窗口**：
   - 根据索引 `i`，取 `[i-num_before : i]` 和 `[i+1 : i+1+num_after]`。

5. **格式化输出**：
   - 生成符合需求格式的字符串。

## 2. 接口定义

### 2.1 Session.get_cursor_context

```python
def get_cursor_context(self, num_before: int = 2, num_after: int = 2) -> str:
    """
    生成光标位置的上下文描述。

    Returns:
        str: 包含光标位置、父容器信息（如果是嵌套结构）、以及前后元素的格式化文本。
        示例:
        Cursor: after Paragraph para_123
        Context:
          [-1] Paragraph para_prev: "Hello"
          [Current] Paragraph para_123: "World"
          [+1] Table table_456: "Table (2x2)"
    """
```

### 2.2 工具层集成

所有修改内容的工具（`add_*`, `update_*`, `delete`, `copy_*`）都将遵循以下模式：

```python
def docx_tool_name(session_id: str, ...):
    session = ...
    # ... 执行操作 ...

    # 成功后
    result_msg = "Operation successful."
    try:
        context = session.get_cursor_context()
        result_msg += f"\n\n{context}"
    except Exception as e:
        logger.warning(f"Failed to get cursor context: {e}")
        # 降级处理：不附加上下文，但不影响主要操作成功

    return result_msg
```

## 3. 边界情况处理

| 场景 | 行为 |
|------|------|
| **空文档** | 显示 "Cursor: at empty document start" |
| **文档开头** | 前置元素显示 `[Document Start]` |
| **文档结尾** | 后续元素显示 `[Document End]` |
| **表格单元格内** | 上下文限定在单元格内部，显示 `Parent: Cell ...` |
| **未知父容器** | 降级显示，不抛出异常 |
| **长文本** | 超过 50 字符截断并添加 "..."，换行符转空格 |

## 4. 数据结构变更

### Session 类

无需新增持久化字段，但需要维护运行时缓存 `_element_id_cache`。该缓存应在 `register_object` 时更新，在 `close_session` 时自动销毁。

注意：`_element_id_cache` 不需要序列化保存，因为加载文件时会重建 session，重新注册对象时会重建缓存。

## 5. 性能考量

- **缓存查找**：使用字典 `O(1)` 查找 ID。
- **兄弟遍历**：获取 `_element` 的子节点通常很快，但如果文档极大且在一个层级（如几万个段落），线性遍历寻找当前索引可能较慢。
- **优化策略**：
  - 如果 `len(siblings)` > 1000，考虑限制搜索范围或仅显示 "Context unavailable (too many siblings)"。
  - 对于本次迭代，暂定标准遍历，因大多数文档单层级元素数量可控。

## 6. 安全性

- 上下文信息仅用于展示，不包含敏感内部状态。
- 截断长文本防止日志爆炸或 Token 消耗过大。
