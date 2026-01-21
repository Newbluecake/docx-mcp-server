---
feature: template-structure-extraction
complexity: standard
generated_by: architect-planner
generated_at: 2026-01-21T10:42:00Z
version: 1
---

# 技术设计: Word 模板结构提取

> **功能标识**: template-structure-extraction
> **复杂度**: standard
> **生成时间**: 2026-01-21T10:42:00Z

## 1. 架构设计

### 1.1 模块结构

```
src/docx_mcp_server/
├── core/
│   ├── template_parser.py (新增)
│   │   ├── TemplateParser 类
│   │   ├── extract_heading_structure()
│   │   ├── extract_table_structure()
│   │   ├── extract_paragraph_structure()
│   │   ├── extract_image_structure()
│   │   └── detect_header_row()
│   └── session.py (已有)
└── server.py (修改)
    └── docx_extract_template_structure() (新增工具)
```

### 1.2 数据流

```
Client (Claude)
    ↓ docx_extract_template_structure(session_id)
Server (server.py)
    ↓ 获取 Session
SessionManager
    ↓ 返回 Document
TemplateParser
    ↓ 遍历 document.element.body
    ├── 识别 Heading → extract_heading_structure()
    ├── 识别 Table → extract_table_structure()
    │   └── detect_header_row() (智能表头检测)
    ├── 识别 Paragraph → extract_paragraph_structure()
    └── 识别 Image → extract_image_structure()
    ↓ 构建 JSON 结构
    ↓ 返回 JSON 字符串
Client
```

## 2. 核心算法

### 2.1 智能表头检测算法

**目标**: 自动识别表格第一行是否为表头

**检测规则**:
1. 第一行所有单元格都加粗 → 表头
2. 第一行所有单元格有背景色（非白色）→ 表头
3. 同时满足 1 和 2 → 表头
4. 都不满足 → 抛出 ValueError

**实现伪代码**:
```python
def detect_header_row(table: Table) -> int:
    first_row = table.rows[0]

    # 检查加粗
    all_bold = all(
        any(run.bold for run in cell.paragraphs[0].runs if run.bold)
        for cell in first_row.cells
        if cell.paragraphs
    )

    # 检查背景色
    all_has_bg = all(
        has_background_color(cell)
        for cell in first_row.cells
    )

    if all_bold or all_has_bg:
        return 0
    else:
        raise ValueError("无法检测表头行：第一行既无加粗也无背景色")

def has_background_color(cell) -> bool:
    # 检查单元格是否有非白色背景
    shading = cell._element.tcPr.shading if cell._element.tcPr else None
    if shading and shading.fill:
        return shading.fill.upper() not in ["FFFFFF", "NONE", "AUTO"]
    return False
```

### 2.2 元素遍历策略

**目标**: 按文档顺序提取所有元素

**实现方式**:
```python
def extract_structure(document: Document) -> dict:
    structure = []

    for element in document.element.body:
        if element.tag.endswith('p'):  # Paragraph
            para = Paragraph(element, document)
            if para.style.name.startswith('Heading'):
                structure.append(extract_heading_structure(para))
            else:
                structure.append(extract_paragraph_structure(para))

        elif element.tag.endswith('tbl'):  # Table
            table = Table(element, document)
            structure.append(extract_table_structure(table))

    return {"document_structure": structure}
```

## 3. JSON 输出格式

### 3.1 整体结构

```json
{
  "metadata": {
    "extracted_at": "2026-01-21T10:42:00Z",
    "docx_version": "0.1.3"
  },
  "document_structure": [
    { /* 元素 1 */ },
    { /* 元素 2 */ }
  ]
}
```

### 3.2 元素类型定义

#### Heading (标题)
```json
{
  "type": "heading",
  "level": 1,
  "text": "第一章",
  "style": {
    "font": "Arial",
    "size": 16,
    "bold": true,
    "color": "000000"
  }
}
```

#### Table (表格)
```json
{
  "type": "table",
  "rows": 5,
  "cols": 3,
  "header_row": 0,
  "headers": ["姓名", "年龄", "部门"],
  "style": {
    "border": {
      "top": {"type": "single", "color": "000000", "width": 1},
      "bottom": {"type": "single", "color": "000000", "width": 1},
      "left": {"type": "single", "color": "000000", "width": 1},
      "right": {"type": "single", "color": "000000", "width": 1}
    },
    "cell_style": {
      "font": "宋体",
      "size": 12,
      "alignment": "center"
    }
  }
}
```

#### Paragraph (段落)
```json
{
  "type": "paragraph",
  "text": "段落内容",
  "style": {
    "font": "宋体",
    "size": 12,
    "bold": false,
    "italic": false,
    "underline": false,
    "color": "000000",
    "alignment": "left",
    "left_indent": 0.0,
    "right_indent": 0.0,
    "first_line_indent": 0.0
  }
}
```

#### Image (图片)
```json
{
  "type": "image",
  "width": 3.0,
  "height": 2.0,
  "alignment": "center",
  "alt_text": "示例图片"
}
```

