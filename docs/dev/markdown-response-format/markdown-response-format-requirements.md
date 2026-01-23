# 需求文档: Markdown Response Format

> **功能标识**: markdown-response-format
> **复杂度**: complex
> **生成方式**: clarify
> **生成时间**: 2026-01-23T10:30:00Z

---

## 1. 概述

### 1.1 一句话描述

将 docx-mcp-server 的所有 MCP 工具返回值从 JSON 格式改为 Markdown 格式，并提供 ASCII 可视化的文档上下文展示，支持 Git diff 风格的编辑前后对比。

### 1.2 核心价值

**解决的问题**：
- 当前 JSON 返回值对人类不友好，难以快速理解文档状态
- 缺乏直观的上下文展示，用户难以感知编辑位置和周围内容
- 编辑前后的变化不可见，无法快速验证操作结果

**带来的价值**：
- **可读性提升**：Markdown 格式更适合人类阅读，Claude 和用户都能快速理解
- **上下文感知**：ASCII 可视化展示文档结构、表格、段落，提供"所见即所得"的体验
- **变更可追踪**：Git diff 风格的对比清晰展示编辑前后的差异
- **调试友好**：开发者和用户都能直观看到工具的执行效果

### 1.3 目标用户

- **主要用户**：Claude（AI Agent）—— 需要理解文档状态并做出决策
- **次要用户**：开发者和最终用户 —— 需要调试和验证工具行为

---

## 2. 需求与用户故事

### 2.1 需求清单

| ID | 需求点 | 优先级 | 用户故事 |
|----|--------|--------|----------|
| R-001 | Markdown 返回格式 | P0 | As a Claude, I want 工具返回 Markdown 文本, so that 我能快速理解文档状态而无需解析 JSON |
| R-002 | ASCII 文档可视化 | P0 | As a user, I want 看到文档的 ASCII 可视化, so that 我能直观理解当前编辑位置和周围内容 |
| R-003 | Git diff 风格对比 | P0 | As a user, I want 看到编辑前后的 diff, so that 我能验证操作是否符合预期 |
| R-004 | 段落内容展示 | P0 | As a user, I want 看到段落的文本内容和格式（粗体、斜体、颜色）, so that 我能理解文档的实际内容 |
| R-005 | 表格 ASCII 展示 | P0 | As a user, I want 看到表格的 ASCII 表格形式, so that 我能理解表格结构和内容 |
| R-006 | 图片/光标/结构展示 | P1 | As a user, I want 看到图片位置、光标位置、文档结构树, so that 我能全面理解文档状态 |
| R-007 | 一页上下文范围 | P0 | As a user, I want 看到约一页内容的上下文（10-15 个元素）, so that 我能理解当前位置的前后关系 |
| R-008 | 破坏性变更 | P0 | As a developer, I want 完全替换 JSON 格式为 Markdown, so that 系统保持简洁统一 |

### 2.2 验收标准

#### R-001: Markdown 返回格式
- **WHEN** 调用任何 MCP 工具（如 `docx_insert_paragraph`）, **THEN** 系统 **SHALL** 返回 Markdown 格式的字符串
- **WHEN** 返回 Markdown 文本, **THEN** 系统 **SHALL NOT** 包含 JSON 结构（如 `{"status": "success"}`）
- **WHEN** 需要传递结构化信息（如 element_id）, **THEN** 系统 **SHALL** 使用 Markdown 内联标记（如 `**Element ID**: para_123`）

#### R-002: ASCII 文档可视化
- **WHEN** 工具返回结果, **THEN** 系统 **SHALL** 包含 ASCII 可视化的文档上下文
- **WHEN** 展示文档上下文, **THEN** 系统 **SHALL** 使用 ASCII 字符绘制边框、分隔线、表格
- **WHEN** 展示段落, **THEN** 系统 **SHALL** 显示段落文本内容（截断过长内容）
- **WHEN** 展示表格, **THEN** 系统 **SHALL** 使用 ASCII 表格格式（`|` 和 `-` 字符）

