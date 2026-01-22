---
feature: mcp-tool-docs
complexity: standard
generated_by: clarify
generated_at: 2026-01-21T12:00:00Z
version: 1
---

# 需求文档: MCP 工具文档增强

> **功能标识**: mcp-tool-docs
> **复杂度**: standard
> **生成方式**: clarify
> **生成时间**: 2026-01-21

## 1. 概述

### 1.1 一句话描述
为 docx-mcp-server 的所有 MCP 工具（server.py 中的 @mcp.tool() 函数）添加详尽的 docstring，包含功能说明、参数详解、使用示例、场景说明和错误处理指南。

### 1.2 核心价值
- **提升可用性**：用户（Claude 和开发者）能够快速理解每个工具的用途和使用方法
- **减少错误**：通过示例和错误处理说明，降低误用概率
- **改善开发体验**：详细的文档让 API 更易于理解和集成

### 1.3 目标用户
- **主要用户**：Claude AI（通过 MCP 协议调用工具）
- **次要用户**：使用 docx-mcp-server 的开发者

---

## 2. 需求与用户故事

### 2.1 需求清单

| ID | 需求点 | 优先级 | 用户故事 |
|----|--------|--------|----------|
| R-001 | 详尽的工具说明 | P0 | 作为 Claude，我希望每个工具都有清晰的功能说明，以便我能准确选择合适的工具 |
| R-002 | 参数详细说明 | P0 | 作为开发者，我希望了解每个参数的类型、含义和约束，以便正确传参 |
| R-003 | 实际使用示例 | P0 | 作为 Claude，我希望看到实际的调用示例，以便我能模仿正确的使用方式 |
| R-004 | 场景说明 | P1 | 作为开发者，我希望了解工具的典型使用场景，以便选择最合适的工具 |
| R-005 | 错误处理指南 | P1 | 作为 Claude，我希望知道可能的错误和处理方式，以便优雅地处理异常 |

### 2.2 验收标准

#### R-001: 详尽的工具说明
- **WHEN** 查看任何 MCP 工具的 docstring，**THEN** 应包含：
  - 工具的核心功能（1-2 句话）
  - 工具的适用场景
  - 与其他工具的关系（如果有）

#### R-002: 参数详细说明
- **WHEN** 查看工具的参数说明，**THEN** 每个参数应包含：
  - 参数类型（str, int, bool 等）
  - 参数含义和用途
  - 是否必需/可选
  - 默认值（如果有）
  - 取值范围或约束

#### R-003: 实际使用示例
- **WHEN** 查看工具的 docstring，**THEN** 应包含至少 1-2 个实际调用示例
- **WHEN** 工具有多种用法，**THEN** 应提供多个示例覆盖不同场景

#### R-004: 场景说明
- **WHEN** 工具有多个典型使用场景，**THEN** 应列出并说明每个场景
- **WHEN** 工具与其他工具配合使用，**THEN** 应说明配合方式

#### R-005: 错误处理指南
- **WHEN** 工具可能抛出异常，**THEN** 应说明：
  - 可能的错误类型
  - 错误发生的原因
  - 如何避免或处理错误

---

## 3. 功能验收清单

| ID | 功能点 | 验收步骤 | 优先级 | 关联需求 | 通过 |
|----|--------|----------|--------|----------|------|
| F-001 | 核心工具文档 | 1. 检查 docx_create, docx_save, docx_close 的 docstring 2. 验证包含所有必需元素 | P0 | R-001~R-005 | ☐ |
| F-002 | 内容操作工具文档 | 1. 检查 docx_insert_paragraph, docx_insert_heading, docx_insert_run 等 2. 验证示例完整 | P0 | R-001~R-005 | ☐ |
| F-003 | 格式化工具文档 | 1. 检查 docx_set_font, docx_set_alignment 等 2. 验证参数说明清晰 | P0 | R-001~R-005 | ☐ |
| F-004 | 表格工具文档 | 1. 检查 docx_insert_table, docx_get_cell 等 2. 验证场景说明完整 | P0 | R-001~R-005 | ☐ |
| F-005 | 高级功能工具文档 | 1. 检查 docx_extract_template_structure, docx_copy_paragraph 等 2. 验证错误处理说明 | P1 | R-001~R-005 | ☐ |

