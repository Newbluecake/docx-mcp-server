## Planning 阶段完成

已生成以下文档：

### 需求分析
- 文件: `docs/dev/format-copy-system/format-copy-system-requirements.md` (已有)
- 摘要: 包含原子化复制、批量区间复制、格式模板系统等 7 个核心需求。

### 技术设计
- 文件: `docs/dev/format-copy-system/format-copy-system-design.md`
- 摘要:
  - **核心架构**: 引入 `TemplateManager` (格式序列化) 和 `CopyEngine` (基于 XML DeepCopy 的复制引擎)。
  - **Session 增强**: 扩展 `Session` 类支持 `element_metadata` 用于来源追踪。
  - **依赖关系**: SessionManager -> CopyEngine/TemplateManager -> Session。

### 任务拆分
- 文件: `docs/dev/format-copy-system/format-copy-system-tasks.md`
- 任务数: 10 个
- 阶段:
  1. 基础设施与核心引擎 (T-001~T-004)
  2. MCP 工具实现 (T-005~T-008)
  3. 验证与验收 (T-009~T-010)

### 推荐操作

**当前复杂度**: `complex`

- **方案审查** (强烈推荐): 此次变更涉及核心 `Session` 类修改和复杂的 XML 操作，建议进行代码级方案审查。
- **直接实施**: 如果您确信设计无误，可以直接开始实施。

请确认下一步操作：