#### R-003: Git diff 风格对比
- **WHEN** 工具修改了文档内容（如 `docx_update_paragraph_text`）, **THEN** 系统 **SHALL** 展示编辑前后的 diff
- **WHEN** 展示 diff, **THEN** 系统 **SHALL** 使用 `-` 标记删除的内容，`+` 标记新增的内容
- **WHEN** 内容未变化, **THEN** 系统 **SHALL** 使用空格前缀标记不变的行
- **WHEN** 展示 diff, **THEN** 系统 **SHALL** 包含前后各 2-3 行的上下文

#### R-004: 段落内容展示
- **WHEN** 展示段落, **THEN** 系统 **SHALL** 显示段落的文本内容
- **WHEN** 段落包含格式（粗体、斜体）, **THEN** 系统 **SHALL** 使用 Markdown 语法标记（`**bold**`, `*italic*`）
- **WHEN** 段落包含颜色, **THEN** 系统 **SHALL** 使用文本标记（如 `[红色]`）或忽略颜色信息
- **WHEN** 段落过长（>80 字符）, **THEN** 系统 **SHALL** 截断并添加 `...` 标记

#### R-005: 表格 ASCII 展示
- **WHEN** 展示表格, **THEN** 系统 **SHALL** 使用 ASCII 表格格式
- **WHEN** 绘制表格, **THEN** 系统 **SHALL** 使用 `|` 作为列分隔符，`-` 作为行分隔符
- **WHEN** 表格单元格包含内容, **THEN** 系统 **SHALL** 显示单元格文本（截断过长内容）
- **WHEN** 表格过大（>10 列或 >20 行）, **THEN** 系统 **SHALL** 截断并标记省略部分

#### R-006: 图片/光标/结构展示
- **WHEN** 文档包含图片, **THEN** 系统 **SHALL** 使用 `[IMG: filename.png]` 标记图片位置
- **WHEN** 展示光标位置, **THEN** 系统 **SHALL** 使用 `>>> [CURSOR] <<<` 或类似标记
- **WHEN** 展示文档结构, **THEN** 系统 **SHALL** 使用树形结构（如 `├── Heading 1`）

#### R-007: 一页上下文范围
- **WHEN** 展示上下文, **THEN** 系统 **SHALL** 包含当前元素前后各 5-7 个元素（总计约 10-15 个）
- **WHEN** 上下文超出范围, **THEN** 系统 **SHALL** 在边界处标记 `... (更多内容) ...`
- **WHEN** 当前元素在文档开头或结尾, **THEN** 系统 **SHALL** 调整上下文范围以保持总数

#### R-008: 破坏性变更
- **WHEN** 实施此功能, **THEN** 系统 **SHALL** 移除所有 JSON 返回格式的代码
- **WHEN** 实施此功能, **THEN** 系统 **SHALL** 更新所有单元测试以验证 Markdown 输出
- **WHEN** 实施此功能, **THEN** 系统 **SHALL** 更新 README.md 和 CLAUDE.md 文档

---

## 3. 功能验收清单