---

## 4. 技术约束

### 4.1 技术栈
- **语言**：Python 3.10+
- **框架**：FastMCP (MCP 协议实现)
- **文档格式**：Google Style Docstring

### 4.2 文档格式规范

**标准格式**：
```python
@mcp.tool()
def docx_example_tool(session_id: str, param1: str, param2: Optional[int] = None) -> str:
    """
    [一句话功能描述]

    [详细功能说明，2-3 句话]

    Typical Use Cases:
        - [场景1描述]
        - [场景2描述]

    Args:
        session_id (str): [参数说明，包含约束]
        param1 (str): [参数说明]
        param2 (Optional[int], optional): [参数说明]. Defaults to None.

    Returns:
        str: [返回值说明]

    Raises:
        ValueError: [错误条件1]
        RuntimeError: [错误条件2]

    Examples:
        Basic usage:
        >>> session_id = docx_create()
        >>> result = docx_example_tool(session_id, "value1")
        >>> print(result)
        'Success'

        Advanced usage:
        >>> result = docx_example_tool(session_id, "value1", param2=10)

    Notes:
        - [重要提示1]
        - [重要提示2]

    See Also:
        - docx_related_tool1: [关系说明]
        - docx_related_tool2: [关系说明]
    """
    # 实现代码
```

### 4.3 集成点
- **修改文件**：`src/docx_mcp_server/server.py`
- **影响范围**：所有 @mcp.tool() 装饰的函数
- **向后兼容**：仅修改 docstring，不改变函数签名和行为

---

## 5. 工具分类与优先级

### 5.1 核心生命周期工具（P0）
- `docx_create` - 创建/加载文档会话
- `docx_save` - 保存文档
- `docx_close` - 关闭会话
- `docx_read_content` - 读取文档内容

### 5.2 内容操作工具（P0）
- `docx_insert_paragraph` - 添加段落
- `docx_insert_heading` - 添加标题
- `docx_insert_run` - 添加文本块
- `docx_update_paragraph_text` - 更新段落文本
- `docx_update_run_text` - 更新文本块

### 5.3 格式化工具（P0）
- `docx_set_font` - 设置字体
- `docx_set_alignment` - 设置对齐
- `docx_set_properties` - 设置属性
- `docx_insert_page_break` - 添加分页符
- `docx_set_margins` - 设置页边距

### 5.4 表格工具（P0）
- `docx_insert_table` - 创建表格
- `docx_get_cell` - 获取单元格
- `docx_insert_paragraph_to_cell` - 单元格添加段落
- `docx_insert_table_row` - 添加行
- `docx_insert_table_col` - 添加列
- `docx_fill_table` - 批量填充表格
- `docx_copy_table` - 复制表格
- `docx_find_table` - 查找表格
- `docx_get_table` - 获取表格

### 5.5 高级功能工具（P1）
- `docx_extract_template_structure` - 提取模板结构
- `docx_copy_paragraph` - 复制段落
- `docx_find_paragraphs` - 查找段落
- `docx_insert_image` - 插入图片
- `docx_replace_text` - 替换文本
- `docx_delete` - 删除元素
- `docx_get_context` - 获取上下文
- `docx_list_files` - 列出文件

---

## 6. 排除项

- **不修改**：工具的实现逻辑和行为
- **不添加**：新的工具或功能
- **不改变**：函数签名和参数类型
- **不翻译**：保持 docstring 为英文（MCP 协议标准）

---

## 7. 实施建议

### 7.1 分批实施
1. **第一批**：核心生命周期工具（4 个）
2. **第二批**：内容操作 + 格式化工具（8 个）
3. **第三批**：表格工具（9 个）
4. **第四批**：高级功能工具（8 个）

### 7.2 质量检查
- 每个工具的 docstring 长度应在 15-30 行
- 至少包含 1 个基础示例
- 复杂工具应包含 2-3 个示例
- 所有参数都有清晰说明
- 常见错误都有说明

---

## 8. 下一步

✅ 在新会话中执行：
```bash
/clouditera:dev:spec-dev mcp-tool-docs --skip-requirements
```
