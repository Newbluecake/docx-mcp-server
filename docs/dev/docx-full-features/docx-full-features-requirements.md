---
feature: docx-full-features
complexity: standard
generated_by: clarify
generated_at: 2026-01-20T12:00:00Z
version: 1
---

# 需求文档: Docx MCP Server 全功能重构

> **功能标识**: docx-full-features
> **复杂度**: standard
> **生成方式**: clarify

## 1. 概述

### 1.1 一句话描述
重构 docx-mcp-server，引入“混合上下文”和“结构化属性设置”机制，以支持 python-docx 的绝大部分功能，同时避免工具列表爆炸。

### 1.2 核心价值
- **完整性**：支持图片、列表、复杂格式、页面布局等高级功能。
- **易用性**：通过“最近创建优先”的上下文机制，减少 Claude 调用时的 ID 传递负担。
- **可维护性**：使用统一的 `set_properties` 接口替代数百个零散的 setter 工具。

### 1.3 目标用户
- **Claude (AI Agent)**：主要用户，需要一个逻辑清晰、参数结构化、上下文感知的 API。

---

## 2. 核心机制设计

### 2.1 混合上下文 (Hybrid Context)
Session 需要维护两个指针：
1.  `last_created_id`: 最后一次创建操作返回的 ID。
2.  `last_accessed_id`: 最后一次读取或修改操作使用的 ID。

**规则**：
- 如果工具调用未提供 `element_id`，默认使用 `last_created_id`。
- 如果提供了 `element_id`，操作成功后更新 `last_accessed_id`。
- `add_run` 等子元素创建工具，若未提供 `parent_id`，自动使用 `last_created_id` 作为父级（需类型检查）。

### 2.2 结构化属性映射 (Structured Properties)
`docx_set_properties` 接受的 `properties` 参数必须符合 python-docx 对象模型：

| 键 (Key) | 对应 python-docx 对象 | 适用对象 |
|:---|:---|:---|
| `font` | `run.font` | Run |
| `paragraph_format` | `paragraph.paragraph_format` | Paragraph |
| `table_style` | `table.style` | Table |
| `cell_format` | (自定义封装) | Cell |

---

## 3. 需求与用户故事

### 3.1 需求清单

| ID | 需求点 | 优先级 | 用户故事 |
|----|--------|--------|----------|
| R-001 | 混合上下文管理 | P0 | As an Agent, 我希望在连续操作时不需要重复传 ID，以便节省 Token 和减少错误。 |
| R-002 | 通用属性设置器 | P0 | As an Agent, 我希望通过一个工具设置字体、对齐和间距，而不是调用三个工具。 |
| R-003 | 图片插入支持 | P1 | As a User, 我希望在文档中插入本地图片。 |
| R-004 | 属性严格验证 | P1 | As a Developer, 我希望传入无效属性时报错，而不是被默默忽略，以便调试。 |
| R-005 | 表格行/列操作 | P2 | As a User, 我希望在现有表格中添加行或列。 |
| R-006 | 增强型定位工具 | P0 | As a User, 我希望按索引或内容查找表格/段落，以便在模板中定位编辑点。 |
| R-007 | 模板文本替换 | P1 | As a User, 我希望能全局或在特定范围内将 `{{key}}` 替换为实际值。 |
| R-008 | 表格复制 | P1 | As a User, 我希望复制整个表格结构（作为模板），以便填充新数据。 |
| R-009 | 文件列表与浏览 | P2 | As a User, 我希望查看服务器目录下的 .docx 文件，以便选择要打开的模板。 |
| R-010 | 自动保存 | P1 | As a User, 我希望在每次修改后自动保存文件，以防止数据丢失，且无需显式调用保存命令。 |

### 3.2 验收标准

#### R-001: 混合上下文管理
- **WHEN** 调用 `docx_insert_paragraph` 后立即调用 `docx_insert_run(text="foo", position=...)`
- **THEN** "foo" 应该被添加到刚才创建的段落中
- **WHEN** 调用 `docx_copy_table` 复制一个表格
- **THEN** 系统应自动将新表格设为当前上下文，后续的 `docx_insert_table_row` 应作用于新表格

#### R-002: 通用属性设置器
- **WHEN** 调用 `docx_set_properties` 传入 `{"font": {"bold": true}, "paragraph_format": {"alignment": "center"}}`
- **THEN** 对应的文本变粗，且段落居中

#### R-006: 增强型定位工具
- **WHEN** 调用 `docx_get_table(index=1)`
- **THEN** 返回文档中第 2 个表格的 ID，并将其设为当前上下文
- **WHEN** 调用 `docx_find_table(text="Revenue")`
- **THEN** 返回包含 "Revenue" 文本的第一个表格 ID

#### R-008: 表格复制
- **WHEN** 复制一个 3x3 的表格
- **THEN** 新表格应保留原表格的样式、列宽和边框设置（内容可选保留）

#### R-009: 文件列表与浏览
- **WHEN** 调用 `docx_list_files(path="./templates")`
- **THEN** 返回该目录下所有 .docx 文件列表
- **WHEN** 尝试列出非允许目录（如 /etc）
- **THEN** (可选) 返回权限错误或限制访问范围

#### R-010: 自动保存
- **WHEN** 在创建会话时指定 `auto_save=True` 和 `file_path`
- **THEN** 每次执行修改操作（如 `docx_insert_paragraph`）后，文件内容应立即写入磁盘

---

## 4. 技术约束

### 4.1 技术栈
- **Python**: 3.10+
- **Library**: `python-docx`
- **Protocol**: MCP (Model Context Protocol)

### 4.2 依赖关系
- 新增 `docx_mcp_server.core.context` 模块管理上下文。
- 新增 `docx_mcp_server.core.properties` 模块处理反射和属性映射。
- 新增 `docx_mcp_server.core.navigation` 模块处理复杂的查找逻辑。

---

## 5. 排除项

- **远程图片下载**：仅支持本地路径，不负责下载 URL。
- **高级模板功能**：不支持 Jinja2 风格的模板替换（那是 python-docx-template 的功能）。
- **批注和修订**：暂不支持。
- **任意文件系统访问**：文件列表功能应限制在特定根目录下（如通过环境变量配置 `DOCX_ROOT`），防止安全风险。

---

## 6. 下一步

✅ 在新会话中执行：
```bash
/clouditera:dev:spec-dev docx-full-features --skip-requirements
```
