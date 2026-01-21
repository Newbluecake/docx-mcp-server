# 技术设计: MCP 工具文档增强

> **功能标识**: mcp-tool-docs
> **复杂度**: standard
> **设计版本**: 1.0
> **设计日期**: 2026-01-21

## 1. 设计概述

### 1.1 设计目标
为 docx-mcp-server 的所有 MCP 工具添加详尽的 Google Style docstring，提升 API 可用性和开发体验。

### 1.2 设计原则
- **一致性**: 所有工具使用统一的文档格式
- **完整性**: 覆盖功能说明、参数、返回值、异常、示例、场景
- **实用性**: 示例代码可直接运行，错误说明清晰
- **最小化**: 仅修改 docstring，不改变函数签名和实现

## 2. 技术方案

### 2.1 文档格式规范

采用 Google Style Docstring，包含以下部分：

```python
@mcp.tool()
def docx_example_tool(session_id: str, param1: str, param2: Optional[int] = None) -> str:
    """
    [一句话功能描述]

    [详细功能说明，2-3 句话，说明工具的核心价值和适用场景]

    Typical Use Cases:
        - [场景1]: [场景描述]
        - [场景2]: [场景描述]

    Args:
        session_id (str): Active session ID returned by docx_create().
        param1 (str): [参数说明，包含类型、用途、约束]
        param2 (Optional[int], optional): [参数说明]. Defaults to None.

    Returns:
        str: [返回值说明，包含格式和内容]

    Raises:
        ValueError: [错误条件1，如何避免]
        RuntimeError: [错误条件2，如何避免]

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

### 2.2 工具分类

根据功能将 29 个工具分为 4 类：

#### 2.2.1 核心生命周期工具 (4 个)
- `docx_create` - 创建/加载文档会话
- `docx_save` - 保存文档
- `docx_close` - 关闭会话
- `docx_read_content` - 读取文档内容

#### 2.2.2 内容操作工具 (5 个)
- `docx_add_paragraph` - 添加段落
- `docx_add_heading` - 添加标题
- `docx_add_run` - 添加文本块
- `docx_update_paragraph_text` - 更新段落文本
- `docx_update_run_text` - 更新文本块

#### 2.2.3 格式化工具 (5 个)
- `docx_set_font` - 设置字体
- `docx_set_alignment` - 设置对齐
- `docx_set_properties` - 设置属性
- `docx_add_page_break` - 添加分页符
- `docx_set_margins` - 设置页边距

#### 2.2.4 表格工具 (9 个)
- `docx_add_table` - 创建表格
- `docx_get_cell` - 获取单元格
- `docx_add_paragraph_to_cell` - 单元格添加段落
- `docx_add_table_row` - 添加行
- `docx_add_table_col` - 添加列
- `docx_fill_table` - 批量填充表格
- `docx_copy_table` - 复制表格
- `docx_find_table` - 查找表格
- `docx_get_table` - 获取表格

#### 2.2.5 高级功能工具 (6 个)
- `docx_extract_template_structure` - 提取模板结构
- `docx_copy_paragraph` - 复制段落
- `docx_find_paragraphs` - 查找段落
- `docx_insert_image` - 插入图片
- `docx_replace_text` - 替换文本
- `docx_delete` - 删除元素
- `docx_get_context` - 获取上下文
- `docx_list_files` - 列出文件
- `docx_format_copy` - 复制格式

### 2.3 实施策略

#### 2.3.1 分批实施
按工具类别分 4 个任务批次，每批独立完成和评审。

#### 2.3.2 质量标准
- 每个工具的 docstring 长度: 15-30 行
- 至少包含 1 个基础示例
- 复杂工具包含 2-3 个示例
- 所有参数都有清晰说明
- 常见错误都有说明

#### 2.3.3 向后兼容
- 仅修改 docstring，不改变函数签名
- 不修改函数实现逻辑
- 不改变返回值格式

## 3. 关键设计决策

### 3.1 为什么使用 Google Style？
- MCP 协议推荐格式
- 可读性强，结构清晰
- 支持自动文档生成工具

### 3.2 为什么分批实施？
- 降低单次修改风险
- 便于分阶段评审
- 支持并行开发

### 3.3 示例代码设计原则
- 使用真实的函数调用
- 展示完整的工作流（create → operate → save → close）
- 覆盖常见场景和边界情况

## 4. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 文档与实现不一致 | 高 | 每个工具测试验证示例代码 |
| 文档过于冗长 | 中 | 严格控制长度，精简表达 |
| 遗漏关键信息 | 中 | 使用 checklist 逐项检查 |

## 5. 验收标准

### 5.1 功能验收
- [ ] 所有 29 个工具都有完整 docstring
- [ ] 每个工具至少 1 个可运行示例
- [ ] 所有参数都有类型和说明
- [ ] 常见错误都有说明

### 5.2 质量验收
- [ ] 文档格式统一，符合 Google Style
- [ ] 示例代码经过测试验证
- [ ] 无拼写和语法错误
- [ ] 代码行为未改变

## 6. 后续优化

- 考虑添加自动文档生成脚本
- 考虑添加文档覆盖率检查工具
- 考虑生成 HTML/Markdown 格式的 API 文档
