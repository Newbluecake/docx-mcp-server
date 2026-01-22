---
feature: element-id-enhancement
complexity: complex
generated_by: clarify
generated_at: 2026-01-23T00:00:00Z
version: 1
---

# 需求文档: Element ID Enhancement

> **功能标识**: element-id-enhancement
> **复杂度**: complex
> **生成方式**: clarify
> **生成时间**: 2026-01-23

## 1. 概述

### 1.1 一句话描述

在所有返回文档结构信息的工具中，为每个元素（段落、表格、单元格等）添加 element_id 字段，使 Agent 能够直接引用和操作这些元素。

### 1.2 核心价值

**解决的问题**：
- 当前部分工具返回的结构信息缺少 element_id，导致 Agent 无法直接操作这些元素
- 需要额外调用查找工具才能获取 element_id，增加了工作流复杂度
- 不同工具的返回格式不一致，影响使用体验

**带来的价值**：
- **提升效率**：Agent 可以一次调用获取结构和 ID，减少 API 往返
- **简化工作流**：无需额外的查找步骤，直接使用返回的 ID 操作元素
- **增强一致性**：所有结构信息工具统一包含 element_id，降低学习成本

### 1.3 目标用户

- **主要用户**：使用 docx-mcp-server 的 AI Agent（如 Claude）
- **次要用户**：开发者（通过更清晰的 API 设计提升开发体验）

---

## 2. 需求与用户故事

### 2.1 需求清单

| ID | 需求点 | 优先级 | 用户故事 |
|----|--------|--------|----------|
| R-001 | docx_extract_template_structure 返回 element_id | P0 | As an Agent, I want to get element_id for each paragraph/table/heading, so that I can directly modify them |
| R-002 | docx_get_structure_summary 返回 element_id | P0 | As an Agent, I want to get element_id in structure summary, so that I can quickly navigate to specific elements |
| R-003 | docx_read_content 默认返回 element_id | P0 | As an Agent, I want to get element_id by default when reading content, so that I don't need to set include_ids=True every time |
| R-004 | docx_get_table_structure 返回 cell_id | P1 | As an Agent, I want to get cell_id for each cell in table structure, so that I can directly modify cell content |
| R-005 | 自动注册元素到 session | P0 | As an Agent, I want returned element_ids to be immediately usable, so that I don't get "element not found" errors |
| R-006 | 保持向后兼容性 | P0 | As a developer, I want existing code to continue working, so that I don't need to update all my scripts |

### 2.2 验收标准

#### R-001: docx_extract_template_structure 返回 element_id
- **WHEN** Agent 调用 `docx_extract_template_structure(session_id)`, **THEN** 系统 **SHALL** 在返回的 JSON 中为每个元素添加 `element_id` 字段
- **WHEN** 返回的元素类型为 paragraph, **THEN** `element_id` **SHALL** 以 `para_` 开头
- **WHEN** 返回的元素类型为 table, **THEN** `element_id` **SHALL** 以 `table_` 开头
- **WHEN** 返回的元素类型为 heading, **THEN** `element_id` **SHALL** 以 `para_` 开头（heading 本质是 paragraph）

#### R-002: docx_get_structure_summary 返回 element_id
- **WHEN** Agent 调用 `docx_get_structure_summary(session_id)`, **THEN** 系统 **SHALL** 在 headings、tables、paragraphs 数组中的每个对象添加 `element_id` 字段
- **WHEN** 返回的 heading 对象, **THEN** **SHALL** 包含 `{"element_id": "para_xxx", "level": 1, "style": "Heading 1", ...}`

#### R-003: docx_read_content 默认返回 element_id
- **WHEN** Agent 调用 `docx_read_content(session_id)` 且未指定 `include_ids`, **THEN** 系统 **SHALL** 默认返回 element_id（`include_ids` 默认值改为 `True`）
- **WHEN** Agent 明确设置 `include_ids=False`, **THEN** 系统 **SHALL** 不返回 element_id（保持向后兼容）

#### R-004: docx_get_table_structure 返回 cell_id
- **WHEN** Agent 调用 `docx_get_table_structure(session_id, table_id)`, **THEN** 系统 **SHALL** 在 `structure_info` 中为每个单元格添加 `cell_id` 字段
- **WHEN** 单元格是合并单元格, **THEN** **SHALL** 返回主单元格的 `cell_id` 并标注 `is_merged: true`

#### R-005: 自动注册元素到 session
- **WHEN** 工具返回 element_id, **THEN** 系统 **SHALL** 自动调用 `session.register_object()` 或 `session._get_element_id(auto_register=True)` 注册元素
- **WHEN** Agent 使用返回的 element_id 调用其他工具, **THEN** 系统 **SHALL** 能够成功找到该元素（不抛出 "element not found" 错误）

#### R-006: 保持向后兼容性
- **WHEN** 现有代码调用修改后的工具, **THEN** 系统 **SHALL** 不破坏现有 JSON 结构（只添加新字段，不删除或重命名现有字段）
- **WHEN** 工具参数签名, **THEN** 系统 **SHALL** 保持不变（不添加、删除或修改必需参数）

---

## 3. 功能验收清单

