---
feature: special-position-ids
complexity: standard
version: 1
created_at: 2026-01-24T10:50:00Z
total_tasks: 8
parallel_groups: 3
---

# 任务拆分: Special Position IDs

> **功能标识**: special-position-ids
> **复杂度**: standard
> **任务总数**: 8
> **并行组数**: 3

---

## 任务依赖图

```
T-001 (Session 增强)
  ↓
T-002 (PositionResolver 增强)
  ↓
┌─────────────┬─────────────┬─────────────┐
│   T-003     │   T-004     │   T-005     │  ← 并行组 1
│ (工具层修改) │ (错误处理)   │ (单元测试)   │
└─────────────┴─────────────┴─────────────┘
  ↓
┌─────────────┬─────────────┐
│   T-006     │   T-007     │  ← 并行组 2
│ (集成测试)   │  (E2E测试)  │
└─────────────┴─────────────┘
  ↓
T-008 (文档更新)
```

---

## 任务列表

### T-001: Session 类增强

**优先级**: P0
**复杂度**: Medium
**预计时间**: 30 分钟
**依赖**: 无
**并行组**: -

#### 描述

修改 `Session` 类，添加特殊 ID 跟踪和解析功能。

#### 实施步骤

1. 在 `Session` dataclass 中添加新字段：
   - `last_insert_id: Optional[str] = None`
   - `last_update_id: Optional[str] = None`

2. 实现 `resolve_special_id(self, special_id: str) -> str` 方法：
   - 支持 `last_insert`, `last_update`, `cursor`, `current`
   - 大小写不敏感（使用 `.lower()`）
   - 对于非特殊 ID，直接返回原值
   - 无法解析时抛出 `ValueError` 并附带清晰消息

3. 修改 `update_context()` 方法：
   - 当 `action="create"` 时，设置 `self.last_insert_id = element_id`
   - 当 `action="update"` 时，设置 `self.last_update_id = element_id`

4. 修改 `get_object()` 方法：
   - 在查找 `object_registry` 前，先调用 `resolve_special_id()`
   - 捕获 `ValueError` 并向上传播（由调用者处理）

#### 验收标准

- [ ] `Session` 类包含 `last_insert_id` 和 `last_update_id` 字段
- [ ] `resolve_special_id()` 正确解析所有 4 种特殊 ID
- [ ] `resolve_special_id()` 对非特殊 ID 返回原值
- [ ] `resolve_special_id()` 在无法解析时抛出 `ValueError`
- [ ] `update_context()` 正确更新特殊 ID 状态
- [ ] `get_object()` 自动解析特殊 ID

#### 测试要点

- 测试 `resolve_special_id()` 的所有分支
- 测试大小写不敏感性
- 测试未初始化时的错误消息
- 测试 `get_object()` 与特殊 ID 的集成

#### 涉及文件

- `src/docx_mcp_server/core/session.py`

---

### T-002: PositionResolver 增强

**优先级**: P0
**复杂度**: Low
**预计时间**: 15 分钟
**依赖**: T-001
**并行组**: -

#### 描述

修改 `PositionResolver.resolve()` 方法，支持在 position 字符串中使用特殊 ID。

#### 实施步骤

1. 在 `resolve()` 方法中，解析 `target_id` 后：
   - 调用 `self.session.resolve_special_id(target_id)`
   - 捕获 `ValueError` 并重新抛出，附加位置上下文

2. 使用解析后的 ID 进行后续查找

#### 验收标准

- [ ] `PositionResolver.resolve()` 支持特殊 ID
- [ ] 错误消息包含位置上下文（如 "Position resolution failed: ..."）
- [ ] 现有使用具体 ID 的代码继续工作

#### 测试要点

- 测试 `position="after:last_insert"` 等场景
- 测试特殊 ID 无法解析时的错误消息
- 测试向后兼容性（具体 ID）

#### 涉及文件

- `src/docx_mcp_server/services/navigation.py`

---

### T-003: 工具层错误处理

**优先级**: P0
**复杂度**: Medium
**预计时间**: 45 分钟
**依赖**: T-001
**并行组**: 1

#### 描述

为所有接受 `element_id` 参数的工具添加特殊 ID 错误处理。

#### 实施步骤

1. 识别所有需要修改的工具（约 15-20 个）：
   - `paragraph_tools.py`: `docx_update_paragraph_text`, `docx_copy_paragraph`, `docx_delete`
   - `run_tools.py`: `docx_update_run_text`, `docx_set_font`
   - `table_tools.py`: `docx_get_cell`, `docx_copy_table`, 行列操作
   - `format_tools.py`: `docx_set_alignment`, `docx_format_copy`, `docx_set_properties`
   - `advanced_tools.py`: `docx_replace_text`, `docx_insert_image`
   - `copy_tools.py`: `docx_get_element_source`, `docx_copy_elements_range`

2. 为每个工具添加 try-except 块：
   ```python
   try:
       element = session.get_object(element_id)
       if not element:
           return create_error_response(
               f"Element '{element_id}' not found",
               error_type="ElementNotFound"
           )
       # ... operation ...
   except ValueError as e:
       if "Special ID" in str(e):
           return create_error_response(
               str(e),
               error_type="SpecialIDNotAvailable"
           )
       raise
   ```

