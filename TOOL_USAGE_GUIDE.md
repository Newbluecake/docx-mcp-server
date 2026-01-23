# docx-mcp-server 工具使用指南

**版本**: v2.1+
**最后更新**: 2026-01-23
**适用对象**: Claude Agent、开发者、文档自动化用户

---

## 目录

1. [快速入门](#1-快速入门)
2. [核心概念](#2-核心概念)
3. [工具选择指南](#3-工具选择指南)
4. [常见场景实战](#4-常见场景实战)
5. [高级技巧](#5-高级技巧)
6. [最佳实践](#6-最佳实践)
7. [故障排查](#7-故障排查)
8. [完整工具参考](#8-完整工具参考)

---

## 1. 快速入门

### 1.1 基本工作流

所有文档操作都遵循以下生命周期：

```
创建会话 → 操作文档 → 保存文档 → 关闭会话
   ↓          ↓          ↓          ↓
create     add/edit    save      close
```

### 1.2 第一个示例：创建简单文档

```python
# 1. 创建新会话
session_id = docx_create()

# 2. 添加内容
para_id = docx_insert_paragraph(
    session_id,
    "Hello World",
    position="end:document_body"
)

# 3. 保存文档
docx_save(session_id, "./output.docx")

# 4. 关闭会话
docx_close(session_id)
```

### 1.3 响应格式（v2.1 新特性）

所有工具返回标准化的 JSON 响应：

```json
{
  "status": "success",
  "message": "Paragraph created successfully",
  "data": {
    "element_id": "para_abc123",
    "cursor": {
      "element_id": "para_abc123",
      "position": "after",
      "context": "Cursor: after paragraph 'Hello World'"
    }
  }
}
```

**解析响应**：

```python
import json

result = docx_insert_paragraph(session_id, "Text", position="end:document_body")
data = json.loads(result)

if data["status"] == "success":
    element_id = data["data"]["element_id"]
    print(f"Created: {element_id}")
else:
    error_msg = data["message"]
    error_type = data["data"]["error_type"]
    print(f"Error ({error_type}): {error_msg}")
```

---

## 2. 核心概念

### 2.1 会话管理（Session）

每个文档操作都在独立的会话中进行：

- **会话 ID**: 唯一标识符（UUID 格式）
- **生命周期**: 创建 → 使用 → 关闭
- **自动过期**: 1 小时无操作后自动清理
- **并发支持**: 多个会话互不干扰

**示例**：

```python
# 创建新文档会话
session_id = docx_create()

# 加载现有文档
session_id = docx_create(file_path="./template.docx")

# 启用自动保存
session_id = docx_create(file_path="./doc.docx", auto_save=True)
```

### 2.2 元素 ID 系统

每个文档元素都有唯一的 ID：

| ID 前缀 | 元素类型 | 示例 |
|---------|---------|------|
| `para_*` | 段落 | `para_a1b2c3d4` |
| `run_*` | 文本块 | `run_e5f6g7h8` |
| `table_*` | 表格 | `table_i9j0k1l2` |
| `cell_*` | 单元格 | `cell_m3n4o5p6` |

**获取元素 ID**：

```python
# 创建时返回
result = docx_insert_paragraph(session_id, "Text", position="end:document_body")
data = json.loads(result)
para_id = data["data"]["element_id"]  # "para_abc123"

# 查找时返回
result = docx_find_paragraphs(session_id, "关键词")
matches = json.loads(result)
para_id = matches[0]["id"]
```

### 2.3 Position 定位系统

`position` 参数控制元素插入位置：

**格式**: `mode:target_id`

| Mode | 说明 | 示例 |
|------|------|------|
| `end:document_body` | 文档末尾 | `end:document_body` |
| `start:document_body` | 文档开头 | `start:document_body` |
| `after:para_123` | 在元素之后 | `after:para_abc123` |
| `before:para_123` | 在元素之前 | `before:para_abc123` |
| `inside:para_123` | 在容器内部 | `inside:para_abc123` |

**示例**：

```python
# 在文档末尾添加
docx_insert_paragraph(session_id, "End", position="end:document_body")

# 在特定段落之后插入
docx_insert_paragraph(session_id, "After", position=f"after:{para_id}")

# 在段落内部添加 Run
docx_insert_run(session_id, "Text", position=f"inside:{para_id}")
```

### 2.4 原子工具 vs 复合工具

**原子工具**（Atomic Tools）:
- 每个工具只做一件事
- 灵活性高，可任意组合
- 适合复杂场景

**复合工具**（Composite Tools）:
- 组合多个原子工具
- 简化常见操作
- 减少工具调用次数

**对比示例**：

```python
# 原子工具方式（4 步）
para_id = docx_insert_paragraph(session_id, "", position="end:document_body")
run_id = docx_insert_run(session_id, "Bold Text", position=f"inside:{para_id}")
docx_set_font(session_id, run_id, bold=True, size=14)
docx_set_alignment(session_id, para_id, "center")

# 复合工具方式（1 步）
para_id = docx_insert_formatted_paragraph(
    session_id, "Bold Text",
    position="end:document_body",
    bold=True, size=14, alignment="center"
)
```

**建议**: 优先使用复合工具，需要精细控制时使用原子工具。

---

## 3. 工具选择指南

### 3.1 文本操作场景

#### 场景 1: 简单占位符替换

**需求**: 替换文档中的 `{{NAME}}` 为 "John Doe"

**推荐工具**: `docx_replace_text`

```python
session_id = docx_create(file_path="./template.docx")
result = docx_replace_text(session_id, "{{NAME}}", "John Doe")
data = json.loads(result)
print(f"替换了 {data['data']['replacements']} 处")
docx_save(session_id, "./output.docx")
docx_close(session_id)
```

**特点**:
- ✅ 跨 Run 智能替换（即使 `{{NAME}}` 被分割成多个 Run）
- ✅ 保留原始格式
- ✅ 支持全局或局部替换（通过 `scope_id`）

---

#### 场景 2: 批量模板填充

**需求**: 同时替换多个占位符

**推荐工具**: `docx_batch_replace_text`

```python
replacements = {
    "{{NAME}}": "John Doe",
    "{{DATE}}": "2026-01-23",
    "{{COMPANY}}": "Acme Corp"
}

result = docx_batch_replace_text(
    session_id,
    json.dumps(replacements)
)
data = json.loads(result)
print(f"替换了 {data['data']['replacements']} 处")
```

**特点**:
- ✅ 一次调用替换多个模式
- ✅ 性能优于多次调用 `docx_replace_text`
- ⚠️ 仅替换单个 Run 内的文本（不跨 Run）

---

#### 场景 3: 查找并编辑

**需求**: 找到包含"重要"的段落，改为红色粗体

**推荐工具**: `docx_quick_edit`（复合工具）

```python
result = docx_quick_edit(
    session_id,
    "重要",
    bold=True,
    color_hex="FF0000"
)
data = json.loads(result)
print(f"修改了 {data['modified_count']} 个段落")
```

**特点**:
- ✅ 查找 + 格式化一步完成
- ✅ 可选择是否替换文本
- ✅ 返回修改统计

---

#### 场景 4: 精确段落更新

**需求**: 已知段落 ID，替换整个段落文本

**推荐工具**: `docx_update_paragraph_text`

```python
# 先查找段落
result = docx_find_paragraphs(session_id, "旧文本")
matches = json.loads(result)
para_id = matches[0]["id"]

# 更新段落
docx_update_paragraph_text(session_id, para_id, "新文本")
```

**特点**:
- ✅ 精确控制
- ⚠️ 会清除段落内所有 Run，替换为单个 Run
- ⚠️ 丢失原有格式

---

#### 场景 5: 精确 Run 更新

**需求**: 只修改某个 Run 的文本，保留格式

**推荐工具**: `docx_update_run_text`

```python
# 假设已知 run_id
docx_update_run_text(session_id, run_id, "新文本")
```

**特点**:
- ✅ 保留 Run 的所有格式（粗体、颜色等）
- ✅ 最精细的控制

---

### 3.2 表格操作场景

#### 场景 1: 按索引获取表格

**需求**: 获取文档中第一个表格

**推荐工具**: `docx_get_table`

```python
result = docx_get_table(session_id, index=0)
data = json.loads(result)
table_id = data["data"]["element_id"]
```

---

#### 场景 2: 按内容查找表格

**需求**: 找到包含"员工信息"的表格

**推荐工具**: `docx_find_table`

```python
result = docx_find_table(session_id, "员工信息")
data = json.loads(result)
table_id = data["data"]["element_id"]
```

---

#### 场景 3: 列出所有表格

**需求**: 查看文档中所有表格的概览

**推荐工具**: `docx_list_tables`

```python
result = docx_list_tables(session_id, max_results=10)
data = json.loads(result)

for table in data["data"]["tables"]:
    print(f"表格 {table['index']}: {table['rows']}x{table['cols']}")
    print(f"  首行: {table['first_row_text']}")
```

---

#### 场景 4: 智能填充表格

**需求**: 从数据库查询结果填充表格，自动扩展行

**推荐工具**: `docx_smart_fill_table`（复合工具）

```python
# 准备数据
data = [
    ["姓名", "年龄", "部门"],
    ["张三", "30", "技术部"],
    ["李四", "25", "市场部"],
    ["王五", "28", "人事部"]
]

# 智能填充（自动扩展行）
result = docx_smart_fill_table(
    session_id,
    table_identifier="0",  # 或 "员工信息" 或 table_id
    data=json.dumps(data),
    has_header=True,
    auto_resize=True
)
```

**特点**:
- ✅ 自动查找表格（支持索引/文本/ID）
- ✅ 自动扩展行数
- ✅ 一步完成

---

#### 场景 5: 手动填充表格

**需求**: 精确控制填充过程

**推荐工具**: `docx_fill_table`（原子工具）

```python
# 先获取表格
result = docx_get_table(session_id, 0)
data = json.loads(result)
table_id = data["data"]["element_id"]

# 准备数据（不含表头）
data = [
    ["张三", "30", "技术部"],
    ["李四", "25", "市场部"]
]

# 从第 1 行开始填充（跳过表头）
docx_fill_table(session_id, json.dumps(data), table_id, start_row=1)
```

---

### 3.3 结构提取场景

#### 场景 1: 快速预览文档结构

**需求**: 查看文档有哪些标题和表格，不需要详细内容

**推荐工具**: `docx_get_structure_summary`（复合工具）

```python
result = docx_get_structure_summary(
    session_id,
    max_headings=10,
    max_tables=5,
    max_paragraphs=0,  # 不返回段落
    include_content=False  # 不返回文本内容
)

structure = json.loads(result)
print(f"标题数: {structure['summary']['total_headings']}")
print(f"表格数: {structure['summary']['total_tables']}")
```

**特点**:
- ✅ Token 使用减少 90%
- ✅ 适合快速浏览
- ✅ 可配置返回内容

---

#### 场景 2: 完整结构分析

**需求**: 提取文档的完整结构，包括所有细节

**推荐工具**: `docx_extract_template_structure`

```python
result = docx_extract_template_structure(session_id)
structure = json.loads(result)

for element in structure["document_structure"]:
    if element["type"] == "heading":
        print(f"标题 {element['level']}: {element['text']}")
    elif element["type"] == "table":
        print(f"表格: {element['rows']}x{element['cols']}")
        print(f"  表头: {element['headers']}")
```

**特点**:
- ✅ 完整的元数据
- ✅ 自动检测表头
- ⚠️ Token 消耗较高

---

### 3.4 格式化场景

#### 场景 1: 快速创建格式化段落

**需求**: 创建一个居中的红色粗体标题

**推荐工具**: `docx_insert_formatted_paragraph`（复合工具）

```python
para_id = docx_insert_formatted_paragraph(
    session_id,
    "重要通知",
    position="end:document_body",
    bold=True,
    size=16,
    color_hex="FF0000",
    alignment="center"
)
```

---

#### 场景 2: 设置字体属性

**需求**: 修改已有 Run 的字体

**推荐工具**: `docx_set_font`

```python
docx_set_font(
    session_id,
    run_id,
    bold=True,
    italic=True,
    size=14,
    color_hex="0000FF"
)
```

---

#### 场景 3: 格式刷

**需求**: 将一个元素的格式复制到另一个元素

**推荐工具**: `docx_format_copy`

```python
# 复制 Run 格式
docx_format_copy(session_id, source_run_id, target_run_id)

# 复制段落格式
docx_format_copy(session_id, source_para_id, target_para_id)
```

---

#### 场景 4: 批量格式化区间

**需求**: 将"第一章"到"第二章"之间的所有段落设为粗体

**推荐工具**: `docx_format_range`（复合工具）

```python
result = docx_format_range(
    session_id,
    start_text="第一章",
    end_text="第二章",
    bold=True,
    size=14
)
```

---


## 4. 常见场景实战

### 4.1 场景：从模板生成报告

**需求**: 加载模板，替换占位符，填充表格，生成报告

```python
import json

# 1. 加载模板
session_id = docx_create(file_path="./report_template.docx")

# 2. 批量替换占位符
replacements = {
    "{{REPORT_TITLE}}": "2026年第一季度销售报告",
    "{{DATE}}": "2026-01-23",
    "{{AUTHOR}}": "张三"
}
result = docx_batch_replace_text(session_id, json.dumps(replacements))

# 3. 填充销售数据表格
sales_data = [
    ["产品", "销量", "金额"],
    ["产品A", "1000", "50000"],
    ["产品B", "800", "40000"],
    ["产品C", "1200", "60000"]
]
result = docx_smart_fill_table(
    session_id,
    "销售数据",  # 查找包含此文本的表格
    json.dumps(sales_data),
    has_header=True,
    auto_resize=True
)

# 4. 保存报告
docx_save(session_id, "./report_2026_Q1.docx")
docx_close(session_id)
```

---

### 4.2 场景：动态创建文档

**需求**: 从零创建一个包含标题、段落、表格的文档

```python
# 1. 创建新文档
session_id = docx_create()

# 2. 添加标题
title_id = docx_insert_formatted_paragraph(
    session_id,
    "项目技术文档",
    position="end:document_body",
    bold=True,
    size=18,
    alignment="center"
)

# 3. 添加一级标题
h1_id = docx_insert_heading(
    session_id,
    "1. 项目概述",
    position="end:document_body",
    level=1
)

# 4. 添加正文段落
para_id = docx_insert_paragraph(
    session_id,
    "本项目旨在开发一个高性能的文档处理系统...",
    position="end:document_body"
)

# 5. 添加表格
result = docx_insert_table(
    session_id,
    rows=3,
    cols=3,
    position="end:document_body"
)
data = json.loads(result)
table_id = data["data"]["element_id"]

# 6. 填充表格
table_data = [
    ["模块", "负责人", "进度"],
    ["前端", "李四", "80%"],
    ["后端", "王五", "90%"]
]
docx_fill_table(session_id, json.dumps(table_data), table_id)

# 7. 保存
docx_save(session_id, "./tech_doc.docx")
docx_close(session_id)
```

---

### 4.3 场景：文档内容分析

**需求**: 提取文档结构，统计信息

```python
# 1. 加载文档
session_id = docx_create(file_path="./document.docx")

# 2. 获取轻量级结构
result = docx_get_structure_summary(
    session_id,
    max_headings=100,
    max_tables=50,
    include_content=True
)
structure = json.loads(result)

# 3. 统计信息
print(f"标题数量: {structure['summary']['total_headings']}")
print(f"表格数量: {structure['summary']['total_tables']}")

# 4. 列出所有标题
print("\n文档大纲:")
for heading in structure["headings"]:
    indent = "  " * (heading["level"] - 1)
    print(f"{indent}{heading['text']}")

# 5. 列出所有表格
print("\n表格列表:")
for i, table in enumerate(structure["tables"]):
    print(f"表格 {i+1}: {table['rows']}行 x {table['cols']}列")
    if "first_row" in table:
        print(f"  表头: {', '.join(table['first_row'])}")

docx_close(session_id)
```

---

### 4.4 场景：批量文档处理

**需求**: 处理目录下所有 .docx 文件

```python
import json

# 1. 列出所有文档
result = docx_list_files("./documents")
files = json.loads(result)

# 2. 批量处理
for filename in files:
    print(f"处理: {filename}")
    
    # 加载文档
    session_id = docx_create(file_path=f"./documents/{filename}")
    
    # 替换水印文本
    docx_replace_text(session_id, "草稿", "正式版")
    
    # 保存到输出目录
    docx_save(session_id, f"./output/{filename}")
    docx_close(session_id)
    
    print(f"完成: {filename}")
```

---


### 4.5 场景：复制和重用内容

**需求**: 复制文档中的某个章节到另一个位置

```python
# 1. 加载文档
session_id = docx_create(file_path="./document.docx")

# 2. 查找章节的开始和结束段落
result = docx_find_paragraphs(session_id, "第一章")
start_matches = json.loads(result)
start_id = start_matches[0]["id"]

result = docx_find_paragraphs(session_id, "第二章")
end_matches = json.loads(result)
end_id = end_matches[0]["id"]

# 3. 复制整个章节到文档末尾
result = docx_copy_elements_range(
    session_id,
    start_id,
    end_id,
    position="end:document_body"
)

# 4. 保存
docx_save(session_id, "./document_with_copy.docx")
docx_close(session_id)
```

---

## 5. 高级技巧

### 5.1 使用光标系统

光标系统允许你跟踪当前操作位置，简化连续插入操作。

```python
session_id = docx_create()

# 1. 插入第一个段落
result = docx_insert_paragraph(
    session_id,
    "第一段",
    position="end:document_body"
)
data = json.loads(result)
para1_id = data["data"]["element_id"]

# 2. 查看光标位置
result = docx_cursor_get(session_id)
cursor = json.loads(result)
print(cursor["data"]["context"])  # "Cursor: after paragraph '第一段'"

# 3. 在当前光标位置插入（使用 after:last_created）
result = docx_insert_paragraph(
    session_id,
    "第二段",
    position=f"after:{para1_id}"
)

# 4. 移动光标到特定位置
docx_cursor_move(session_id, para1_id, position="before")

# 5. 在光标位置插入
result = docx_insert_paragraph(
    session_id,
    "插入到第一段之前",
    position=f"before:{para1_id}"
)
```

---

### 5.2 格式模板系统

提取和复用格式，实现样式一致性。

```python
session_id = docx_create(file_path="./template.docx")

# 1. 查找样式良好的段落
result = docx_find_paragraphs(session_id, "标准格式")
matches = json.loads(result)
source_para_id = matches[0]["id"]

# 2. 提取格式模板
result = docx_extract_format_template(session_id, source_para_id)
format_template = result  # JSON 字符串

# 3. 应用到其他段落
result = docx_find_paragraphs(session_id, "需要格式化")
matches = json.loads(result)

for match in matches:
    target_para_id = match["id"]
    docx_apply_format_template(
        session_id,
        target_para_id,
        format_template
    )

docx_save(session_id, "./formatted.docx")
docx_close(session_id)
```

---

### 5.3 智能文本替换（跨 Run）

`docx_replace_text` 可以处理被分割成多个 Run 的文本。

**问题场景**:
```
文档中的文本: "{{NA" (Run 1) + "ME}}" (Run 2)
普通替换: 无法匹配
```

**解决方案**:
```python
# docx_replace_text 会自动处理跨 Run 的文本
result = docx_replace_text(session_id, "{{NAME}}", "John Doe")
# 成功替换，即使 {{NAME}} 被分割成多个 Run
```

**注意**: `docx_batch_replace_text` 不支持跨 Run 替换，性能更高但功能受限。

---

### 5.4 表格结构分析

获取表格的详细结构信息，包括合并单元格。

```python
session_id = docx_create(file_path="./complex_table.docx")

# 获取表格
result = docx_get_table(session_id, 0)
data = json.loads(result)
table_id = data["data"]["element_id"]

# 获取表格结构（包含 ASCII 可视化）
result = docx_get_table_structure(session_id, table_id)
structure = json.loads(result)

print(structure["data"]["ascii_visualization"])
# 输出类似:
# ┌─────┬─────┬─────┐
# │  A  │  B  │  C  │
# ├─────┼─────┼─────┤
# │  1  │  2  │  3  │
# └─────┴─────┴─────┘

# 检查合并单元格
if structure["data"]["has_merged_cells"]:
    print("表格包含合并单元格")
```

---

### 5.5 错误处理最佳实践

v2.1+ 所有工具返回 JSON 响应，不再抛出异常。

```python
import json

def safe_operation(session_id):
    result = docx_insert_paragraph(
        session_id,
        "Text",
        position="end:document_body"
    )
    
    data = json.loads(result)
    
    if data["status"] == "success":
        element_id = data["data"]["element_id"]
        return element_id
    else:
        error_type = data["data"].get("error_type")
        error_msg = data["message"]
        
        # 根据错误类型处理
        if error_type == "SessionNotFound":
            print("会话已过期，需要重新创建")
        elif error_type == "ElementNotFound":
            print("元素不存在，可能已被删除")
        elif error_type == "ValidationError":
            print(f"参数错误: {error_msg}")
        else:
            print(f"未知错误: {error_msg}")
        
        return None
```

**常见错误类型**:

| 错误类型 | 说明 | 处理建议 |
|---------|------|---------|
| `SessionNotFound` | 会话不存在或已过期 | 重新创建会话 |
| `ElementNotFound` | 元素 ID 不存在 | 检查 ID 是否正确 |
| `InvalidElementType` | 元素类型不匹配 | 确认操作对象类型 |
| `ValidationError` | 参数验证失败 | 检查参数格式 |
| `FileNotFound` | 文件不存在 | 检查文件路径 |
| `CreationError` | 创建元素失败 | 查看详细错误信息 |

---


## 6. 最佳实践

### 6.1 会话管理

**✅ 推荐做法**:

```python
# 使用 try-finally 确保会话关闭
session_id = docx_create(file_path="./doc.docx")
try:
    # 执行操作
    docx_insert_paragraph(session_id, "Text", position="end:document_body")
    docx_save(session_id, "./output.docx")
finally:
    docx_close(session_id)
```

**❌ 避免**:
- 忘记调用 `docx_close()`（会导致资源泄漏）
- 在多个操作间重复创建会话
- 使用已过期的 session_id

---

### 6.2 性能优化

#### 优化 1: 使用复合工具

```python
# ❌ 慢：4 次工具调用
para_id = docx_insert_paragraph(session_id, "", position="end:document_body")
run_id = docx_insert_run(session_id, "Text", position=f"inside:{para_id}")
docx_set_font(session_id, run_id, bold=True)
docx_set_alignment(session_id, para_id, "center")

# ✅ 快：1 次工具调用
para_id = docx_insert_formatted_paragraph(
    session_id, "Text",
    position="end:document_body",
    bold=True, alignment="center"
)
```

#### 优化 2: 批量替换

```python
# ❌ 慢：多次调用
docx_replace_text(session_id, "{{NAME}}", "John")
docx_replace_text(session_id, "{{DATE}}", "2026-01-23")
docx_replace_text(session_id, "{{COMPANY}}", "Acme")

# ✅ 快：一次调用
replacements = {
    "{{NAME}}": "John",
    "{{DATE}}": "2026-01-23",
    "{{COMPANY}}": "Acme"
}
docx_batch_replace_text(session_id, json.dumps(replacements))
```

#### 优化 3: 结构提取

```python
# ❌ 慢：完整结构提取（高 Token 消耗）
result = docx_extract_template_structure(session_id)

# ✅ 快：轻量级摘要（低 Token 消耗）
result = docx_get_structure_summary(
    session_id,
    max_headings=10,
    max_tables=5,
    include_content=False
)
```

---

### 6.3 代码组织

**推荐模式**:

```python
import json

class DocumentProcessor:
    def __init__(self, template_path):
        self.session_id = docx_create(file_path=template_path)
    
    def fill_template(self, data):
        """填充模板数据"""
        # 替换占位符
        replacements = {
            "{{TITLE}}": data["title"],
            "{{DATE}}": data["date"]
        }
        docx_batch_replace_text(self.session_id, json.dumps(replacements))
        
        # 填充表格
        if "table_data" in data:
            docx_smart_fill_table(
                self.session_id,
                "0",
                json.dumps(data["table_data"]),
                has_header=True
            )
    
    def save(self, output_path):
        """保存文档"""
        docx_save(self.session_id, output_path)
    
    def close(self):
        """关闭会话"""
        docx_close(self.session_id)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# 使用上下文管理器
with DocumentProcessor("./template.docx") as processor:
    processor.fill_template({
        "title": "报告",
        "date": "2026-01-23",
        "table_data": [["A", "B"], ["1", "2"]]
    })
    processor.save("./output.docx")
```

---

### 6.4 调试技巧

#### 技巧 1: 查看会话上下文

```python
result = docx_get_context(session_id)
context = json.loads(result)
print(json.dumps(context, indent=2))
```

#### 技巧 2: 使用光标上下文

```python
result = docx_insert_paragraph(session_id, "Text", position="end:document_body")
data = json.loads(result)

# 查看光标位置描述
print(data["data"]["cursor"]["context"])
# 输出: "Cursor: after paragraph 'Text' (para_abc123)"
```

#### 技巧 3: 列出所有会话

```python
result = docx_list_sessions()
sessions = json.loads(result)
for session in sessions["data"]["sessions"]:
    print(f"Session: {session['session_id']}")
    print(f"  File: {session.get('file_path', 'N/A')}")
    print(f"  Objects: {session['object_count']}")
```

---


## 7. 故障排查

### 7.1 常见问题

#### 问题 1: "Session not found"

**原因**: 会话已过期（1小时无操作）或 session_id 错误

**解决方案**:
```python
# 检查会话是否存在
result = docx_list_sessions()
sessions = json.loads(result)
print(f"活跃会话数: {sessions['data']['count']}")

# 重新创建会话
session_id = docx_create(file_path="./doc.docx")
```

---

#### 问题 2: "Element not found"

**原因**: 元素 ID 不存在或已被删除

**解决方案**:
```python
# 重新查找元素
result = docx_find_paragraphs(session_id, "关键词")
matches = json.loads(result)

if matches:
    para_id = matches[0]["id"]
else:
    print("未找到匹配的段落")
```

---

#### 问题 3: 文本替换不生效

**原因**: 文本被分割成多个 Run

**解决方案**:
```python
# 使用 docx_replace_text（支持跨 Run）
result = docx_replace_text(session_id, "{{NAME}}", "John")

# 而不是 docx_batch_replace_text（不支持跨 Run）
```

---

#### 问题 4: 表格填充数据不完整

**原因**: 表格行数不足

**解决方案**:
```python
# 使用 docx_smart_fill_table（自动扩展行）
result = docx_smart_fill_table(
    session_id,
    "0",
    json.dumps(data),
    auto_resize=True  # 关键参数
)
```

---

#### 问题 5: 格式丢失

**原因**: 使用了 `docx_update_paragraph_text`（会清除所有 Run）

**解决方案**:
```python
# ❌ 会丢失格式
docx_update_paragraph_text(session_id, para_id, "新文本")

# ✅ 保留格式
# 方法 1: 使用 docx_replace_text
docx_replace_text(session_id, "旧文本", "新文本", scope_id=para_id)

# 方法 2: 更新单个 Run
docx_update_run_text(session_id, run_id, "新文本")
```

---

### 7.2 调试清单

遇到问题时，按以下顺序检查：

1. **检查响应状态**
   ```python
   data = json.loads(result)
   if data["status"] == "error":
       print(f"错误类型: {data['data']['error_type']}")
       print(f"错误信息: {data['message']}")
   ```

2. **验证会话有效性**
   ```python
   result = docx_get_context(session_id)
   # 如果返回错误，说明会话无效
   ```

3. **检查元素 ID**
   ```python
   # 确保 ID 格式正确
   assert para_id.startswith("para_")
   assert table_id.startswith("table_")
   ```

4. **查看文档结构**
   ```python
   result = docx_get_structure_summary(session_id)
   structure = json.loads(result)
   print(json.dumps(structure, indent=2))
   ```

5. **启用详细日志**
   ```python
   # 设置日志级别为 DEBUG
   docx_set_log_level("DEBUG")
   ```

---


## 8. 完整工具参考

### 8.1 会话管理工具（6个）

#### `docx_create`
创建新文档会话或加载现有文档。

**参数**:
- `file_path` (str, optional): 文档路径，None 表示创建新文档
- `auto_save` (bool, optional): 是否启用自动保存，默认 False

**返回**: session_id (str)

**示例**:
```python
# 创建新文档
session_id = docx_create()

# 加载现有文档
session_id = docx_create(file_path="./template.docx")

# 启用自动保存
session_id = docx_create(file_path="./doc.docx", auto_save=True)
```

---

#### `docx_save`
保存文档到指定路径。

**参数**:
- `session_id` (str): 会话 ID
- `file_path` (str): 保存路径

**返回**: JSON 响应

**示例**:
```python
docx_save(session_id, "./output.docx")
```

---

#### `docx_close`
关闭会话并释放资源。

**参数**:
- `session_id` (str): 会话 ID

**返回**: JSON 响应

**示例**:
```python
docx_close(session_id)
```

---

#### `docx_get_context`
获取会话上下文信息。

**参数**:
- `session_id` (str): 会话 ID

**返回**: JSON 响应，包含会话状态

**示例**:
```python
result = docx_get_context(session_id)
context = json.loads(result)
print(f"最后创建的元素: {context['data']['last_created_id']}")
```

---

#### `docx_list_sessions`
列出所有活跃会话（调试用）。

**参数**: 无

**返回**: JSON 响应，包含会话列表

**示例**:
```python
result = docx_list_sessions()
sessions = json.loads(result)
for session in sessions["data"]["sessions"]:
    print(f"Session: {session['session_id']}")
```

---

#### `docx_cleanup_sessions`
清理过期会话（维护用）。

**参数**:
- `max_idle_seconds` (int, optional): 最大空闲时间，默认使用配置值

**返回**: JSON 响应

---

### 8.2 内容读取工具（4个）

#### `docx_read_content`
读取文档全文，支持分页。

**参数**:
- `session_id` (str): 会话 ID
- `max_paragraphs` (int, optional): 最大段落数
- `start_from` (int, optional): 起始段落索引
- `include_tables` (bool, optional): 是否包含表格，默认 False

**返回**: 文本内容或 JSON

**示例**:
```python
# 读取全部
content = docx_read_content(session_id)

# 分页读取
content = docx_read_content(session_id, max_paragraphs=10, start_from=0)
```

---

#### `docx_find_paragraphs`
查找包含特定文本的段落。

**参数**:
- `session_id` (str): 会话 ID
- `query` (str): 搜索文本
- `max_results` (int, optional): 最大结果数，默认 10

**返回**: JSON 数组，包含匹配的段落

**示例**:
```python
result = docx_find_paragraphs(session_id, "关键词", max_results=5)
matches = json.loads(result)
for match in matches:
    print(f"段落 {match['id']}: {match['text']}")
```

---

#### `docx_list_files`
列出目录下的 .docx 文件。

**参数**:
- `directory` (str, optional): 目录路径，默认当前目录

**返回**: JSON 数组，包含文件名列表

**示例**:
```python
result = docx_list_files("./documents")
files = json.loads(result)
print(f"找到 {len(files)} 个文档")
```

---

#### `docx_extract_template_structure`
提取文档的完整结构。

**参数**:
- `session_id` (str): 会话 ID
- `max_depth` (int, optional): 最大嵌套深度
- `include_content` (bool, optional): 是否包含文本内容，默认 True

**返回**: JSON，包含文档结构

**示例**:
```python
result = docx_extract_template_structure(session_id)
structure = json.loads(result)
for element in structure["document_structure"]:
    print(f"{element['type']}: {element.get('text', '')}")
```

---


### 8.3 复合工具（5个）⭐ 推荐优先使用

#### `docx_insert_formatted_paragraph`
一步创建格式化段落。

**参数**:
- `session_id` (str): 会话 ID
- `text` (str): 段落文本
- `position` (str): 插入位置
- `bold` (bool, optional): 是否粗体
- `italic` (bool, optional): 是否斜体
- `size` (float, optional): 字体大小（磅）
- `color_hex` (str, optional): 颜色（如 "FF0000"）
- `alignment` (str, optional): 对齐方式（left/center/right/justify）
- `style` (str, optional): 段落样式

**返回**: 段落 ID

**示例**:
```python
para_id = docx_insert_formatted_paragraph(
    session_id,
    "重要通知",
    position="end:document_body",
    bold=True,
    size=16,
    color_hex="FF0000",
    alignment="center"
)
```

---

#### `docx_quick_edit`
查找并编辑段落（一步完成）。

**参数**:
- `session_id` (str): 会话 ID
- `search_text` (str): 搜索文本
- `new_text` (str, optional): 新文本
- `bold` (bool, optional): 是否粗体
- `italic` (bool, optional): 是否斜体
- `size` (float, optional): 字体大小
- `color_hex` (str, optional): 颜色

**返回**: JSON，包含修改统计

**示例**:
```python
result = docx_quick_edit(
    session_id,
    "重要",
    bold=True,
    color_hex="FF0000"
)
```

---

#### `docx_get_structure_summary`
轻量级结构提取（低 Token 消耗）。

**参数**:
- `session_id` (str): 会话 ID
- `max_headings` (int, optional): 最大标题数，默认 10
- `max_tables` (int, optional): 最大表格数，默认 5
- `max_paragraphs` (int, optional): 最大段落数，默认 0
- `include_content` (bool, optional): 是否包含内容，默认 False

**返回**: JSON，包含结构摘要

**示例**:
```python
result = docx_get_structure_summary(
    session_id,
    max_headings=10,
    max_tables=5,
    include_content=False
)
```

---

#### `docx_smart_fill_table`
智能填充表格（自动扩展行）。

**参数**:
- `session_id` (str): 会话 ID
- `table_identifier` (str): 表格标识（索引/文本/ID）
- `data` (str): JSON 数组数据
- `has_header` (bool, optional): 首行是否为表头，默认 True
- `auto_resize` (bool, optional): 是否自动扩展行，默认 True

**返回**: JSON，包含填充统计

**示例**:
```python
data = [
    ["姓名", "年龄"],
    ["张三", "30"],
    ["李四", "25"]
]
result = docx_smart_fill_table(
    session_id,
    "0",  # 第一个表格
    json.dumps(data),
    has_header=True,
    auto_resize=True
)
```

---

#### `docx_format_range`
批量格式化段落区间。

**参数**:
- `session_id` (str): 会话 ID
- `start_text` (str): 起始标记文本
- `end_text` (str): 结束标记文本
- `bold` (bool, optional): 是否粗体
- `italic` (bool, optional): 是否斜体
- `size` (float, optional): 字体大小
- `color_hex` (str, optional): 颜色

**返回**: JSON，包含格式化统计

**示例**:
```python
result = docx_format_range(
    session_id,
    "第一章",
    "第二章",
    bold=True,
    size=14
)
```

---


### 8.4 段落操作工具（6个）

#### `docx_insert_paragraph`
添加段落到文档。

**参数**:
- `session_id` (str): 会话 ID
- `text` (str): 段落文本
- `position` (str): 插入位置（必选）
- `style` (str, optional): 段落样式

**返回**: JSON 响应，包含段落 ID

**示例**:
```python
result = docx_insert_paragraph(
    session_id,
    "这是一个段落",
    position="end:document_body"
)
data = json.loads(result)
para_id = data["data"]["element_id"]
```

---

#### `docx_insert_heading`
添加标题到文档。

**参数**:
- `session_id` (str): 会话 ID
- `text` (str): 标题文本
- `position` (str): 插入位置（必选）
- `level` (int, optional): 标题级别（1-9），默认 1

**返回**: JSON 响应，包含标题 ID

**示例**:
```python
result = docx_insert_heading(
    session_id,
    "第一章",
    position="end:document_body",
    level=1
)
```

---

#### `docx_update_paragraph_text`
更新段落文本（会清除所有 Run）。

**参数**:
- `session_id` (str): 会话 ID
- `paragraph_id` (str): 段落 ID
- `new_text` (str): 新文本

**返回**: JSON 响应

**示例**:
```python
docx_update_paragraph_text(session_id, para_id, "新的段落文本")
```

---

#### `docx_copy_paragraph`
深拷贝段落（保留格式）。

**参数**:
- `session_id` (str): 会话 ID
- `paragraph_id` (str): 源段落 ID
- `position` (str): 插入位置

**返回**: JSON 响应，包含新段落 ID

**示例**:
```python
result = docx_copy_paragraph(
    session_id,
    para_id,
    position="end:document_body"
)
```

---

#### `docx_delete`
删除元素。

**参数**:
- `session_id` (str): 会话 ID
- `element_id` (str, optional): 元素 ID

**返回**: JSON 响应

**示例**:
```python
docx_delete(session_id, element_id=para_id)
```

---

#### `docx_insert_page_break`
插入分页符。

**参数**:
- `session_id` (str): 会话 ID
- `position` (str): 插入位置（必选）

**返回**: JSON 响应

**示例**:
```python
docx_insert_page_break(session_id, position="end:document_body")
```

---

### 8.5 Run 操作工具（3个）

#### `docx_insert_run`
向段落添加文本块。

**参数**:
- `session_id` (str): 会话 ID
- `text` (str): 文本内容
- `position` (str): 插入位置（必选）

**返回**: JSON 响应，包含 Run ID

**示例**:
```python
result = docx_insert_run(
    session_id,
    "文本块",
    position=f"inside:{para_id}"
)
data = json.loads(result)
run_id = data["data"]["element_id"]
```

---

#### `docx_update_run_text`
更新 Run 文本（保留格式）。

**参数**:
- `session_id` (str): 会话 ID
- `run_id` (str): Run ID
- `new_text` (str): 新文本

**返回**: JSON 响应

**示例**:
```python
docx_update_run_text(session_id, run_id, "新文本")
```

---

#### `docx_set_font`
设置字体属性。

**参数**:
- `session_id` (str): 会话 ID
- `run_id` (str): Run ID
- `size` (float, optional): 字体大小（磅）
- `bold` (bool, optional): 是否粗体
- `italic` (bool, optional): 是否斜体
- `color_hex` (str, optional): 颜色（如 "FF0000"）

**返回**: JSON 响应

**示例**:
```python
docx_set_font(
    session_id,
    run_id,
    bold=True,
    size=14,
    color_hex="0000FF"
)
```

---


### 8.6 表格操作工具（11个）

#### `docx_insert_table`
创建新表格。

**参数**:
- `session_id` (str): 会话 ID
- `rows` (int): 行数
- `cols` (int): 列数
- `position` (str): 插入位置（必选）

**返回**: JSON 响应，包含表格 ID

**示例**:
```python
result = docx_insert_table(
    session_id,
    rows=3,
    cols=3,
    position="end:document_body"
)
data = json.loads(result)
table_id = data["data"]["element_id"]
```

---

#### `docx_get_table`
按索引获取表格。

**参数**:
- `session_id` (str): 会话 ID
- `index` (int): 表格索引（从 0 开始）

**返回**: JSON 响应，包含表格 ID

**示例**:
```python
result = docx_get_table(session_id, index=0)
data = json.loads(result)
table_id = data["data"]["element_id"]
```

---

#### `docx_find_table`
按内容查找表格。

**参数**:
- `session_id` (str): 会话 ID
- `text` (str): 搜索文本

**返回**: JSON 响应，包含表格 ID

**示例**:
```python
result = docx_find_table(session_id, "员工信息")
data = json.loads(result)
table_id = data["data"]["element_id"]
```

---

#### `docx_list_tables`
列出所有表格。

**参数**:
- `session_id` (str): 会话 ID
- `max_results` (int, optional): 最大结果数，默认 50

**返回**: JSON 响应，包含表格列表

**示例**:
```python
result = docx_list_tables(session_id, max_results=10)
data = json.loads(result)
for table in data["data"]["tables"]:
    print(f"表格 {table['index']}: {table['rows']}x{table['cols']}")
```

---

#### `docx_get_cell`
获取单元格。

**参数**:
- `session_id` (str): 会话 ID
- `table_id` (str): 表格 ID
- `row` (int): 行索引（从 0 开始）
- `col` (int): 列索引（从 0 开始）

**返回**: JSON 响应，包含单元格 ID

**示例**:
```python
result = docx_get_cell(session_id, table_id, row=0, col=0)
data = json.loads(result)
cell_id = data["data"]["element_id"]
```

---

#### `docx_insert_paragraph_to_cell`
向单元格添加段落。

**参数**:
- `session_id` (str): 会话 ID
- `text` (str): 段落文本
- `position` (str): 插入位置（必选，如 `inside:cell_id`）

**返回**: JSON 响应

**示例**:
```python
docx_insert_paragraph_to_cell(
    session_id,
    "单元格内容",
    position=f"inside:{cell_id}"
)
```

---

#### `docx_insert_table_row`
添加行到表格。

**参数**:
- `session_id` (str): 会话 ID
- `position` (str): 插入位置（必选，如 `inside:table_id`）

**返回**: JSON 响应

**示例**:
```python
docx_insert_table_row(session_id, position=f"inside:{table_id}")
```

---

#### `docx_insert_table_col`
添加列到表格。

**参数**:
- `session_id` (str): 会话 ID
- `position` (str): 插入位置（必选，如 `inside:table_id`）

**返回**: JSON 响应

**示例**:
```python
docx_insert_table_col(session_id, position=f"inside:{table_id}")
```

---

#### `docx_fill_table`
批量填充表格数据。

**参数**:
- `session_id` (str): 会话 ID
- `data` (str): JSON 数组数据
- `table_id` (str, optional): 表格 ID
- `start_row` (int, optional): 起始行，默认 0

**返回**: JSON 响应

**示例**:
```python
data = [
    ["张三", "30", "技术部"],
    ["李四", "25", "市场部"]
]
docx_fill_table(
    session_id,
    json.dumps(data),
    table_id,
    start_row=1  # 跳过表头
)
```

---

#### `docx_copy_table`
深拷贝表格（保留结构和格式）。

**参数**:
- `session_id` (str): 会话 ID
- `table_id` (str): 源表格 ID
- `position` (str): 插入位置

**返回**: JSON 响应，包含新表格 ID

**示例**:
```python
result = docx_copy_table(
    session_id,
    table_id,
    position="end:document_body"
)
```

---

#### `docx_get_table_structure`
获取表格结构（包含 ASCII 可视化）。

**参数**:
- `session_id` (str): 会话 ID
- `table_id` (str): 表格 ID

**返回**: JSON 响应，包含结构信息

**示例**:
```python
result = docx_get_table_structure(session_id, table_id)
structure = json.loads(result)
print(structure["data"]["ascii_visualization"])
```

---


### 8.7 格式化工具（6个）

#### `docx_set_alignment`
设置段落对齐方式。

**参数**:
- `session_id` (str): 会话 ID
- `paragraph_id` (str): 段落 ID
- `alignment` (str): 对齐方式（left/center/right/justify）

**返回**: JSON 响应

**示例**:
```python
docx_set_alignment(session_id, para_id, "center")
```

---

#### `docx_set_properties`
通用属性设置（JSON 格式）。

**参数**:
- `session_id` (str): 会话 ID
- `properties` (str): JSON 属性配置
- `element_id` (str, optional): 元素 ID

**返回**: JSON 响应

**示例**:
```python
props = json.dumps({
    "font": {"bold": True, "size": 14},
    "paragraph_format": {"alignment": "center"}
})
docx_set_properties(session_id, props, element_id=run_id)
```

---

#### `docx_format_copy`
复制格式（格式刷）。

**参数**:
- `session_id` (str): 会话 ID
- `source_id` (str): 源元素 ID
- `target_id` (str): 目标元素 ID

**返回**: JSON 响应

**示例**:
```python
docx_format_copy(session_id, source_run_id, target_run_id)
```

---

#### `docx_set_margins`
设置页边距。

**参数**:
- `session_id` (str): 会话 ID
- `top` (float, optional): 上边距（英寸）
- `bottom` (float, optional): 下边距（英寸）
- `left` (float, optional): 左边距（英寸）
- `right` (float, optional): 右边距（英寸）

**返回**: JSON 响应

**示例**:
```python
docx_set_margins(session_id, top=1.0, bottom=1.0, left=1.0, right=1.0)
```

---

#### `docx_extract_format_template`
提取格式模板。

**参数**:
- `session_id` (str): 会话 ID
- `element_id` (str): 元素 ID

**返回**: JSON 格式模板

**示例**:
```python
template = docx_extract_format_template(session_id, para_id)
```

---

#### `docx_apply_format_template`
应用格式模板。

**参数**:
- `session_id` (str): 会话 ID
- `element_id` (str): 目标元素 ID
- `template_json` (str): 格式模板 JSON

**返回**: JSON 响应

**示例**:
```python
docx_apply_format_template(session_id, target_para_id, template)
```

---

### 8.8 高级编辑工具（3个）

#### `docx_replace_text`
智能文本替换（支持跨 Run）。

**参数**:
- `session_id` (str): 会话 ID
- `old_text` (str): 旧文本
- `new_text` (str): 新文本
- `scope_id` (str, optional): 作用域 ID

**返回**: JSON 响应，包含替换统计

**示例**:
```python
result = docx_replace_text(session_id, "{{NAME}}", "John Doe")
data = json.loads(result)
print(f"替换了 {data['data']['replacements']} 处")
```

---

#### `docx_batch_replace_text`
批量文本替换。

**参数**:
- `session_id` (str): 会话 ID
- `replacements_json` (str): JSON 替换映射
- `scope_id` (str, optional): 作用域 ID

**返回**: JSON 响应，包含替换统计

**示例**:
```python
replacements = {
    "{{NAME}}": "John",
    "{{DATE}}": "2026-01-23"
}
result = docx_batch_replace_text(session_id, json.dumps(replacements))
```

---

#### `docx_insert_image`
插入图片。

**参数**:
- `session_id` (str): 会话 ID
- `image_path` (str): 图片路径
- `position` (str): 插入位置（必选）
- `width` (float, optional): 宽度（英寸）
- `height` (float, optional): 高度（英寸）

**返回**: JSON 响应

**示例**:
```python
result = docx_insert_image(
    session_id,
    "./logo.png",
    position="end:document_body",
    width=2.0
)
```

---


### 8.9 光标定位工具（2个）

#### `docx_cursor_get`
获取当前光标位置。

**参数**:
- `session_id` (str): 会话 ID

**返回**: JSON 响应，包含光标状态

**示例**:
```python
result = docx_cursor_get(session_id)
cursor = json.loads(result)
print(cursor["data"]["context"])
```

---

#### `docx_cursor_move`
移动光标到指定位置。

**参数**:
- `session_id` (str): 会话 ID
- `element_id` (str): 目标元素 ID
- `position` (str, optional): 相对位置（before/after/inside_start/inside_end）

**返回**: JSON 响应

**示例**:
```python
docx_cursor_move(session_id, para_id, position="after")
```

---

### 8.10 复制工具（2个）

#### `docx_get_element_source`
获取元素来源元数据。

**参数**:
- `session_id` (str): 会话 ID
- `element_id` (str): 元素 ID

**返回**: JSON 响应，包含来源信息

**示例**:
```python
result = docx_get_element_source(session_id, para_id)
source = json.loads(result)
if source["data"]:
    print(f"来源: {source['data']['source_id']}")
```

---

#### `docx_copy_elements_range`
复制元素区间（如整个章节）。

**参数**:
- `session_id` (str): 会话 ID
- `start_id` (str): 起始元素 ID
- `end_id` (str): 结束元素 ID
- `position` (str): 插入位置

**返回**: JSON 响应，包含新元素 ID 映射

**示例**:
```python
result = docx_copy_elements_range(
    session_id,
    start_para_id,
    end_para_id,
    position="end:document_body"
)
```

---


### 8.11 系统工具（3个）

#### `docx_server_status`
获取服务器状态和环境信息。

**参数**: 无

**返回**: JSON 响应，包含服务器信息

**示例**:
```python
result = docx_server_status()
status = json.loads(result)
print(f"服务器版本: {status['data']['version']}")
print(f"操作系统: {status['data']['platform']}")
```

---

#### `docx_get_log_level`
获取当前日志级别。

**参数**: 无

**返回**: JSON 响应，包含日志级别

**示例**:
```python
result = docx_get_log_level()
level = json.loads(result)
print(f"当前日志级别: {level['data']['level']}")
```

---

#### `docx_set_log_level`
设置日志级别。

**参数**:
- `level` (str): 日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）

**返回**: JSON 响应

**示例**:
```python
docx_set_log_level("DEBUG")  # 启用详细日志
```

---

### 8.12 历史管理工具（3个）

#### `docx_log`
获取提交历史日志。

**参数**:
- `session_id` (str): 会话 ID
- `limit` (int, optional): 最大提交数，默认 10

**返回**: JSON 响应，包含提交列表

**示例**:
```python
result = docx_log(session_id, limit=5)
log = json.loads(result)
for commit in log["data"]["commits"]:
    print(f"{commit['id']}: {commit['message']}")
```

---

#### `docx_rollback`
回滚到指定提交或上一个提交。

**参数**:
- `session_id` (str): 会话 ID
- `commit_id` (str, optional): 目标提交 ID，None 表示回滚到上一个

**返回**: JSON 响应

**示例**:
```python
# 回滚到上一个提交
docx_rollback(session_id)

# 回滚到指定提交
docx_rollback(session_id, commit_id="abc123")
```

---

#### `docx_checkout`
切换到指定提交状态。

**参数**:
- `session_id` (str): 会话 ID
- `commit_id` (str): 目标提交 ID

**返回**: JSON 响应

**示例**:
```python
docx_checkout(session_id, commit_id="abc123")
```

---


## 9. 快速参考卡

### 9.1 工具选择决策树

```
需要操作文档？
├─ 创建/加载文档 → docx_create
├─ 添加内容？
│  ├─ 简单段落 → docx_insert_paragraph
│  ├─ 格式化段落 → docx_insert_formatted_paragraph ⭐
│  ├─ 标题 → docx_insert_heading
│  ├─ 表格 → docx_insert_table
│  └─ 图片 → docx_insert_image
├─ 修改内容？
│  ├─ 替换占位符 → docx_replace_text
│  ├─ 批量替换 → docx_batch_replace_text
│  ├─ 查找并编辑 → docx_quick_edit ⭐
│  └─ 更新段落 → docx_update_paragraph_text
├─ 查找内容？
│  ├─ 查找段落 → docx_find_paragraphs
│  ├─ 查找表格 → docx_find_table
│  └─ 查看结构 → docx_get_structure_summary ⭐
├─ 填充表格？
│  ├─ 智能填充 → docx_smart_fill_table ⭐
│  └─ 手动填充 → docx_fill_table
├─ 格式化？
│  ├─ 设置字体 → docx_set_font
│  ├─ 格式刷 → docx_format_copy
│  └─ 批量格式化 → docx_format_range ⭐
└─ 保存/关闭 → docx_save + docx_close
```

⭐ = 推荐优先使用的复合工具

---

### 9.2 常用代码片段

#### 片段 1: 基本文档操作
```python
import json

# 创建会话
session_id = docx_create()

# 添加内容
result = docx_insert_paragraph(session_id, "Text", position="end:document_body")
data = json.loads(result)
para_id = data["data"]["element_id"]

# 保存并关闭
docx_save(session_id, "./output.docx")
docx_close(session_id)
```

#### 片段 2: 模板填充
```python
# 加载模板
session_id = docx_create(file_path="./template.docx")

# 批量替换
replacements = {"{{NAME}}": "John", "{{DATE}}": "2026-01-23"}
docx_batch_replace_text(session_id, json.dumps(replacements))

# 填充表格
data = [["A", "B"], ["1", "2"]]
docx_smart_fill_table(session_id, "0", json.dumps(data), auto_resize=True)

# 保存
docx_save(session_id, "./output.docx")
docx_close(session_id)
```

#### 片段 3: 错误处理
```python
result = docx_insert_paragraph(session_id, "Text", position="end:document_body")
data = json.loads(result)

if data["status"] == "success":
    element_id = data["data"]["element_id"]
else:
    print(f"错误: {data['message']}")
    print(f"类型: {data['data']['error_type']}")
```

---

## 10. 附录

### 10.1 版本历史

- **v2.1** (2026-01-23): 标准化 JSON 响应格式，所有工具返回统一结构
- **v2.0** (2026-01-20): 新增 5 个复合工具，优化性能
- **v1.5** (2026-01-15): 新增光标系统和位置定位
- **v1.0** (2026-01-01): 初始版本

### 10.2 相关资源

- **项目主页**: [GitHub - docx-mcp-server](https://github.com/your-repo/docx-mcp-server)
- **开发指南**: `CLAUDE.md`
- **功能重叠分析**: `tool_overlap_analysis.md`
- **API 文档**: `README.md`

### 10.3 贡献指南

欢迎贡献！请参考 `CLAUDE.md` 中的开发指南。

---

**文档结束**

*生成时间: 2026-01-23*
*文档版本: v1.0*
*适用于: docx-mcp-server v2.1+*