| ID | 功能点 | 验收步骤 | 优先级 | 关联需求 | 通过 |
|----|--------|----------|--------|----------|------|
| F-001 | 段落插入返回 Markdown | 1. 调用 `docx_insert_paragraph` <br> 2. 验证返回值是 Markdown 文本 <br> 3. 验证包含 ASCII 可视化 | P0 | R-001, R-002 | ☐ |
| F-002 | 段落更新展示 diff | 1. 调用 `docx_update_paragraph_text` <br> 2. 验证返回值包含 Git diff 风格对比 <br> 3. 验证 `-` 和 `+` 标记正确 | P0 | R-003 | ☐ |
| F-003 | 表格插入展示 ASCII 表格 | 1. 调用 `docx_insert_table` <br> 2. 验证返回值包含 ASCII 表格 <br> 3. 验证表格边框和内容正确 | P0 | R-005 | ☐ |
| F-004 | 段落格式展示 | 1. 创建包含粗体、斜体的段落 <br> 2. 验证返回值使用 Markdown 语法标记格式 | P0 | R-004 | ☐ |
| F-005 | 上下文范围控制 | 1. 在长文档中插入段落 <br> 2. 验证上下文包含约 10-15 个元素 <br> 3. 验证边界处有省略标记 | P0 | R-007 | ☐ |
| F-006 | 光标位置展示 | 1. 调用 `docx_cursor_move` <br> 2. 验证返回值标记光标位置 | P1 | R-006 | ☐ |
| F-007 | 图片位置展示 | 1. 调用 `docx_insert_image` <br> 2. 验证返回值标记图片位置 | P1 | R-006 | ☐ |
| F-008 | 所有工具迁移完成 | 1. 检查所有 51 个 MCP 工具 <br> 2. 验证全部返回 Markdown 格式 <br> 3. 验证无 JSON 格式残留 | P0 | R-008 | ☐ |
| F-009 | 单元测试更新 | 1. 运行 `pytest tests/unit/` <br> 2. 验证所有测试通过 <br> 3. 验证测试验证 Markdown 输出 | P0 | R-008 | ☐ |
| F-010 | E2E 测试更新 | 1. 运行 `pytest tests/e2e/` <br> 2. 验证所有测试通过 | P0 | R-008 | ☐ |

---

## 4. 技术约束

### 4.1 技术栈

**必须保持**：
- Python 3.8+
- python-docx 库
- MCP 协议（工具返回值类型为 `str`）

**新增依赖**（可选）：
- 无需新增外部依赖，使用 Python 标准库实现 ASCII 绘制

### 4.2 架构约束

**响应格式化层**：
- 修改 `src/docx_mcp_server/core/response.py` 中的响应格式化函数
- 移除 `create_success_response`、`create_error_response` 等 JSON 格式化函数
- 新增 `create_markdown_response` 函数

**工具层**：
- 修改所有 51 个 MCP 工具的返回语句
- 从 `return create_success_response(...)` 改为 `return create_markdown_response(...)`

**可视化层**：
- 新增 `src/docx_mcp_server/core/visualizer.py` 模块
- 实现 ASCII 绘制逻辑：
  - `render_paragraph(paragraph) -> str`
  - `render_table(table) -> str`
  - `render_context(session, element_id, range=7) -> str`
  - `render_diff(old_content, new_content) -> str`

### 4.3 性能约束

**Token 消耗**：
- 每次工具调用的返回值可能增加 500-2000 tokens（取决于上下文大小）
- 用户明确表示不关心性能，优先保证完整展示

**渲染性能**：
- ASCII 绘制应在 100ms 内完成（对于单个工具调用）
- 避免在大文档（>1000 段落）中渲染全文档

### 4.4 兼容性约束

**破坏性变更**：
- 完全移除 JSON 格式，不保留向后兼容
- 所有依赖 JSON 解析的代码（如测试用例）需要更新

**MCP 协议兼容**：
- MCP 工具返回值类型仍为 `str`，符合协议规范
- Claude 可以直接读取 Markdown 文本，无需额外解析

---

## 5. 设计约束

### 5.1 Markdown 格式规范

**基本结构**：
```markdown
# 操作结果: [操作名称]

**Status**: ✅ Success / ❌ Error
**Element ID**: para_abc123
**Operation**: Insert Paragraph

---

## 📄 Document Context

[ASCII 可视化的文档上下文]

---

## 🔄 Changes (如适用)

[Git diff 风格的变更对比]
```

**元数据嵌入**：
- 使用 Markdown 粗体标记关键信息（`**Element ID**: para_123`）
- 不使用 Frontmatter 或 HTML 注释

### 5.2 ASCII 可视化规范

