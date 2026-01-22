---
feature: table-change-tracking
complexity: complex
version: 1.0
created_at: 2026-01-22
---

# 任务拆分文档: Table Change Tracking & History System

> **功能标识**: table-change-tracking
> **复杂度**: complex
> **任务版本**: 1.0

## 任务概览

本功能共拆分为 **12 个任务**，分为 **5 个并行组**。

### 任务统计

- **P0 任务**: 12 个
- **预计总工时**: 16-20 小时
- **并行组数**: 5 组

### 依赖关系图

```
Group 1 (基础设施)
  ├── T-001: Commit 数据结构
  ├── T-002: Session 历史记录增强
  └── T-003: Response 格式增强
      ↓
Group 2 (表格分析)
  ├── T-004: TableStructureAnalyzer 实现
  └── T-005: docx_get_table_structure 工具
      ↓
Group 3 (智能填充)
  ├── T-006: 增强 docx_fill_table
  └── T-007: 增强 docx_smart_fill_table
      ↓
Group 4 (历史记录工具)
  ├── T-008: docx_log 工具
  ├── T-009: docx_rollback 工具
  └── T-010: docx_checkout 工具
      ↓
Group 5 (变更追踪集成)
  ├── T-011: 集成变更追踪到修改类工具
  └── T-012: 测试与文档更新
```

---

## Group 1: 核心基础设施 (并行执行)

### T-001: 实现 Commit 数据结构

**优先级**: P0
**预计工时**: 1 小时
**依赖**: 无
**可并行**: 是

**描述**:
创建 `src/docx_mcp_server/core/commit.py` 模块，实现 Commit 数据类。

**实施步骤**:
1. 创建 `commit.py` 文件
2. 定义 `Commit` dataclass，包含以下字段：
   - `commit_id: str` (UUID)
   - `timestamp: str` (ISO 8601)
   - `operation: str`
   - `changes: Dict[str, Any]`
   - `affected_elements: List[str]`
   - `description: str = ""`
   - `user_metadata: Dict[str, Any] = None`
3. 添加 `to_dict()` 方法用于序列化
4. 添加 `from_dict()` 类方法用于反序列化

**验收标准**:
- [ ] Commit 类定义完整
- [ ] 包含所有必需字段
- [ ] 支持序列化和反序列化
- [ ] 通过单元测试 `test_commit.py`

**测试用例**:
```python
def test_commit_creation():
    commit = Commit(
        commit_id="test-id",
        timestamp="2026-01-22T10:00:00Z",
        operation="update_paragraph_text",
        changes={"before": {"text": "old"}, "after": {"text": "new"}},
        affected_elements=["para_123"]
    )
    assert commit.commit_id == "test-id"
    assert commit.operation == "update_paragraph_text"
```

---

### T-002: Session 历史记录增强

**优先级**: P0
**预计工时**: 2 小时
**依赖**: T-001
**可并行**: 否

**描述**:
在 `src/docx_mcp_server/core/session.py` 中增强 Session 类，添加历史记录功能。

**实施步骤**:
1. 在 Session 类中添加新属性：
   - `history_stack: List[Commit] = field(default_factory=list)`
   - `current_commit_index: int = -1`
2. 实现 `create_commit()` 方法
3. 实现 `rollback()` 方法
4. 实现 `checkout()` 方法
5. 实现 `get_commit_log()` 方法
6. 实现 `_apply_reverse_changes()` 私有方法

**验收标准**:
- [ ] Session 类包含历史记录属性
- [ ] `create_commit()` 正确创建并添加 commit
- [ ] `rollback()` 能回撤到指定版本
- [ ] `checkout()` 能切换到指定版本
- [ ] 通过单元测试 `test_session_history.py`

**测试用例**:
```python
def test_create_commit():
    session = Session(session_id="test", document=Document())
    commit_id = session.create_commit(
        operation="test_op",
        changes={"before": {}, "after": {}},
        affected_elements=["elem_1"]
    )
    assert len(session.history_stack) == 1
    assert session.current_commit_index == 0
```

---

### T-003: Response 格式增强

**优先级**: P0
**预计工时**: 1 小时
**依赖**: 无
**可并行**: 是

**描述**:
在 `src/docx_mcp_server/core/response.py` 中添加变更追踪响应支持。

**实施步骤**:
1. 添加 `create_change_tracked_response()` 函数
2. 扩展 `create_success_response()` 支持 `changes` 和 `commit_id` 参数
3. 添加辅助函数 `enhance_response_with_changes()`

**验收标准**:
- [ ] 新增 `create_change_tracked_response()` 函数
- [ ] 响应格式包含 `changes` 和 `commit_id` 字段
- [ ] 向后兼容现有响应格式
- [ ] 通过单元测试

