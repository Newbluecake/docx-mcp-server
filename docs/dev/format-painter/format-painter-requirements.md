---
feature: format-painter
complexity: standard
generated_by: clarify
generated_at: 2026-01-21T10:00:00Z
version: 1
---

# 需求文档: Format Painter Support

> **功能标识**: format-painter
> **复杂度**: standard
> **生成方式**: clarify
> **生成时间**: 2026-01-21

## 1. 概述

### 1.1 一句话描述
在 MCP Server 中添加 `docx_format_copy` 工具，实现类似于 Word "格式刷" 的功能，支持将一个元素（段落、文本、表格）的格式完整应用到另一个元素。

### 1.2 核心价值
- **自动化排版**：允许 Claude 通过简单的 API 调用快速统一文档格式，无需逐个设置属性。
- **一致性**：确保文档不同部分的样式完全一致。
- **效率**：一步操作替代几十次 `set_font` / `set_alignment` 调用。

### 1.3 目标用户
- **主要用户**：Claude Agent（通过 MCP 协议调用）。
- **最终用户**：使用 Claude 进行文档编辑的人类用户。

---

## 2. 需求与用户故事

### 2.1 需求清单

| ID | 需求点 | 优先级 | 用户故事 |
|----|--------|--------|----------|
| R-001 | Run 格式复制 | P0 | As an Agent, I want to copy font/color/size from one text run to another. |
| R-002 | Paragraph 格式复制 | P0 | As an Agent, I want to copy alignment/indentation/spacing from one paragraph to another. |
| R-003 | Table 深度格式复制 | P1 | As an Agent, I want to copy borders and shading from one table to another (cell-level). |
| R-004 | 智能类型匹配 | P1 | As an Agent, I want the tool to intelligently handle mismatching types (e.g. Para -> Run). |

### 2.2 验收标准

#### R-001: Run 格式复制
- **WHEN** 调用 `docx_format_copy(source_run_id, target_run_id)`
- **THEN** 目标 Run 的字体、大小、颜色、加粗、斜体、下划线必须与源 Run 一致。

#### R-002: Paragraph 格式复制
- **WHEN** 调用 `docx_format_copy(source_para_id, target_para_id)`
- **THEN** 目标段落的对齐方式、缩进（左右/首行）、行距、段前段后距必须与源段落一致。
- **THEN** 目标段落的默认 Run 格式（如果有）也应更新。

#### R-003: Table 深度格式复制
- **WHEN** 调用 `docx_format_copy(source_table_id, target_table_id)`
- **THEN** 目标表格的样式（Style）、列宽配置应当复制。
- **THEN** (Best Effort) 尝试复制单元格级别的边框和底纹。

#### R-004: 智能类型匹配
- **WHEN** Source 是 Paragraph，Target 是 Run
- **THEN** 仅应用 Paragraph 中定义的字符样式属性到 Target Run。
- **WHEN** Source 是 Run，Target 是 Paragraph
- **THEN** 仅应用 Run 的字符属性到 Paragraph 的默认 Run 属性（Character format only）。
- **WHEN** 类型完全不兼容（如 Table -> Run）
- **THEN** 抛出明确的 `ValueError`。

---

## 3. 功能验收清单

| ID | 功能点 | 验收步骤 | 优先级 | 关联需求 | 通过 |
|----|--------|----------|--------|----------|------|
| F-001 | API 实现 | `docx_format_copy` 工具可用 | P0 | All | ☐ |
| F-002 | 字符格式刷 | 测试粗体红字 -> 普通文字，验证变为粗体红字 | P0 | R-001 | ☐ |
| F-003 | 段落格式刷 | 测试居中缩进段落 -> 普通段落，验证对齐缩进 | P0 | R-002 | ☐ |
| F-004 | 错误处理 | 测试 Table -> Run，验证报错信息清晰 | P1 | R-004 | ☐ |

---

## 4. 技术约束

### 4.1 技术栈
- `python-docx`: 必须使用现有库，必要时操作 `_element` (lxml) 进行底层 XML 复制。

### 4.2 局限性
- 表格的深度复制（Borders/Shading）在 `python-docx` 中 API 支持有限，可能需要直接操作 OXML (`tblPr`, `tcPr`)。
- 只有显式设置的格式能被复制，继承自 Style 的格式可能难以解析（除非解析 Style 树，暂不作为 P0）。

---

## 5. 排除项

- **样式定义复制**：不复制 Style 对象本身，只复制显式属性。
- **跨文档复制**：暂不支持（虽然 Session 间隔离，但技术上可行，暂定仅支持同一 Session 内）。

---

## 6. 下一步

✅ 在新会话中执行：
```bash
/clouditera:dev:spec-dev format-painter --skip-requirements
```
