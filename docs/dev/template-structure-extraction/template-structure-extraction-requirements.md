---
feature: template-structure-extraction
complexity: standard
generated_by: clarify
generated_at: 2026-01-21T10:35:00Z
version: 1
---

# 需求文档: Word 模板结构提取

> **功能标识**: template-structure-extraction
> **复杂度**: standard
> **生成方式**: clarify
> **生成时间**: 2026-01-21T10:35:00Z

## 1. 概述

### 1.1 一句话描述

为 docx-mcp-server 添加 Word 模板结构提取能力，智能识别文档中的标题、表格、图片、段落等元素的结构和样式信息，输出 JSON 格式的结构化数据，供后续文档生成使用。

### 1.2 核心价值

**解决的问题**：
- 用户需要基于 Word 模板批量生成文档，但现有工具无法自动识别模板的结构和样式
- 手动提取模板信息（表头列名、段落样式、图片尺寸等）效率低且容易出错
- 缺乏统一的模板结构描述格式，导致模板复用困难

**带来的价值**：
- **自动化**：一键提取模板结构，无需手动分析文档
- **标准化**：输出 JSON 格式，易于程序化处理和存储
- **可复用**：提取的结构信息可用于批量生成、模板验证、文档对比等场景

### 1.3 目标用户

- **主要用户**：需要基于 Word 模板批量生成报告、合同、发票等文档的开发者
- **次要用户**：需要分析 Word 文档结构的数据分析师、文档管理员

---

## 2. 需求与用户故事

### 2.1 需求清单

| ID | 需求点 | 优先级 | 用户故事 |
|----|--------|--------|----------|
| R-001 | 标题结构识别 | P0 | As a 开发者, I want 识别文档中的标题层级（Heading 1/2/3）, so that 我可以理解文档的章节结构 |
| R-002 | 表格结构识别 | P0 | As a 开发者, I want 识别表格的表头、列名、行数、列数, so that 我可以按列名填充数据 |
| R-003 | 表格样式提取 | P0 | As a 开发者, I want 提取表格的边框、颜色、字体等样式, so that 生成的文档保持原有样式 |
| R-004 | 图片结构识别 | P1 | As a 开发者, I want 识别图片的尺寸、位置、对齐方式, so that 我可以插入相同格式的图片 |
| R-005 | 段落样式提取 | P1 | As a 开发者, I want 提取段落的字体、对齐、缩进等样式, so that 生成的段落保持一致格式 |
| R-006 | JSON 结构化输出 | P0 | As a 开发者, I want 以 JSON 格式输出所有结构信息, so that 我可以程序化处理这些数据 |
| R-007 | 智能表头检测 | P0 | As a 开发者, I want 自动检测表头行（通过加粗/背景色）, so that 我无需手动指定表头位置 |
| R-008 | 元素顺序保持 | P1 | As a 开发者, I want 输出的 JSON 保持元素在文档中的原始顺序, so that 我可以按顺序重建文档 |

### 2.2 验收标准

#### R-001: 标题结构识别
- **WHEN** 调用 `docx_extract_template_structure(session_id)`, **THEN** 系统 **SHALL** 识别所有使用 Heading 1/2/3 样式的段落
- **WHEN** 文档包含多级标题, **THEN** 系统 **SHALL** 正确识别标题的层级关系（父子关系）
- **WHEN** 标题包含文本内容, **THEN** 系统 **SHALL** 提取标题文本和样式信息（字体、大小、颜色）

#### R-002: 表格结构识别
- **WHEN** 文档包含表格, **THEN** 系统 **SHALL** 识别表格的行数、列数
- **WHEN** 表格有表头行, **THEN** 系统 **SHALL** 智能检测表头（通过加粗或背景色特征）
- **WHEN** 表头检测成功, **THEN** 系统 **SHALL** 提取每列的列名（表头单元格文本）
- **WHEN** 表头检测失败, **THEN** 系统 **SHALL** 抛出错误并停止处理（严格模式）

#### R-003: 表格样式提取
- **WHEN** 提取表格结构, **THEN** 系统 **SHALL** 提取以下样式信息：
  - 边框样式（类型、颜色、宽度）
  - 单元格背景色和前景色
  - 文字格式（字体名称、大小、加粗、斜体、颜色）
  - 对齐方式（水平/垂直）