**测试用例**:
```python
def test_change_tracked_response():
    response = create_change_tracked_response(
        session=mock_session,
        message="Updated successfully",
        element_id="para_123",
        changes={"before": {"text": "old"}, "after": {"text": "new"}},
        commit_id="commit-123"
    )
    data = json.loads(response)
    assert data["status"] == "success"
    assert "changes" in data["data"]
    assert "commit_id" in data["data"]
```

---

## Group 2: 表格分析 (并行执行)

### T-004: 实现 TableStructureAnalyzer

**优先级**: P0
**预计工时**: 3 小时
**依赖**: 无
**可并行**: 是

**描述**:
创建 `src/docx_mcp_server/core/table_analyzer.py` 模块，实现表格结构分析功能。

**实施步骤**:
1. 创建 `table_analyzer.py` 文件
2. 实现 `detect_irregular_structure()` 方法：
   - 检测合并单元格
   - 检测嵌套表格
   - 检测行列不一致
3. 实现 `generate_ascii_visualization()` 方法：
   - 生成 ASCII 表格边框
   - 填充单元格内容（截断长文本）
   - 标注合并单元格
   - 标注空单元格
4. 实现 `get_fillable_cells()` 方法：
   - 返回可填充的单元格坐标列表

**验收标准**:
- [ ] 正确检测合并单元格
- [ ] 正确检测嵌套表格
- [ ] ASCII 可视化格式正确
- [ ] 长文本正确截断为 20 字符
- [ ] 通过单元测试 `test_table_analyzer.py`

**测试用例**:
```python
def test_detect_merged_cells():
    # 创建包含合并单元格的表格
    doc = Document()
    table = doc.add_table(rows=2, cols=2)
    # 合并第一行的两个单元格
    cell_a = table.rows[0].cells[0]
    cell_b = table.rows[0].cells[1]
    cell_a.merge(cell_b)

    result = detect_irregular_structure(table)
    assert result["has_merged_cells"] == True
    assert result["is_irregular"] == True
```

---

### T-005: 实现 docx_get_table_structure 工具

**优先级**: P0
**预计工时**: 1 小时
**依赖**: T-004
**可并行**: 否

**描述**:
在 `src/docx_mcp_server/tools/table_tools.py` 中添加 `docx_get_table_structure` 工具。

**实施步骤**:
1. 在 `table_tools.py` 中添加 `docx_get_table_structure()` 函数
2. 调用 `TableStructureAnalyzer` 生成可视化
3. 返回标准化 JSON 响应
4. 在 `__init__.py` 中注册工具

**验收标准**:
- [ ] 工具正确调用 TableStructureAnalyzer
- [ ] 返回 ASCII 可视化和元数据
- [ ] 响应格式符合标准
- [ ] 通过集成测试

**测试用例**:
```python
def test_get_table_structure():
    session_id = docx_create()
    table_id = docx_insert_table(session_id, rows=3, cols=3, position="end:document_body")

    result = docx_get_table_structure(session_id, table_id)
    data = json.loads(result)

    assert data["status"] == "success"
    assert "ascii_visualization" in data["data"]
    assert "structure_info" in data["data"]
```

---

## Group 3: 智能填充 (并行执行)

### T-006: 增强 docx_fill_table

**优先级**: P0
**预计工时**: 2 小时
**依赖**: T-004
**可并行**: 是

**描述**:
增强 `docx_fill_table` 工具，添加不规则表格检测和智能跳过功能。

**实施步骤**:
1. 在填充前调用 `detect_irregular_structure()`
2. 获取可填充单元格列表
3. 填充时跳过不规则单元格
4. 记录跳过的区域
5. 返回填充范围和跳过区域信息

**验收标准**:
- [ ] 正确检测不规则表格
- [ ] 只填充规则单元格
- [ ] 返回 `filled_range` 和 `skipped_regions`
- [ ] 不会因不规则结构而崩溃
- [ ] 通过测试 `test_fill_irregular_table.py`

---

### T-007: 增强 docx_smart_fill_table

**优先级**: P0
**预计工时**: 2 小时
**依赖**: T-004, T-006
**可并行**: 否

**描述**:
增强 `docx_smart_fill_table` 工具，添加智能填充和自动扩展功能。

**实施步骤**:
1. 集成 T-006 的不规则检测逻辑
2. 实现自动扩展行功能
3. 支持通过表格 ID 或文本查找表格
4. 返回详细的填充报告

**验收标准**:
- [ ] 支持 `auto_resize` 参数
- [ ] 自动扩展行数以容纳数据
- [ ] 正确处理 `has_header` 参数
- [ ] 返回完整的填充报告
- [ ] 通过测试 `test_smart_fill_table.py`

---

## Group 4: 历史记录工具 (并行执行)

### T-008: 实现 docx_log 工具

**优先级**: P0
**预计工时**: 1 小时
**依赖**: T-002
**可并行**: 是