## 4. 技术实现细节

### 4.1 样式提取

**字体信息**:
```python
def extract_font_style(run):
    return {
        "font": run.font.name or "默认",
        "size": run.font.size.pt if run.font.size else 12,
        "bold": run.font.bold or False,
        "italic": run.font.italic or False,
        "underline": run.font.underline or False,
        "color": run.font.color.rgb.hex() if run.font.color and run.font.color.rgb else "000000"
    }
```

**段落对齐**:
```python
ALIGNMENT_MAP = {
    WD_ALIGN_PARAGRAPH.LEFT: "left",
    WD_ALIGN_PARAGRAPH.CENTER: "center",
    WD_ALIGN_PARAGRAPH.RIGHT: "right",
    WD_ALIGN_PARAGRAPH.JUSTIFY: "justify"
}

def extract_alignment(paragraph):
    return ALIGNMENT_MAP.get(paragraph.alignment, "left")
```

**表格边框**:
```python
def extract_border_style(cell):
    borders = {}
    for side in ['top', 'bottom', 'left', 'right']:
        border = getattr(cell._element.tcPr.tcBorders, side, None)
        if border:
            borders[side] = {
                "type": border.val,
                "color": border.color or "000000",
                "width": border.sz or 1
            }
    return borders
```

### 4.2 图片处理

**图片尺寸提取**:
```python
def extract_image_structure(paragraph):
    for run in paragraph.runs:
        if run._element.xpath('.//pic:pic'):
            inline = run._element.xpath('.//a:graphic//a:graphicData')[0]
            pic = inline.xpath('.//pic:pic')[0]

            # 提取尺寸
            cx = pic.xpath('.//a:ext/@cx')[0]
            cy = pic.xpath('.//a:ext/@cy')[0]

            width = int(cx) / 914400  # EMU to inches
            height = int(cy) / 914400

            return {
                "type": "image",
                "width": round(width, 2),
                "height": round(height, 2),
                "alignment": extract_alignment(paragraph),
                "alt_text": pic.xpath('.//pic:cNvPr/@descr')[0] if pic.xpath('.//pic:cNvPr/@descr') else ""
            }
```

## 5. 错误处理

### 5.1 错误类型

| 错误场景 | 错误类型 | 错误消息 |
|---------|---------|---------|
| Session 不存在 | ValueError | "Session {session_id} not found" |
| 表头检测失败 | ValueError | "无法检测表头行：第一行既无加粗也无背景色" |
| 文档为空 | ValueError | "文档为空，无法提取结构" |
| 不支持的元素 | 跳过 | 记录日志，不抛出错误 |

### 5.2 容错策略

- **缺失样式**: 使用默认值（如字体大小默认 12pt）
- **空单元格**: 表头列名为空字符串
- **无图片**: 跳过该段落，不添加到结构中

## 6. 性能优化

### 6.1 优化策略

1. **单次遍历**: 只遍历一次 document.element.body
2. **延迟计算**: 仅在需要时提取样式信息
3. **缓存**: 对重复的样式信息进行缓存（如表格单元格样式）

### 6.2 性能目标

- 提取时间 < 5 秒（文档 < 10MB，元素 < 500）
- 内存占用 < 100MB

## 7. 测试策略

### 7.1 单元测试

- `test_detect_header_row_bold()` - 测试加粗表头检测
- `test_detect_header_row_background()` - 测试背景色表头检测
- `test_detect_header_row_fail()` - 测试表头检测失败
- `test_extract_heading_structure()` - 测试标题提取
- `test_extract_table_structure()` - 测试表格提取
- `test_extract_paragraph_structure()` - 测试段落提取
- `test_extract_image_structure()` - 测试图片提取

### 7.2 E2E 测试

- `test_extract_complete_template()` - 测试完整模板提取
- `test_extract_order_preserved()` - 测试元素顺序保持
- `test_extract_empty_document()` - 测试空文档处理

## 8. 依赖关系

### 8.1 现有依赖

- `python-docx` - 核心文档操作库
- `SessionManager` - 会话管理
- `json` - JSON 序列化

### 8.2 新增依赖

无（使用现有依赖即可）

## 9. 兼容性

### 9.1 支持的格式

- .docx (Office 2007+)

### 9.2 不支持的格式

- .doc (旧版 Word)
- 合并单元格表格
- 嵌套表格
- 文本框、形状

## 10. 未来扩展

### 10.1 可扩展点

1. **自定义样式支持**: 识别用户自定义样式名称
2. **合并单元格**: 支持复杂表格结构
3. **占位符识别**: 识别 `{{name}}` 等占位符
4. **章节克隆**: 基于提取的结构生成新文档

### 10.2 扩展建议

- 在 `TemplateParser` 中添加 `extract_custom_style()` 方法
- 在 JSON 输出中添加 `placeholders` 字段
- 创建 `TemplateGenerator` 类用于文档生成

---

**文档版本**: v1
**最后更新**: 2026-01-21T10:42:00Z
