# docx-mcp-server 系统提示词指南

**版本**: v2.1+ | **更新**: 2026-01-23 | **核心**: 标准化 JSON 响应 & 复合工具优先

## 1. 核心机制

### 1.1 生命周期
```
create(创建) → add/edit(操作) → save(保存) → close(关闭)
```
*必须*在操作完成后调用 `docx_close(session_id)` 释放资源。

### 1.2 ID 系统与定位
*   **ID 前缀**: `para_*`(段落), `run_*`(文本), `table_*`(表格), `cell_*`(单元格)
*   **Position**: `end:document_body`, `after:para_id`, `inside:cell_id`
*   **Cursor**: 操作会自动更新光标，可使用 `after:last_created` (隐式) 或显式光标操作。

### 1.3 响应格式 (JSON)
所有工具返回 JSON，不要解析纯字符串，不要捕获异常。
```json
{
  "status": "success", // 或 "error"
  "message": "...",
  "data": {
    "element_id": "para_123",
    "cursor": { "context": "..." },
    "error_type": "ElementNotFound" // 仅在错误时
  }
}
```

## 2. 工具选择决策树 (⭐ = 优先使用)

根据用户需求选择最高效的工具路径：

*   **创建/加载**
    *   `docx_create` (新文档/加载模板)
*   **结构分析**
    *   快速预览 (Token少) → `docx_get_structure_summary` ⭐
    *   完整提取 (Token多) → `docx_extract_template_structure`
*   **添加内容**
    *   格式化段落 (一步完成) → `docx_insert_formatted_paragraph` ⭐
    *   普通段落/标题 → `docx_insert_paragraph` / `docx_insert_heading`
    *   表格/图片 → `docx_insert_table` / `docx_insert_image`
*   **修改内容**
    *   查找并改格式/文本 → `docx_quick_edit` ⭐
    *   替换占位符 (跨Run) → `docx_replace_text`
    *   批量替换 (性能高) → `docx_batch_replace_text`
    *   精准修改 → `docx_update_paragraph_text` / `docx_update_run_text`
*   **表格操作**
    *   智能填充 (自动扩行) → `docx_smart_fill_table` ⭐
    *   手动填充 → `docx_fill_table`
*   **格式化**
    *   批量区间格式化 → `docx_format_range` ⭐
    *   格式刷 → `docx_format_copy`
    *   细粒度设置 → `docx_set_font` / `docx_set_alignment`

## 3. 核心工具参考

### 3.1 复合工具 (Composite Tools) - 优先使用 ⭐

| 工具 | 签名 (关键参数) | 用途 |
|------|----------------|------|
| `docx_insert_formatted_paragraph` | `(session_id, text, position, bold, size, color_hex, alignment)` | 一步创建带格式段落 |
| `docx_quick_edit` | `(session_id, search_text, new_text, bold, color_hex)` | 查找文本并修改内容或格式 |
| `docx_get_structure_summary` | `(session_id, max_headings, max_tables, include_content=False)` | 低消耗获取文档大纲 |
| `docx_smart_fill_table` | `(session_id, table_identifier, data, auto_resize=True)` | 智能填充表格，自动处理行数 |
| `docx_format_range` | `(session_id, start_text, end_text, bold, size)` | 批量格式化两个文本之间的内容 |

### 3.2 基础内容工具

| 类别 | 工具 | 说明 |
|------|------|------|
| **会话** | `docx_create(file_path, auto_save)` | 创建/加载会话 |
| | `docx_save(session_id, file_path)` | 保存文档 |
| | `docx_close(session_id)` | **必须调用** |
| **段落** | `docx_insert_paragraph(session_id, text, position)` | 插入纯文本段落 |
| | `docx_insert_heading(session_id, text, position, level)` | 插入标题 |
| | `docx_update_paragraph_text(session_id, pid, text)` | 更新全段 (丢失格式) |
| | `docx_delete(session_id, element_id)` | 删除元素 |
| **Run** | `docx_insert_run(session_id, text, position)` | 在段落内插入文本 |
| | `docx_update_run_text(session_id, rid, text)` | 更新文本 (保留格式) |
| | `docx_set_font(session_id, rid, bold, size, color)` | 设置字体样式 |
| **高级** | `docx_replace_text(session_id, old, new, scope)` | 智能替换 (支持跨Run) |
| | `docx_batch_replace_text(session_id, map_json)` | 批量替换 (不支持跨Run) |
| | `docx_insert_image(session_id, path, position, w, h)` | 插入图片 |

### 3.3 表格工具

| 工具 | 说明 |
|------|------|
| `docx_insert_table(session_id, rows, cols, pos)` | 创建空表格 |
| `docx_get_table(session_id, index)` | 获取表格句柄 |
| `docx_find_table(session_id, text)` | 按内容查找表格 |
| `docx_fill_table(session_id, data_json, tid)` | 基础数据填充 |
| `docx_insert_table_row/col(session_id, pos)` | 插入行列 |
| `docx_get_cell(session_id, tid, row, col)` | 获取单元格 |
| `docx_insert_paragraph_to_cell(session_id, text, pos)` | 向单元格写内容 |

## 4. 常用代码模式

### 4.1 模板填充标准流
```python
session_id = docx_create(file_path="/path/template.docx")
try:
    # 1. 文本替换
    replacements = {"{{NAME}}": "Alice", "{{DATE}}": "2026-01-23"}
    docx_batch_replace_text(session_id, json.dumps(replacements))

    # 2. 表格填充 (自动扩充行)
    data = [["Item A", "100"], ["Item B", "200"]]
    docx_smart_fill_table(session_id, "Summary Table", json.dumps(data), auto_resize=True)

    docx_save(session_id, "/path/output.docx")
finally:
    docx_close(session_id)
```

### 4.2 从零创建文档
```python
session_id = docx_create()
try:
    # 标题
    docx_insert_formatted_paragraph(session_id, "Report", "end:document_body",
                                   bold=True, size=18, alignment="center")

    # 正文
    para_id = docx_insert_paragraph(session_id, "Introduction...", "end:document_body")

    # 插入表格
    docx_insert_table(session_id, rows=3, cols=2, position="end:document_body")

    docx_save(session_id, "/path/report.docx")
finally:
    docx_close(session_id)
```

### 4.3 错误处理模式
```python
result = docx_insert_paragraph(session_id, "Text", position="invalid")
data = json.loads(result)

if data["status"] == "error":
    etype = data["data"].get("error_type")
    if etype == "SessionNotFound":
        # 重建会话
        pass
    elif etype == "ElementNotFound":
        # 检查 ID
        pass
    print(f"Error: {data['message']}")
else:
    elem_id = data["data"]["element_id"]
```

## 5. 常见问题与最佳实践

1.  **Session Lost**: 会话默认 1 小时过期。如果在长任务中遇到 `SessionNotFound`，请重新调用 `docx_create`。
2.  **跨 Run 替换**: `docx_batch_replace_text` 速度快但不支持跨 Run。如果模板中的占位符如 `{{NAME}}` 被 Word 分割成了多个 XML 标签，必须使用 `docx_replace_text`。
3.  **格式丢失**: `docx_update_paragraph_text` 会重置段落格式。若要保留格式修改文本，请使用 `docx_update_run_text` 或 `docx_replace_text`。
4.  **Token 优化**: 不要在大文档上使用 `docx_extract_template_structure` 或 `docx_read_content` 读取全文。使用 `docx_get_structure_summary` 或分页读取。
5.  **路径**: 始终使用绝对路径。
