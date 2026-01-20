---
feature: load-existing-file
complexity: standard
generated_by: clarify
generated_at: 2026-01-20
version: 1
---

# 需求文档: 支持加载和编辑现有 Word 文档

> **功能标识**: load-existing-file
> **复杂度**: standard
> **生成方式**: clarify
> **生成时间**: 2026-01-20

## 1. 概述

### 1.1 一句话描述
扩展 MCP 服务器功能，使其能够加载本地现有的 `.docx` 文件，并提供搜索和读取内容的工具，以便对文档进行编辑或追加内容。

### 1.2 核心价值
目前服务器只能创建空白文档，无法处理现有文档。本功能将支持“打开 -> 读取/搜索 -> 编辑 -> 保存”的完整工作流，极大地扩展了其实用性，使其能用于文档修订、模板填充和内容提取场景。

### 1.3 目标用户
- **主要用户**：Claude (作为 MCP Client)，需要读取用户提供的 Word 文档并进行修改。

---

## 2. 需求与用户故事

### 2.1 需求清单

| ID | 需求点 | 优先级 | 用户故事 |
|----|--------|--------|----------|
| R-001 | 支持加载现有文件 | P0 | 作为 Claude，我想在创建会话时指定文件路径，以便编辑现有文档。 |
| R-002 | 全文内容读取 | P0 | 作为 Claude，我想读取文档的文本内容，以便理解文档当前的结构和内容。 |
| R-003 | 搜索并获取元素ID | P0 | 作为 Claude，我想通过关键词搜索段落，并获得其 `element_id`，以便对特定段落进行修改（如设置样式、追加文本）。 |

### 2.2 验收标准

#### R-001: 支持加载现有文件
- **WHEN** 调用 `docx_create(file_path="/path/to/existing.docx")`
- **THEN** 会话被创建，且文档内容与磁盘上的文件一致
- **AND** 如果文件不存在，应返回明确的错误

#### R-002: 全文内容读取
- **WHEN** 调用 `docx_read_content(session_id)`
- **THEN** 返回文档的文本概览
- **AND** 返回结果应包含关键元素的 ID（可选，或通过 separate tool），以便后续操作

#### R-003: 搜索并获取元素ID
- **WHEN** 调用 `docx_find_paragraphs(session_id, query="Target Text")`
- **THEN** 返回所有包含 "Target Text" 的段落列表
- **AND** 每个列表项包含：`element_id` (用于后续操作) 和 `text` (用于确认)

---

## 3. 功能验收清单

| ID | 功能点 | 验收步骤 | 优先级 | 关联需求 | 通过 |
|----|--------|----------|--------|----------|------|
| F-001 | 更新 `docx_create` | 1. `docx_create("/path/to/test.docx")` 2. 保存并验证内容未丢失 | P0 | R-001 | ☐ |
| F-002 | 新增 `docx_read_content` | 1. 加载文档 2. 调用工具 3. 验证返回了文档中的文本 | P1 | R-002 | ☐ |
| F-003 | 新增 `docx_find_paragraphs` | 1. 加载包含"Hello World"的文档 2. 搜索"Hello" 3. 验证返回了有效的 ID | P0 | R-003 | ☐ |

---

## 4. 技术约束

### 4.1 技术栈
- `python-docx` (已引入)
- `FastMCP` (已引入)

### 4.2 API 设计约束
- **ID 注册**：加载现有文档时，其中的对象（段落、表格）最初并未注册到 `Session.object_registry`。
- **懒加载策略**：不应在加载时遍历注册所有对象（性能差）。应在 `find` 或 `read` 操作时，将找到的对象注册并返回 ID。

---

## 5. 排除项

- **复杂的表格结构读取**：本次主要关注文本段落的搜索和编辑，复杂表格的精确坐标定位暂不作为核心搜索目标（但可以通过遍历支持）。
- **图片提取**：不处理文档中的图片提取。

---

## 6. 下一步

✅ 在新会话中执行：
```bash
/clouditera:dev:spec-dev load-existing-file --skip-requirements
```