| ID | 功能点 | 验收步骤 | 优先级 | 关联需求 | 通过 |
|----|--------|----------|--------|----------|------|
| F-001 | docx_extract_template_structure 添加 element_id | 1. 调用工具 2. 解析返回 JSON 3. 验证每个元素有 element_id 4. 验证 ID 前缀正确 | P0 | R-001 | ☐ |
| F-002 | docx_get_structure_summary 添加 element_id | 1. 调用工具 2. 验证 headings/tables/paragraphs 数组中每个对象有 element_id | P0 | R-002 | ☐ |
| F-003 | docx_read_content 默认返回 element_id | 1. 调用工具（不传 include_ids） 2. 验证返回包含 element_id 3. 调用工具（include_ids=False） 4. 验证不返回 element_id | P0 | R-003 | ☐ |
| F-004 | docx_get_table_structure 添加 cell_id | 1. 调用工具 2. 验证 structure_info 中每个单元格有 cell_id | P1 | R-004 | ☐ |
| F-005 | 自动注册元素 | 1. 调用结构工具获取 element_id 2. 使用该 ID 调用其他工具（如 docx_update_paragraph_text） 3. 验证操作成功 | P0 | R-005 | ☐ |
| F-006 | 向后兼容性测试 | 1. 运行现有单元测试 2. 验证所有测试通过 3. 检查 JSON 结构未破坏 | P0 | R-006 | ☐ |
| F-007 | 性能测试 | 1. 对比修改前后的性能 2. 验证自动注册不会显著增加内存占用（< 10%） | P1 | R-005 | ☐ |

---

## 4. 技术约束

### 4.1 技术栈
- **语言**: Python 3.8+
- **核心库**: python-docx
- **框架**: FastMCP (MCP 协议实现)
- **测试框架**: pytest

### 4.2 集成点

**修改的模块**：
1. `src/docx_mcp_server/tools/content_tools.py`
   - `docx_extract_template_structure()`: 修改返回值
   - `docx_read_content()`: 修改 `include_ids` 默认值

2. `src/docx_mcp_server/tools/composite_tools.py`
   - `docx_get_structure_summary()`: 修改返回值

3. `src/docx_mcp_server/tools/table_tools.py`
   - `docx_get_table_structure()`: 修改返回值

4. `src/docx_mcp_server/core/template_parser.py`
   - `extract_heading_structure()`: 添加 element_id 参数
   - `extract_paragraph_structure()`: 添加 element_id 参数
   - `extract_table_structure()`: 添加 element_id 参数

5. `src/docx_mcp_server/core/table_analyzer.py`
   - `detect_irregular_structure()`: 添加 cell_id 字段

**依赖的核心类**：
- `Session`: 使用 `register_object()` 和 `_get_element_id(auto_register=True)`
- `TemplateParser`: 需要传入 session 对象以注册元素
- `TableStructureAnalyzer`: 需要传入 session 对象以注册单元格

### 4.3 性能要求
- 自动注册元素不应显著增加内存占用（< 10%）
- 工具调用延迟增加不超过 5%
- 大文档（1000+ 段落）处理时间增加不超过 10%

### 4.4 兼容性要求
- 保持现有工具的参数签名不变
- 保持现有 JSON 响应结构（只添加字段，不删除或重命名）
- 现有单元测试应全部通过（可能需要更新断言）

---

## 5. 排除项

以下内容**不在**本次需求范围内：

- ❌ **不修改工具参数签名**：保持现有参数不变，不添加新的必需参数
- ❌ **不破坏现有 JSON 结构**：只添加新字段，不删除或重命名现有字段
- ❌ **不重构 Session 类**：只使用现有的 `register_object()` 和 `_get_element_id()` 方法
- ❌ **不修改 MCP 协议层**：只修改工具实现，不涉及 MCP 协议相关代码
- ❌ **不添加迁移指南**：因为是向后兼容的增强，不需要迁移指南

---

## 6. 实施优先级

### P0 - 核心工具（必须完成）
1. `docx_extract_template_structure` - 最常用的结构提取工具
2. `docx_get_structure_summary` - 轻量级结构摘要
3. `docx_read_content` - 内容读取工具
4. 自动注册机制 - 确保返回的 ID 可用

### P1 - 增强功能（建议完成）
1. `docx_get_table_structure` - 表格结构分析
2. 性能测试 - 验证性能影响

### P2 - 文档更新（必须完成）
1. 更新工具 docstring
2. 更新 README.md
3. 更新 CLAUDE.md

---

## 7. 测试策略

### 7.1 单元测试
- 为每个修改的工具编写单元测试
- 验证返回的 JSON 包含 element_id 字段
- 验证 element_id 前缀正确（para_、table_、cell_）
- 验证自动注册功能正常

### 7.2 E2E 测试
- 测试完整工作流：提取结构 → 获取 ID → 修改元素
- 验证跨工具的 ID 引用正常工作

### 7.3 更新现有测试
- 更新现有测试用例以适配新的返回格式
- 确保所有现有测试通过

### 7.4 性能测试
- 对比修改前后的性能指标
- 验证自动注册不会显著影响性能
- 测试大文档（1000+ 段落）的处理时间

---

## 8. 下一步

✅ 需求已澄清，准备进入技术设计阶段。

在当前会话执行：
```bash
/clouditera:dev:spec-dev element-id-enhancement --skip-requirements --no-worktree
```

或在新会话执行：
```bash
/clouditera:dev:spec-dev element-id-enhancement --skip-requirements
```
