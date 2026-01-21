# 任务列表: Format Painter

> **功能**: format-painter
> **总任务数**: 6
> **并行组**: 2

## Group 1: Core Implementation
串行执行核心逻辑开发。

- [ ] **T-001**: 创建 FormatPainter 基础架构
    - 建立 `src/docx_mcp_server/core/format_painter.py`
    - 实现入口函数 `copy_format(source, target)`
    - 实现类型分发逻辑
    - 在 `server.py` 注册 `docx_format_copy` 工具

- [ ] **T-002**: 实现 Run 格式复制逻辑
    - 实现 `_copy_run_format`
    - 覆盖所有字体属性 (Bold, Italic, Size, Color, etc.)
    - 单元测试: `tests/unit/test_format_painter_run.py`

- [ ] **T-003**: 实现 Paragraph 格式复制逻辑
    - 实现 `_copy_paragraph_format`
    - 覆盖对齐、缩进、行距
    - 单元测试: `tests/unit/test_format_painter_para.py`

- [ ] **T-004**: 实现 Table 深度复制逻辑
    - 实现 `_copy_table_format`
    - 实现 OXML 操作 (Borders, Shading)
    - 单元测试: `tests/unit/test_format_painter_table.py`

## Group 2: Advanced Features & Polish
依赖 Group 1 完成。

- [ ] **T-005**: 实现智能类型匹配 (Cross-type)
    - 处理 Para -> Run
    - 处理 Run -> Para
    - 错误处理 (Table mismatch)

- [ ] **T-006**: 集成测试与边界测试
    - 编写 E2E 测试 `tests/e2e/test_format_painter_workflow.py`
    - 验证复杂组合
    - 验证错误消息清晰度
