# 任务拆分: Cursor Navigation Enhanced

**版本**: 2.0 (Redesign)
**状态**: Draft
**依赖**: docs/dev/cursor-navigation-enhanced/cursor-navigation-enhanced-design.md

## 任务清单

### Group 1: Core Services (核心服务)

| 任务 ID | 标题 | 描述 | 复杂度 | 依赖 |
|---------|------|------|--------|------|
| T-001 | XML 基础与 Navigator | 提取 `cursor_tools` 和 `copy_engine` 中的 XML 操作到 `core.xml_util`。实现 `ElementNavigator` 类，支持 `get_parent`, `get_siblings`, `iter_children`。 | Standard | - |
| T-002 | 实现 ContextVisualizer | 实现 `ContextVisualizer` 类，生成 ASCII 树状视图。支持 `concise` (默认) 和 `tree` 两种模式。需要处理文本截断和节点类型标记。 | Standard | T-001 |
| T-003 | 实现 PositionResolver 与 Builder | 实现 `PositionResolver` 解析 `after:ID` 等语法并执行插入。实现 `ContextBuilder` 组装 ID、Path 和 Visual 字段。 | Standard | T-001, T-002 |

### Group 2: Tool Integration (工具集成)

| 任务 ID | 标题 | 描述 | 复杂度 | 依赖 |
|---------|------|------|--------|------|
| T-004 | 升级 Paragraph 相关工具 | 更新 `docx_add_paragraph` 和 `docx_add_heading`。添加 `position` 参数支持，使用 `PositionResolver` 处理插入，返回 `ContextBuilder` 生成的 JSON。 | Simple | T-003 |
| T-005 | 升级 Table 相关工具 | 更新 `docx_add_table`。支持 `position` 参数（段落前后插入）。集成新的上下文返回格式。 | Simple | T-003 |
| T-006 | 升级 Image 与辅助工具 | 更新 `docx_insert_image` 支持 `position`。检查是否需要更新 `docx_add_run` (通常不需要 position，但需要上下文)。 | Simple | T-003 |

### Group 3: Verification (验证)

| 任务 ID | 标题 | 描述 | 复杂度 | 依赖 |
|---------|------|------|--------|------|
| T-007 | E2E 验证与可视化测试 | 编写测试验证：1. 乱序插入是否符合预期；2. 返回的 ASCII 树是否准确反映文档结构；3. Token 消耗是否在可控范围内。 | Standard | T-004, T-005 |

## 执行策略

- **优先级**: T-002 (Visualizer) 是本次重构的核心，应优先通过单元测试验证其输出效果。
- **兼容性**: 在 T-004/5 实施时，必须保证不传 `position` 参数时的行为与旧版本完全一致（追加到末尾）。