**段落展示**：
```
┌─────────────────────────────────────────┐
│ Paragraph (para_123)                    │
├─────────────────────────────────────────┤
│ This is a **bold** and *italic* text.  │
│ It can span multiple lines...          │
└─────────────────────────────────────────┘
```

**表格展示**：
```
┌─────────┬─────────┬─────────┐
│ Name    │ Age     │ City    │
├─────────┼─────────┼─────────┤
│ Alice   │ 30      │ NYC     │
│ Bob     │ 25      │ LA      │
└─────────┴─────────┴─────────┘
```

**上下文展示**（一页内容）：
```
📄 Document Context (showing 10 elements around para_123)

  ... (5 more elements above) ...

  ┌─────────────────────────────────────────┐
  │ Paragraph (para_120)                    │
  │ Previous paragraph content...           │
  └─────────────────────────────────────────┘

  ┌─────────────────────────────────────────┐
  │ Paragraph (para_121)                    │
  │ Another paragraph...                    │
  └─────────────────────────────────────────┘

>>> [CURSOR] <<<

  ┌─────────────────────────────────────────┐
  │ Paragraph (para_123) ⭐ CURRENT         │
  │ This is the newly inserted paragraph.   │
  └─────────────────────────────────────────┘

  ┌─────────────────────────────────────────┐
  │ Paragraph (para_124)                    │
  │ Next paragraph...                       │
  └─────────────────────────────────────────┘

  ... (5 more elements below) ...
```

### 5.3 Git Diff 风格规范

**变更对比**：
```
🔄 Changes

  ┌─────────────────────────────────────────┐
  │ Paragraph (para_123)                    │
  ├─────────────────────────────────────────┤
- │ Old text content here.                  │
+ │ New text content here.                  │
  │ Unchanged line.                         │
  └─────────────────────────────────────────┘
```

**上下文行**：
- 变更前后各保留 2-3 行不变的内容
- 使用空格前缀标记不变的行

---

## 6. 排除项

以下功能**不在**本次需求范围内：

- **JSON 格式保留**：不提供 `--format=json` 参数切换回 JSON 格式
  - 原因：用户明确要求完全替换，保持系统简洁

- **颜色高亮**：不使用 ANSI 颜色代码（如 `\033[31m红色\033[0m`）
  - 原因：Markdown 文本需要在多种环境中展示，ANSI 代码可能不兼容

- **交互式可视化**：不提供可折叠/展开的交互式 UI
  - 原因：MCP 工具返回纯文本，不支持交互

- **自定义上下文范围**：不提供 `--context-lines=N` 参数
  - 原因：固定为"一页内容"（10-15 个元素），简化实现

- **图片内容预览**：不展示图片的缩略图或 ASCII art
  - 原因：仅标记图片位置（`[IMG: filename.png]`），不渲染图片内容

- **复杂格式支持**：不支持嵌套列表、脚注、批注等复杂格式的可视化
  - 原因：优先支持段落、表格、图片等核心元素

---

## 7. 实施计划

### 7.1 阶段划分

**阶段 1: 核心架构重构**（P0）
- 新增 `visualizer.py` 模块
- 修改 `response.py` 响应格式化层
- 实现基础 Markdown 返回格式

**阶段 2: ASCII 可视化实现**（P0）
- 实现段落 ASCII 绘制
- 实现表格 ASCII 绘制
- 实现上下文范围控制

**阶段 3: Git Diff 实现**（P0）
- 实现编辑前后对比逻辑
- 实现 diff 渲染

**阶段 4: 工具迁移**（P0）
- 迁移所有 51 个 MCP 工具
- 移除 JSON 格式化代码

**阶段 5: 测试更新**（P0）
- 更新所有单元测试
- 更新所有 E2E 测试
- 更新文档

**阶段 6: 增强功能**（P1）
- 实现图片位置标记
- 实现光标位置标记
- 实现文档结构树