3. 确保错误响应遵循 Markdown 格式

#### 验收标准

- [ ] 所有工具正确处理特殊 ID
- [ ] 特殊 ID 错误返回 `SpecialIDNotAvailable` 错误类型
- [ ] 错误消息清晰且可操作
- [ ] 现有功能不受影响

#### 测试要点

- 测试每个工具使用特殊 ID 的成功场景
- 测试特殊 ID 不可用时的错误响应
- 测试错误响应格式符合 Markdown 规范

#### 涉及文件

- `src/docx_mcp_server/tools/paragraph_tools.py`
- `src/docx_mcp_server/tools/run_tools.py`
- `src/docx_mcp_server/tools/table_tools.py`
- `src/docx_mcp_server/tools/format_tools.py`
- `src/docx_mcp_server/tools/advanced_tools.py`
- `src/docx_mcp_server/tools/copy_tools.py`

---

### T-004: 响应格式增强

**优先级**: P1
**复杂度**: Low
**预计时间**: 15 分钟
**依赖**: T-001
**并行组**: 1

#### 描述

在 `response.py` 中添加对 `SpecialIDNotAvailable` 错误类型的支持，并提供友好的建议。

#### 实施步骤

1. 确认 `create_error_response()` 支持 `error_type` 参数（已存在）

2. 为 `SpecialIDNotAvailable` 错误添加建议文本：
   ```python
   SUGGESTIONS = {
       "SpecialIDNotAvailable": "Make sure you have performed the required operation before using this special ID.",
       # ... other suggestions ...
   }
   ```

3. 在错误响应中包含建议（如果适用）

#### 验收标准

- [ ] `SpecialIDNotAvailable` 错误包含友好建议
- [ ] 错误响应格式符合 Markdown 规范
- [ ] 建议文本清晰且可操作

#### 测试要点

- 测试错误响应包含建议部分
- 测试建议文本的准确性

#### 涉及文件

- `src/docx_mcp_server/core/response.py`

---

### T-005: 单元测试

**优先级**: P0
**复杂度**: Medium
**预计时间**: 45 分钟
**依赖**: T-001
**并行组**: 1

#### 描述

为 Session 类的新功能编写全面的单元测试。

#### 实施步骤

1. 创建 `tests/unit/test_special_position_ids.py`

2. 测试 `resolve_special_id()`:
   - 测试所有 4 种特殊 ID
   - 测试大小写不敏感
   - 测试非特殊 ID 的 pass-through
   - 测试未初始化时的错误

3. 测试 `get_object()` 集成:
   - 测试使用特殊 ID 获取对象
   - 测试特殊 ID 解析失败时的异常

4. 测试 `update_context()`:
   - 测试 `action="create"` 更新 `last_insert_id`
   - 测试 `action="update"` 更新 `last_update_id`

5. 测试边界情况:
   - 元素删除后使用 `last_insert`
   - 会话刚创建时使用特殊 ID

#### 验收标准

- [ ] 测试覆盖率 > 95%（针对新增代码）
- [ ] 所有测试通过
- [ ] 测试用例清晰且易于维护

#### 测试要点

- 使用 pytest fixtures 创建测试 session
- 测试所有成功和失败路径
- 验证错误消息的准确性

#### 涉及文件

- `tests/unit/test_special_position_ids.py` (新建)

---

### T-006: 集成测试

**优先级**: P0
**复杂度**: Medium
**预计时间**: 45 分钟
**依赖**: T-002, T-003, T-004, T-005
**并行组**: 2

#### 描述

测试特殊 ID 与 PositionResolver 和各工具的集成。

#### 实施步骤

1. 创建 `tests/integration/test_special_ids_integration.py`

2. 测试 PositionResolver 集成:
   - 测试 `position="after:last_insert"`
   - 测试 `position="inside:cursor"`
   - 测试特殊 ID 解析失败时的错误

3. 测试工具集成:
   - 测试 `docx_insert_run(session_id, "Text", position="inside:last_insert")`
   - 测试 `docx_update_paragraph_text(session_id, "last_insert", "New text")`
   - 测试 `docx_set_alignment(session_id, "last_update", "center")`
   - 测试 `docx_format_copy(session_id, "last_insert", "last_update")`

4. 测试多个特殊 ID 同时使用

#### 验收标准

- [ ] 所有集成测试通过
- [ ] 测试覆盖主要使用场景
- [ ] 测试验证文档状态的正确性

#### 测试要点

- 使用真实的 docx 操作
- 验证元素在文档中的位置和内容
- 测试错误场景的处理

#### 涉及文件

- `tests/integration/test_special_ids_integration.py` (新建)

---

### T-007: E2E 测试

**优先级**: P0
**复杂度**: Medium
**预计时间**: 45 分钟
**依赖**: T-002, T-003, T-004, T-005
**并行组**: 2

#### 描述

