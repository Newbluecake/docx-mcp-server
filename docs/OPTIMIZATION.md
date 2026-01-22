# 工具优化说明 (v2.0)

> 本次更新针对大模型使用体验进行了全面优化

## 🎯 优化目标

1. **减少多步操作** - 常见任务一步完成
2. **降低 Token 消耗** - 可控的返回信息量
3. **改善工具发现性** - 按使用场景分组

## ✨ 新增功能

### 1. 复合工具 (Composite Tools)

5 个新的高层工具，将多步操作合并为一步：

#### 📝 `docx_add_formatted_paragraph`
一步创建带格式的段落

**之前**:
```python
para_id = docx_add_paragraph(session_id, "")
run_id = docx_add_run(session_id, "Important!", paragraph_id=para_id)
docx_set_font(session_id, run_id, bold=True, size=14, color_hex="FF0000")
docx_set_alignment(session_id, para_id, "center")
```

**现在**:
```python
para_id = docx_add_formatted_paragraph(
    session_id, "Important!",
    bold=True, size=14, color_hex="FF0000", alignment="center"
)
```

**效果**: 4 次调用 → 1 次调用 (减少 75%)

#### 🔍 `docx_quick_edit`
查找并编辑段落

**之前**:
```python
matches = docx_find_paragraphs(session_id, "old text")
for match in json.loads(matches):
    docx_update_paragraph_text(session_id, match["id"], "new text")
```

**现在**:
```python
result = docx_quick_edit(session_id, "old text", new_text="new text", bold=True)
```

**效果**: N+1 次调用 → 1 次调用

#### 📊 `docx_get_structure_summary`
轻量级文档结构提取

**之前**:
```python
structure = docx_extract_template_structure(session_id)  # 返回 ~2000 tokens
```

**现在**:
```python
summary = docx_get_structure_summary(
    session_id,
    max_headings=10,
    max_tables=5,
    max_paragraphs=0  # 不返回普通段落
)  # 返回 ~200 tokens
```

**效果**: Token 使用减少 90%

#### 📋 `docx_smart_fill_table`
智能表格填充

**之前**:
```python
table_id = docx_find_table(session_id, "Employee")
# 手动检查行数，添加行
for i in range(rows_needed - existing_rows):
    docx_add_table_row(session_id, table_id)
docx_fill_table(session_id, data, table_id)
```

**现在**:
```python
result = docx_smart_fill_table(
    session_id, "Employee", data,
    has_header=True, auto_resize=True
)
```

**效果**: 自动扩展行，无需手动计算

#### 🎨 `docx_format_range`
批量格式化段落范围

**之前**:
```python
# 手动查找范围内的所有段落
# 逐个格式化
```

**现在**:
```python
result = docx_format_range(
    session_id, "Chapter 1", "Chapter 2",
    bold=True, size=14
)
```

**效果**: 批量操作，一次完成

### 2. 优化现有工具

#### `docx_read_content` - 支持分页

```python
# 读取前 10 段
content = docx_read_content(session_id, max_paragraphs=10)

# 读取第 10-20 段
content = docx_read_content(session_id, max_paragraphs=10, start_from=10)
```

**效果**: 大文档不再一次性返回所有内容

#### `docx_find_paragraphs` - 限制结果数量

```python
# 只返回前 5 个匹配
matches = docx_find_paragraphs(session_id, "test", max_results=5)
```

**效果**: 避免返回过多结果

#### `docx_extract_template_structure` - 可配置详细程度

```python
# 只返回结构，不返回内容
structure = docx_extract_template_structure(
    session_id,
    include_content=False
)

# 限制每种类型的数量
structure = docx_extract_template_structure(
    session_id,
    max_items_per_type='{"headings": 10, "tables": 5, "paragraphs": 0}'
)
```

**效果**: Token 使用可控，按需返回

### 3. 增强上下文机制

Session 类新增上下文栈支持：

```python
# 推入上下文
session.push_context(element_id)

# 获取当前上下文
current = session.get_current_context()

# 弹出上下文
element_id = session.pop_context()
```

**用途**: 支持嵌套操作，更灵活的上下文管理

## 📊 性能对比

| 操作 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 创建格式化段落 | 4 次调用 | 1 次调用 | 75% ↓ |
| 查找并编辑 | N+1 次调用 | 1 次调用 | ~90% ↓ |
| 提取文档结构 | ~2000 tokens | ~200 tokens | 90% ↓ |
| 填充表格 | 3-5 次调用 | 1 次调用 | 70% ↓ |

## 🗂️ 新的工具分组

工具现在按使用场景分组（在文档中体现）：

```
📝 快速编辑 (最常用)
  - docx_quick_edit (新)
  - docx_replace_text
  - docx_batch_replace_text
  - docx_find_paragraphs

✨ 创建内容
  - docx_add_formatted_paragraph (新)
  - docx_add_heading
  - docx_add_table
  - docx_smart_fill_table (新)

🔍 文档分析
  - docx_get_structure_summary (新)
  - docx_read_content (改进)
  - docx_find_table

🎨 格式化
  - docx_format_range (新)
  - docx_set_font
  - docx_format_copy

⚙️ 高级操作 (原子工具)
  - docx_add_run
  - docx_get_cell
  - docx_cursor_move
  ...
```

## 🔄 向后兼容

所有现有工具保持不变，新增的参数都是可选的：

```python
# 旧代码仍然有效
content = docx_read_content(session_id)

# 新代码可以使用新参数
content = docx_read_content(session_id, max_paragraphs=10)
```

## 📝 使用建议

### 对于 Claude

1. **优先使用复合工具** - 对于常见场景，使用 `docx_add_formatted_paragraph`、`docx_quick_edit` 等
2. **控制返回信息** - 使用 `max_paragraphs`、`max_results` 等参数限制返回量
3. **按需提取结构** - 使用 `docx_get_structure_summary` 而非 `docx_extract_template_structure`

### 对于开发者

1. **保留原子工具** - 复杂场景仍需要精细控制
2. **组合使用** - 复合工具 + 原子工具可以覆盖所有场景
3. **测试覆盖** - 新增 10 个单元测试，覆盖所有新功能

## 🚀 下一步

可能的进一步优化：

1. **更多复合工具** - 根据实际使用反馈添加
2. **智能推荐** - 工具描述中提示相关工具
3. **批量操作** - 支持一次操作多个元素

## 📚 相关文档

- [完整工具列表](README.md#工具列表)
- [开发指南](CLAUDE.md)
- [测试用例](tests/unit/test_composite_tools.py)