#### R-004: 图片结构识别
- **WHEN** 文档包含图片, **THEN** 系统 **SHALL** 识别图片的宽度和高度（单位：英寸）
- **WHEN** 图片在段落中, **THEN** 系统 **SHALL** 识别图片的对齐方式（左/中/右）
- **WHEN** 图片有替代文本, **THEN** 系统 **SHALL** 提取替代文本（alt text）

#### R-005: 段落样式提取
- **WHEN** 提取段落结构, **THEN** 系统 **SHALL** 提取以下样式信息：
  - 字体名称、大小、颜色
  - 加粗、斜体、下划线状态
  - 对齐方式（左/中/右/两端对齐）
  - 缩进（左缩进、右缩进、首行缩进）
  - 行间距和段间距

#### R-006: JSON 结构化输出
- **WHEN** 调用提取工具, **THEN** 系统 **SHALL** 返回符合以下格式的 JSON 字符串：
  ```json
  {
    "document_structure": [
      {
        "type": "heading",
        "level": 1,
        "text": "章节标题",
        "style": { "font": "Arial", "size": 16, "bold": true }
      },
      {
        "type": "table",
        "rows": 5,
        "cols": 3,
        "headers": ["姓名", "年龄", "部门"],
        "header_row": 0,
        "style": { "border": {...}, "cell_style": {...} }
      },
      {
        "type": "paragraph",
        "text": "段落内容",
        "style": { "font": "宋体", "size": 12, "alignment": "left" }
      },
      {
        "type": "image",
        "width": 3.0,
        "height": 2.0,
        "alignment": "center",
        "alt_text": "示例图片"
      }
    ]
  }
  ```

#### R-007: 智能表头检测
- **WHEN** 表格第一行所有单元格都加粗, **THEN** 系统 **SHALL** 识别为表头行
- **WHEN** 表格第一行所有单元格有背景色（非白色）, **THEN** 系统 **SHALL** 识别为表头行
- **WHEN** 表格第一行同时满足加粗和背景色, **THEN** 系统 **SHALL** 识别为表头行
- **WHEN** 表格第一行不满足以上任何条件, **THEN** 系统 **SHALL** 抛出错误："无法检测表头行"

#### R-008: 元素顺序保持
- **WHEN** 文档包含多个元素（标题、段落、表格、图片）, **THEN** 系统 **SHALL** 按文档中的出现顺序输出到 JSON 数组
- **WHEN** 元素嵌套（如表格中的段落）, **THEN** 系统 **SHALL** 在父元素的 JSON 对象中嵌套子元素

---

## 3. 功能验收清单

| ID | 功能点 | 验收步骤 | 优先级 | 关联需求 | 通过 |
|----|--------|----------|--------|----------|------|
| F-001 | 提取标题结构 | 1. 创建包含 Heading 1/2/3 的文档<br>2. 调用提取工具<br>3. 验证 JSON 中包含所有标题及层级 | P0 | R-001 | ☐ |
| F-002 | 智能检测表头 | 1. 创建表格，第一行加粗<br>2. 调用提取工具<br>3. 验证 JSON 中 `header_row: 0` 且 `headers` 正确 | P0 | R-002, R-007 | ☐ |
| F-003 | 表头检测失败处理 | 1. 创建表格，第一行无加粗无背景色<br>2. 调用提取工具<br>3. 验证抛出错误："无法检测表头行" | P0 | R-002, R-007 | ☐ |
| F-004 | 提取表格样式 | 1. 创建带边框和背景色的表格<br>2. 调用提取工具<br>3. 验证 JSON 中包含边框和颜色信息 | P0 | R-003 | ☐ |
| F-005 | 提取图片信息 | 1. 插入图片（3x2 英寸，居中）<br>2. 调用提取工具<br>3. 验证 JSON 中 `width: 3.0, height: 2.0, alignment: "center"` | P1 | R-004 | ☐ |
| F-006 | 提取段落样式 | 1. 创建段落（宋体 12pt，左对齐，首行缩进 2 字符）<br>2. 调用提取工具<br>3. 验证 JSON 中包含字体、对齐、缩进信息 | P1 | R-005 | ☐ |
| F-007 | 元素顺序正确 | 1. 创建文档：标题 → 段落 → 表格 → 图片<br>2. 调用提取工具<br>3. 验证 JSON 数组顺序与文档一致 | P1 | R-008 | ☐ |
| F-008 | 完整模板提取 | 1. 加载真实 Word 模板（包含所有元素类型）<br>2. 调用提取工具<br>3. 验证 JSON 完整且可用于重建文档 | P0 | R-001~R-008 | ☐ |