**描述**:
创建 `src/docx_mcp_server/tools/history_tools.py` 模块，实现 `docx_log` 工具。

**实施步骤**:
1. 创建 `history_tools.py` 文件
2. 实现 `docx_log()` 函数
3. 调用 `session.get_commit_log()`
4. 格式化并返回历史记录
5. 在 `__init__.py` 中注册工具

**验收标准**:
- [ ] 正确返回最近 N 条记录
- [ ] 按时间倒序排列
- [ ] 包含 commit_id、timestamp、operation 等信息
- [ ] 通过测试

---

### T-009: 实现 docx_rollback 工具

**优先级**: P0
**预计工时**: 1.5 小时
**依赖**: T-002
**可并行**: 是

**描述**:
在 `history_tools.py` 中实现 `docx_rollback` 工具。

**实施步骤**:
1. 实现 `docx_rollback()` 函数
2. 支持无参数回撤（回到上一个 commit）
3. 支持指定 commit_id 回撤
4. 调用 `session.rollback()`
5. 返回回撤详情

**验收标准**:
- [ ] 支持单步回撤
- [ ] 支持指定版本回撤
- [ ] 正确应用反向变更
- [ ] 返回详细的回撤信息
- [ ] 通过测试 `test_rollback.py`

---

### T-010: 实现 docx_checkout 工具

**优先级**: P0
**预计工时**: 1.5 小时
**依赖**: T-002
**可并行**: 是

**描述**:
在 `history_tools.py` 中实现 `docx_checkout` 工具。

**实施步骤**:
1. 实现 `docx_checkout()` 函数
2. 调用 `session.checkout()`
3. 保留后续历史记录
4. 返回 checkout 详情

**验收标准**:
- [ ] 正确切换到指定 commit
- [ ] 保留后续历史记录
- [ ] 返回详细的 checkout 信息
- [ ] 通过测试

---

## Group 5: 变更追踪集成 (串行执行)

### T-011: 集成变更追踪到修改类工具

**优先级**: P0
**预计工时**: 3 小时
**依赖**: T-002, T-003
**可并行**: 否

**描述**:
将变更追踪功能集成到所有修改类工具中。

**实施步骤**:
1. 在以下工具中集成变更追踪：
   - `docx_update_paragraph_text` (paragraph_tools.py)
   - `docx_update_run_text` (run_tools.py)
   - `docx_set_font` (run_tools.py)
   - `docx_set_alignment` (format_tools.py)
   - `docx_set_properties` (format_tools.py)
   - `docx_replace_text` (advanced_tools.py)
   - `docx_batch_replace_text` (advanced_tools.py)
2. 在每个工具中：
   - 捕获修改前状态
   - 执行修改
   - 捕获修改后状态
   - 调用 `session.create_commit()`
   - 在响应中包含 `changes` 和 `commit_id`

**验收标准**:
- [ ] 所有修改类工具都集成了变更追踪
- [ ] 响应包含完整的变更信息
- [ ] 不影响现有功能
- [ ] 通过集成测试 `test_change_tracking_integration.py`

---

### T-012: 测试与文档更新

**优先级**: P0
**预计工时**: 2 小时
**依赖**: T-001 到 T-011
**可并行**: 否

**描述**:
完成所有测试并更新相关文档。

**实施步骤**:
1. 编写并运行所有单元测试
2. 编写并运行所有集成测试
3. 更新 `README.md`：
   - 添加新工具说明
   - 更新工具列表
4. 更新 `CLAUDE.md`：
   - 更新架构说明
   - 添加变更追踪使用指南
5. 创建示例代码和使用场景

**验收标准**:
- [ ] 所有测试通过
- [ ] 测试覆盖率 >= 80%
- [ ] README.md 已更新
- [ ] CLAUDE.md 已更新
- [ ] 包含使用示例

---

## 任务执行顺序

### 阶段 1: 基础设施 (Day 1)
- T-001, T-002, T-003 (并行) → 4 小时

### 阶段 2: 表格分析 (Day 1-2)
- T-004 (3 小时)
- T-005 (1 小时)

### 阶段 3: 智能填充 (Day 2)
- T-006 (2 小时)
- T-007 (2 小时)

### 阶段 4: 历史记录 (Day 2-3)
- T-008, T-009, T-010 (并行) → 4 小时

### 阶段 5: 集成与测试 (Day 3)
- T-011 (3 小时)
- T-012 (2 小时)

**总计**: 约 21 小时 (3 个工作日)

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 合并单元格检测复杂 | 延期 | 优先实现基本场景，复杂场景后续迭代 |
| 反向变更应用失败 | 功能缺陷 | 充分测试，添加错误处理 |
| 集成影响现有功能 | 回归 | 完整的回归测试 |

---

**文档完成日期**: 2026-01-22
**拆分者**: AI Team
**审核状态**: 待审核