编写端到端测试，模拟真实的 Agent 使用场景。

#### 实施步骤

1. 创建 `tests/e2e/test_special_ids_workflow.py`

2. 测试场景 1: 简化的连续插入
   ```python
   # 不使用特殊 ID（旧方式）
   para_id = extract_element_id(docx_insert_paragraph(...))
   run_id = extract_element_id(docx_insert_run(..., position=f"inside:{para_id}"))
   docx_set_font(..., run_id, ...)

   # 使用特殊 ID（新方式）
   docx_insert_paragraph(...)
   docx_insert_run(..., position="inside:last_insert")
   docx_set_font(..., "last_insert", ...)
   ```

3. 测试场景 2: 使用 cursor 定位
   ```python
   docx_cursor_move(session_id, "para_123", "after")
   docx_insert_paragraph(session_id, "Text", position="after:cursor")
   ```

4. 测试场景 3: 格式复制工作流
   ```python
   docx_insert_paragraph(...)  # last_insert
   docx_update_paragraph_text(..., "para_xyz", ...)  # last_update
   docx_format_copy(..., "last_insert", "last_update")
   ```

5. 测试场景 4: 错误恢复
   ```python
   # 会话刚创建，立即使用 last_insert
   result = docx_insert_run(..., position="inside:last_insert")
   assert "SpecialIDNotAvailable" in result
   ```

#### 验收标准

- [ ] 所有 E2E 测试通过
- [ ] 测试覆盖真实使用场景
- [ ] 测试验证生成的 .docx 文件正确性

#### 测试要点

- 保存并检查生成的 .docx 文件
- 验证文档结构和内容
- 测试错误场景的用户体验

#### 涉及文件

- `tests/e2e/test_special_ids_workflow.py` (新建)

---

### T-008: 文档更新

**优先级**: P1
**复杂度**: Low
**预计时间**: 30 分钟
**依赖**: T-006, T-007
**并行组**: -

#### 描述

更新项目文档，说明特殊 ID 功能的使用方法。

#### 实施步骤

1. 更新 `README.md`:
   - 在"核心概念"部分添加"特殊位置 ID"章节
   - 添加使用示例
   - 更新快速参考部分

2. 更新 `CLAUDE.md`:
   - 在"开发指南"部分添加特殊 ID 说明
   - 更新工具使用示例
   - 添加错误处理指南

3. 更新 `CHANGELOG.md`:
   - 记录新功能
   - 列出新增的错误类型
   - 说明向后兼容性

#### 验收标准

- [ ] README.md 包含特殊 ID 使用示例
- [ ] CLAUDE.md 包含开发指南
- [ ] CHANGELOG.md 记录变更
- [ ] 文档清晰且易于理解

#### 测试要点

- 文档示例可以直接运行
- 错误处理指南准确
- 向后兼容性说明清晰

#### 涉及文件

- `README.md`
- `CLAUDE.md`
- `CHANGELOG.md`

---

## 并行执行策略

### 并行组 1（T-003, T-004, T-005）

这三个任务都依赖 T-001，但彼此独立：
- T-003: 修改工具层
- T-004: 增强响应格式
- T-005: 编写单元测试

可以由不同开发者或在不同分支上并行开发。

### 并行组 2（T-006, T-007）

这两个任务都是测试，依赖前面的实现：
- T-006: 集成测试
- T-007: E2E 测试

可以并行编写和运行。

---

## 风险与缓解

### 风险 1: 工具层修改遗漏

**描述**: 可能遗漏某些工具，导致部分工具不支持特殊 ID

**缓解**:
- 使用 grep 搜索所有接受 `element_id` 参数的函数
- 编写集成测试覆盖所有主要工具
- Code review 时检查遗漏

### 风险 2: 向后兼容性破坏

**描述**: 修改 `get_object()` 可能影响现有代码

**缓解**:
- 运行完整的现有测试套件
- 确保非特殊 ID 的行为不变
- 添加向后兼容性测试

### 风险 3: 错误消息不清晰

**描述**: 特殊 ID 错误可能让用户困惑

**缓解**:
- 提供清晰的错误消息和建议
- 在文档中说明常见错误场景
- E2E 测试验证用户体验

---

## 验收检查清单

### 功能完整性

- [ ] 所有 4 种特殊 ID 正常工作
- [ ] 所有工具支持特殊 ID
- [ ] PositionResolver 支持特殊 ID
- [ ] 错误处理完善

### 测试覆盖

- [ ] 单元测试覆盖率 > 95%
- [ ] 集成测试覆盖主要场景
- [ ] E2E 测试覆盖真实工作流
- [ ] 所有测试通过

### 文档完整性

- [ ] README.md 更新
- [ ] CLAUDE.md 更新
- [ ] CHANGELOG.md 更新
- [ ] 代码注释清晰

### 质量保证

- [ ] 代码符合项目规范
- [ ] 无 linting 错误
- [ ] 向后兼容性验证
- [ ] 性能无明显下降

---

**任务拆分者**: AI Team
**审核者**: TBD
**最后更新**: 2026-01-24
