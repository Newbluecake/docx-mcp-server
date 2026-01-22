---
feature: cursor-navigation-enhanced
complexity: standard
generated_by: clarify
generated_at: 2026-01-22T12:00:00Z
version: 1
---

# 需求文档: Cursor Navigation Enhanced

> **功能标识**: cursor-navigation-enhanced
> **复杂度**: standard
> **生成方式**: clarify
> **生成时间**: 2026-01-22

## 1. 概述

### 1.1 一句话描述
增强 MCP 工具的文档导航和位置控制能力，使工具调用返回包含周围元素（父级、兄弟）的丰富上下文，并支持在工具调用时通过 `position` 参数精确指定插入位置。

### 1.2 核心价值
- **增强导航**：通过返回父级、兄弟元素 ID，让 Agent 更容易理解文档结构和当前位置。
- **精确控制**：允许在创建元素时直接指定位置（如“在段落 A 之后”），减少对 `docx_cursor_move` 的依赖，提高操作效率。
- **上下文感知**：提供多层级的上下文信息，帮助 Agent 做出更准确的决策。

### 1.3 目标用户
- **主要用户**：使用 docx-mcp-server 的 AI Agent（如 Claude）。
- **次要用户**：需要精确控制文档生成的开发者。

---

## 2. 需求与用户故事

### 2.1 需求清单

| ID | 需求点 | 优先级 | 用户故事 |
|----|--------|--------|----------|
| R-001 | 增强 Cursor 对象结构 | P0 | 作为 Agent，我希望工具返回的 cursor 信息包含父元素和兄弟元素的 ID，以便我了解当前在文档中的位置。 |
| R-002 | 工具支持显式 Position 参数 | P0 | 作为 Agent，我希望在调用 `add_paragraph` 等工具时能直接指定 `position`（如 `after:para_123`），以便一步完成定位和插入。支持在表格单元格等嵌套结构中定位。 |
| R-003 | 按需获取详细上下文 | P1 | 作为 Agent，我希望通过参数（如 `view_mode`）控制返回的上下文详细程度（仅 ID vs 包含文本摘要/结构树），以节省 Token。 |
| R-004 | 统一返回格式 | P0 | 作为 Agent，我希望所有工具的返回格式保持一致，都包含增强后的 cursor 信息。 |
| R-005 | 直观的上下文可视化 | P0 | 作为 Agent，我希望上下文包含字段（如 `visual_tree`），以 ASCII 树或缩进列表形式直观展示当前节点及其周围结构，而非仅是 ID 列表。 |

### 2.2 验收标准

#### R-001 & R-005: 增强 Cursor 与可视化
- **WHEN** 调用工具成功后, **THEN** `data.cursor` 包含：
    - `element_id`: 当前 ID
    - `structure`: 结构化对象 (parent, siblings)
    - `visual`: 字符串形式的直观表示（如下例）
      ```
      Body
      ├── Heading 1 (h_123): "Introduction"
      ├── [Paragraph (p_456): "Current text..."] <--- Current
      └── Table (t_789): 3 rows, 2 cols
      ```

#### R-002: 工具支持显式 Position 参数
- **WHEN** 调用 `docx_insert_paragraph(..., position="after:para_123")`, **THEN** 插入到指定段落后。
- **WHEN** 调用 `docx_insert_paragraph(..., position="inside:cell_abc")` (或类似语义), **THEN** 追加到单元格内容末尾。
- **WHEN** 引用不存在的 ID, **THEN** 返回明确的 `ElementNotFound` 错误。

#### R-003: 按需获取详细上下文
- **WHEN** 不传参数, **THEN** 默认返回 `view_mode="concise"` (仅 ID 和简短 visual)。
- **WHEN** 传递 `view_mode="tree"` (暂定参数名), **THEN** 返回更深层级或更宽的兄弟节点范围。

---

## 3. 功能验收清单

| ID | 功能点 | 验收步骤 | 优先级 | 关联需求 | 通过 |
|----|--------|----------|--------|----------|------|
| F-001 | Cursor 结构增强 | 1. 调用 `docx_insert_paragraph` 2. 检查返回 JSON 包含 parent/sibling ID | P0 | R-001 | ☐ |
| F-002 | Position 参数支持 | 1. 创建段落 A 2. 调用 `docx_insert_paragraph(..., position="before:para_A")` 3. 验证新段落位于 A 之前 | P0 | R-002 | ☐ |
| F-003 | 路径信息返回 | 1. 在表格单元格内创建内容 2. 检查返回的 path 字段是否正确反映层级 | P1 | R-001 | ☐ |

---

## 4. 技术约束

### 4.1 性能与 Token
- **Token 消耗**：增强的上下文信息会增加 Token 使用量。必须严格控制默认返回的信息量，避免包含过长的文本内容或过深的递归结构。
- **响应速度**：计算上下文（特别是兄弟节点和路径）不应显著增加工具调用的延迟。

### 4.2 兼容性
- **向后兼容**：插入类工具统一要求传入 `position`，示例与测试需同步更新。
- **JSON 结构**：保持 v2.1 引入的 `{"status":..., "data":...}` 结构，增强内容应放在 `data` 或 `data.cursor` 中。

---

## 5. 排除项

- **全文档树实时返回**：每次调用都返回整个文档的 DOM 树是不现实的（Token 爆炸）。
- **非结构化文档的精确导航**：对于极其混乱的文档，路径导航可能受限。

---

## 6. 下一步

✅ 在新会话中执行：
```bash
/clouditera:dev:spec-dev cursor-navigation-enhanced --skip-requirements
```
