---
feature: context-aware-return
complexity: standard
generated_by: clarify
generated_at: 2026-01-21T10:00:00Z
version: 1
---

# 需求文档: 工具返回值上下文增强

> **功能标识**: context-aware-return
> **复杂度**: standard
> **生成方式**: clarify
> **生成时间**: 2026-01-21

## 1. 概述

### 1.1 一句话描述
修改局部操作类工具（读写/搜索），使其默认返回操作目标的前后邻居元素信息（ID、类型、简述），以辅助大模型维护上下文。

### 1.2 核心价值
- **减少 ID 管理负担**：大模型无需显式查询上下文即可获得邻居 ID，方便后续操作（如"在刚才那个段落后面插入"）。
- **增强操作信心**：通过返回的上下文确认操作位置是否正确。
- **提升连续操作效率**：减少 `read_content` 或 `get_structure` 的调用频率。

### 1.3 目标用户
- **主要用户**：Claude (大模型)，在进行文档编辑任务时。

---

## 2. 需求与用户故事

### 2.1 需求清单

| ID | 需求点 | 优先级 | 用户故事 |
|----|--------|--------|----------|
| R-001 | 上下文生成逻辑 | P0 | As a 开发者, I want 一个统一的方法获取元素的前后邻居, so that 我可以在不同工具中复用。 |
| R-002 | 默认返回上下文 | P0 | As a Claude, I want 调用 `add_paragraph` 后看到它前后的段落信息, so that 我知道我在哪里。 |
| R-003 | 可关闭上下文 | P1 | As a 开发者, I want 能够通过参数关闭上下文返回, so that 在批处理或节省 token 时不受影响。 |
| R-004 | 格式化输出 | P0 | As a Claude, I want 上下文以紧凑的文本格式返回, so that 既易读又不浪费 token。 |

### 2.2 验收标准

#### R-001: 上下文生成逻辑
- **WHEN** 给定一个元素（Paragraph/Table/Run）, **THEN** 系统能识别其在父容器中的位置。
- **THEN** 返回前一个元素（Prev）和后一个元素（Next）的 ID 和简要描述（截断文本）。
- **THEN** 处理边界情况（第一个/最后一个元素）。

#### R-002: 默认返回上下文
- **WHEN** 调用 `docx_add_paragraph`, `docx_quick_edit`, `docx_find_paragraphs` 等工具。
- **THEN** 返回值中包含 `<this>` 元素及其前后邻居信息。

#### R-004: 格式化输出
- 格式示例：`para_prev: "Previous text..."; <para_curr>: "Current text"; para_next: "Next text..."`
- 描述限制在 20-30 字符，避免过长。

---

## 3. 功能验收清单

| ID | 功能点 | 验收步骤 | 优先级 | 关联需求 | 通过 |
|----|--------|----------|--------|----------|------|
| F-001 | `get_element_context` 核心方法 | 1. 单元测试：首元素、中间元素、尾元素 2. 验证返回 ID 和描述正确 | P0 | R-001 | ☐ |
| F-002 | `docx_add_paragraph` 增强 | 1. 添加段落 2. 检查返回值包含 prev/next | P0 | R-002 | ☐ |
| F-003 | `docx_find_paragraphs` 增强 | 1. 查找文本 2. 检查每个匹配项包含上下文 | P0 | R-002 | ☐ |
| F-004 | `docx_quick_edit` 增强 | 1. 编辑段落 2. 检查返回值包含上下文 | P0 | R-002 | ☐ |
| F-005 | 关闭参数支持 | 1. 调用工具带 `return_context=False` 2. 验证仅返回 ID | P1 | R-003 | ☐ |

---

## 4. 技术约束

### 4.1 技术栈
- python-docx (现有的)
- docx-mcp-server 架构

### 4.2 涉及工具范围
需要修改以下模块中的局部操作工具：
- `paragraph_tools.py`: `add_paragraph`, `update_paragraph_text`, `delete`
- `run_tools.py`: `add_run`, `update_run_text`
- `table_tools.py`: `add_table`, `add_row` (可选)
- `composite_tools.py`: `quick_edit`, `add_formatted_paragraph`
- `content_tools.py`: `find_paragraphs` (已部分支持，需统一格式)

---

## 5. 排除项

- **全局工具**：`read_content`, `extract_template_structure` 不需要此功能（本身就是上下文）。
- **属性设置**：`set_font`, `set_alignment` 等纯属性修改工具暂不强制返回上下文，除非用户强烈要求（保持原子性）。
- **复杂嵌套**：暂不深入处理多层嵌套（如表格内的表格）的复杂上下文，只返回直接邻居。

---

## 6. 下一步

✅ 在新会话中执行：
```bash
/clouditera:dev:spec-dev context-aware-return --skip-requirements
```