### 7.2 风险与挑战

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Token 消耗大幅增加 | 高 | 用户已接受，无需缓解 |
| 测试用例更新工作量大 | 中 | 使用脚本批量更新测试断言 |
| ASCII 绘制逻辑复杂 | 中 | 参考现有 ASCII 表格库（如 `tabulate`）|
| 破坏性变更影响现有用户 | 低 | 项目处于早期阶段，用户较少 |

---

## 8. 下一步

✅ 需求文档已生成，下一步操作：

**在当前会话执行**：
```bash
/clouditera:dev:spec-dev markdown-response-format --skip-requirements --no-worktree
```

**或在新会话执行**：
```bash
/clouditera:dev:spec-dev markdown-response-format --skip-requirements
```

---

## 附录 A: 示例输出

### A.1 段落插入示例

**调用**：
```python
docx_insert_paragraph(session_id, "Hello World", position="end:document_body")
```

**返回值**（Markdown）：
```markdown
# 操作结果: Insert Paragraph

**Status**: ✅ Success
**Element ID**: para_abc123
**Operation**: Insert Paragraph
**Position**: end:document_body

---

## 📄 Document Context

  ... (3 more elements above) ...

  ┌─────────────────────────────────────────┐
  │ Paragraph (para_abc120)                 │
  │ Previous paragraph content...           │
  └─────────────────────────────────────────┘

>>> [CURSOR] <<<

  ┌─────────────────────────────────────────┐
  │ Paragraph (para_abc123) ⭐ NEW          │
  │ Hello World                             │
  └─────────────────────────────────────────┘

  (end of document)
```

### A.2 段落更新示例

**调用**：
```python
docx_update_paragraph_text(session_id, "para_abc123", "Hello Claude")
```

**返回值**（Markdown）：
```markdown
# 操作结果: Update Paragraph Text

**Status**: ✅ Success
**Element ID**: para_abc123
**Operation**: Update Paragraph Text

---

## 🔄 Changes

  ┌─────────────────────────────────────────┐
  │ Paragraph (para_abc123)                 │
  ├─────────────────────────────────────────┤
- │ Hello World                             │
+ │ Hello Claude                            │
  └─────────────────────────────────────────┘

---

## 📄 Document Context

  ... (3 more elements above) ...

  ┌─────────────────────────────────────────┐
  │ Paragraph (para_abc120)                 │
  │ Previous paragraph content...           │
  └─────────────────────────────────────────┘

  ┌─────────────────────────────────────────┐
  │ Paragraph (para_abc123) ⭐ UPDATED      │
  │ Hello Claude                            │
  └─────────────────────────────────────────┘

  ┌─────────────────────────────────────────┐
  │ Paragraph (para_abc124)                 │
  │ Next paragraph...                       │
  └─────────────────────────────────────────┘

  ... (3 more elements below) ...
```

### A.3 表格插入示例

**调用**：
```python
docx_insert_table(session_id, rows=3, cols=2, position="end:document_body")
```

**返回值**（Markdown）：
```markdown
# 操作结果: Insert Table

**Status**: ✅ Success
**Element ID**: table_def456
**Operation**: Insert Table
**Dimensions**: 3 rows × 2 columns

---

## 📄 Document Context

  ... (2 more elements above) ...

  ┌─────────────────────────────────────────┐
  │ Paragraph (para_abc123)                 │
  │ Text before table...                    │
  └─────────────────────────────────────────┘

>>> [CURSOR] <<<

  ┌─────────────────────────────────────────┐
  │ Table (table_def456) ⭐ NEW             │
  ├─────────────────────┬───────────────────┤
  │ (empty)             │ (empty)           │
  ├─────────────────────┼───────────────────┤
  │ (empty)             │ (empty)           │
  ├─────────────────────┼───────────────────┤
  │ (empty)             │ (empty)           │
  └─────────────────────┴───────────────────┘

  (end of document)
```

---

**文档版本**: v1.0
**最后更新**: 2026-01-23