---

## 4. 技术约束

### 4.1 技术栈

- **核心库**：python-docx（已有依赖）
- **架构**：基于现有 docx-mcp-server 的 Session 管理机制
- **输出格式**：JSON（使用 Python 标准库 `json`）

### 4.2 集成点

**新增模块**：
- `src/docx_mcp_server/core/template_parser.py` - 模板解析核心逻辑
  - `TemplateParser` 类：负责遍历文档元素并提取结构
  - `extract_heading_structure()` - 提取标题
  - `extract_table_structure()` - 提取表格（含智能表头检测）
  - `extract_image_structure()` - 提取图片
  - `extract_paragraph_structure()` - 提取段落

**新增工具**：
- `docx_extract_template_structure(session_id: str) -> str` - 主入口工具
  - 参数：会话 ID
  - 返回：JSON 字符串（包含完整文档结构）

**依赖现有模块**：
- `SessionManager` - 获取文档会话
- `Finder` - 查找表格（可选，用于定位特定表格）

### 4.3 性能要求

- 单个文档提取时间 < 5 秒（文档大小 < 10MB，元素数量 < 500）
- 内存占用 < 100MB（处理单个文档时）

### 4.4 兼容性

- 支持 .docx 格式（Office 2007+）
- 不支持 .doc 格式（旧版 Word）

---

## 5. 排除项

- **不支持复杂表格结构**：合并单元格、嵌套表格暂不支持（未来可扩展）
- **不支持占位符替换**：本功能仅提取结构，不做内容替换（如 `{{name}}`）
- **不支持章节克隆**：本功能仅提取结构，不做文档生成（未来可扩展）
- **不支持自定义样式名称**：仅识别内置样式（Heading 1/2/3），不识别用户自定义样式名
- **不支持文本框、形状**：仅支持段落、表格、图片三种基本元素

---

## 6. 实现建议

### 6.1 智能表头检测算法

```python
def detect_header_row(table: Table) -> int:
    """
    智能检测表头行（第一行）

    检测规则：
    1. 第一行所有单元格都加粗 → 表头
    2. 第一行所有单元格有背景色（非白色）→ 表头
    3. 同时满足 1 和 2 → 表头
    4. 都不满足 → 抛出错误

    Returns:
        int: 表头行索引（通常为 0）

    Raises:
        ValueError: 无法检测表头行
    """
    first_row = table.rows[0]

    # 检查加粗
    all_bold = all(
        any(run.bold for run in cell.paragraphs[0].runs)
        for cell in first_row.cells
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
```

### 6.2 JSON 输出格式设计

**设计原则**：
- 扁平化：避免过深的嵌套
- 可扩展：预留 `metadata` 字段用于未来扩展
- 类型明确：使用 `type` 字段区分元素类型

**示例**：
```json
{
  "metadata": {
    "extracted_at": "2026-01-21T10:35:00Z",
    "docx_version": "0.1.3"
  },
  "document_structure": [
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
    },
    {
      "type": "table",
      "rows": 5,
      "cols": 3,
      "header_row": 0,
      "headers": ["姓名", "年龄", "部门"],
      "style": {
        "border": {
          "top": {"type": "single", "color": "000000", "width": 1},
          "bottom": {"type": "single", "color": "000000", "width": 1}
        },
        "cell_style": {
          "font": "宋体",
          "size": 12,
          "alignment": "center"
        }
      }
    }
  ]
}
```

---

## 7. 下一步

✅ 需求已澄清，准备进入技术设计阶段。

**推荐工作流**：

### 选项 1：创建 Worktree 并继续（推荐）
在隔离的工作区中继续开发，避免影响主分支。

**操作步骤**：
1. 创建 worktree：
   ```bash
   bash scripts/worktree-manager.sh create template-structure-extraction
   ```
2. 切换到 worktree 目录
3. 在当前会话执行：
   ```bash
   /clouditera:dev:spec-dev template-structure-extraction --skip-requirements
   ```

### 选项 2：在主工作区继续
直接在当前目录继续开发（不推荐，可能影响其他功能）。

**操作步骤**：
在当前会话执行：
```bash
/clouditera:dev:spec-dev template-structure-extraction --skip-requirements --no-worktree
```

---

**文档版本**: v1
**最后更新**: 2026-01-21T10:35:00Z
