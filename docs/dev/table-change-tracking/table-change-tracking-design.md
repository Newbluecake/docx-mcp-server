---
feature: table-change-tracking
complexity: complex
version: 1.0
created_at: 2026-01-22
---

# 技术设计文档: Table Change Tracking & History System

> **功能标识**: table-change-tracking
> **复杂度**: complex
> **设计版本**: 1.0

## 1. 系统架构设计

### 1.1 整体架构

本功能在现有 docx-mcp-server 架构基础上，增强 Session 管理和响应格式，新增历史记录系统。

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Tools Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Table Tools  │  │ History Tools│  │ Other Tools  │     │
│  │ (Enhanced)   │  │   (New)      │  │ (Enhanced)   │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Core Layer                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Session (Enhanced)                       │  │
│  │  - object_registry                                    │  │
│  │  - history_stack: List[Commit]  ← NEW                │  │
│  │  - current_commit_index: int    ← NEW                │  │
│  │  - create_commit()              ← NEW                │  │
│  │  - rollback()                   ← NEW                │  │
│  │  - checkout()                   ← NEW                │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Response Formatter (Enhanced)                 │  │
│  │  - create_success_response()                          │  │
│  │  - create_error_response()                            │  │
│  │  - create_context_aware_response()                    │  │
│  │  - create_change_tracked_response()  ← NEW            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Table Structure Analyzer (New)                │  │
│  │  - detect_irregular_structure()                       │  │
│  │  - generate_ascii_visualization()                     │  │
│  │  - get_fillable_cells()                               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                  python-docx Library                        │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 核心组件

#### 1.2.1 Commit 数据结构

```python
from dataclasses import dataclass
from typing import Dict, Any, List
from datetime import datetime

@dataclass
class Commit:
    """历史记录提交对象"""
    commit_id: str              # UUID
    timestamp: str              # ISO 8601 格式
    operation: str              # 操作类型 (如 "update_paragraph_text")
    changes: Dict[str, Any]     # 增量变更数据
    affected_elements: List[str] # 受影响元素 ID 列表

    # 可选字段
    description: str = ""       # 操作描述
    user_metadata: Dict[str, Any] = None  # 用户自定义元数据
```

**changes 字段结构**：

```python
changes = {
    "before": {
        # 修改前的状态（增量数据）
        "text": "old text",
        "cells": [{"row": 0, "col": 0, "text": ""}],
        "font": {"bold": False, "size": 12}
    },
    "after": {
        # 修改后的状态（增量数据）
        "text": "new text",
        "cells": [{"row": 0, "col": 0, "text": "Alice"}],
        "font": {"bold": True, "size": 14}
    },
    "context": {
        # 上下文信息
        "element_type": "paragraph",
        "parent_id": "document_body",
        "position": 5
    }
}
```

#### 1.2.2 Session 增强

在现有 `Session` 类中新增以下属性和方法：

```python
@dataclass
class Session:
    # ... 现有属性 ...

    # 新增属性
    history_stack: List[Commit] = field(default_factory=list)
    current_commit_index: int = -1  # 指向当前 commit 位置

    # 新增方法
    def create_commit(
        self,
        operation: str,
        changes: Dict[str, Any],
        affected_elements: List[str],
        description: str = ""
    ) -> str:
        """创建新的 commit 记录"""
        pass

    def rollback(self, commit_id: Optional[str] = None) -> Dict[str, Any]:
        """回撤到指定 commit 或上一个 commit"""
        pass

    def checkout(self, commit_id: str) -> Dict[str, Any]:
        """切换到指定 commit 状态"""
        pass

    def get_commit_log(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取历史记录"""
        pass
```

#### 1.2.3 Table Structure Analyzer

新增 `src/docx_mcp_server/core/table_analyzer.py` 模块：

```python
class TableStructureAnalyzer:
    """表格结构分析器"""

    @staticmethod
    def detect_irregular_structure(table: Table) -> Dict[str, Any]:
        """检测表格是否包含不规则结构"""
        pass

    @staticmethod
    def generate_ascii_visualization(table: Table) -> str:
        """生成 ASCII 格式的表格可视化"""
        pass

    @staticmethod
    def get_fillable_cells(table: Table) -> List[Tuple[int, int]]:
        """获取可填充的单元格坐标列表"""
        pass
```

### 1.3 数据流设计

#### 1.3.1 变更追踪流程

```
Tool Call (修改操作)
    ↓
1. 捕获修改前状态 (before)
    ↓
2. 执行修改操作
    ↓
3. 捕获修改后状态 (after)
    ↓
4. 创建 Commit 对象
    ↓
5. 添加到 history_stack
    ↓
6. 返回包含 changes 的 JSON 响应
```

#### 1.3.2 回撤流程

```
docx_rollback(session_id, commit_id)
    ↓
1. 获取目标 commit
    ↓
2. 从 current_commit_index 到 target_index 反向遍历
    ↓
3. 对每个 commit 应用反向变更
    ↓
4. 更新 current_commit_index
    ↓
5. 返回回撤详情
```

## 2. 详细设计

### 2.1 表格智能填充 (R-001)

#### 2.1.1 不规则结构检测

**检测算法**：

```python
def detect_irregular_structure(table: Table) -> Dict[str, Any]:
    """
    检测表格是否包含不规则结构

    Returns:
        {
            "is_irregular": bool,
            "has_merged_cells": bool,
            "has_nested_tables": bool,
            "row_col_inconsistent": bool,
            "irregular_regions": [
                {"type": "merged", "row": 0, "col": 0, "rowspan": 2, "colspan": 1},
                {"type": "nested", "row": 1, "col": 2}
            ]
        }
    """
    result = {
        "is_irregular": False,
        "has_merged_cells": False,
        "has_nested_tables": False,
        "row_col_inconsistent": False,
        "irregular_regions": []
    }

    # 1. 检查合并单元格
    for row_idx, row in enumerate(table.rows):
        for col_idx, cell in enumerate(row.cells):
            # 检查 grid_span (列跨度)
            grid_span = cell._element.tcPr.gridSpan.val if (
                cell._element.tcPr is not None and
                cell._element.tcPr.gridSpan is not None
            ) else 1

            # 检查 vMerge (行跨度)
            v_merge = cell._element.tcPr.vMerge if (
                cell._element.tcPr is not None
            ) else None

            if grid_span > 1 or v_merge is not None:
                result["has_merged_cells"] = True
                result["is_irregular"] = True
                result["irregular_regions"].append({
                    "type": "merged",
                    "row": row_idx,
                    "col": col_idx,
                    "colspan": grid_span,
                    "rowspan": "unknown"  # 需要额外计算
                })

    # 2. 检查嵌套表格
    for row_idx, row in enumerate(table.rows):
        for col_idx, cell in enumerate(row.cells):
            if len(cell.tables) > 0:
                result["has_nested_tables"] = True
                result["is_irregular"] = True
                result["irregular_regions"].append({
                    "type": "nested",
                    "row": row_idx,
                    "col": col_idx
                })

    # 3. 检查行列一致性
    col_counts = [len(row.cells) for row in table.rows]
    if len(set(col_counts)) > 1:
        result["row_col_inconsistent"] = True
        result["is_irregular"] = True

    return result
```

#### 2.1.2 智能填充策略

**填充算法**：

```python
def smart_fill_table(
    session_id: str,
    table_id: str,
    data: str,  # JSON array
    has_header: bool = True,
    auto_resize: bool = True
) -> str:
    """智能填充表格，遇到不规则区域时跳过"""

    # 1. 检测表格结构
    structure_info = detect_irregular_structure(table)

    # 2. 获取可填充单元格列表
    fillable_cells = get_fillable_cells(table, structure_info)

    # 3. 解析数据
    data_rows = json.loads(data)

    # 4. 填充数据
    filled_range = {"start_row": 0, "start_col": 0, "end_row": 0, "end_col": 0}
    skipped_regions = []

    start_row = 1 if has_header else 0

    for data_row_idx, data_row in enumerate(data_rows):
        table_row_idx = start_row + data_row_idx

        # 自动扩展行
        if auto_resize and table_row_idx >= len(table.rows):
            table.add_row()

        for col_idx, value in enumerate(data_row):
            if (table_row_idx, col_idx) in fillable_cells:
                # 填充单元格
                cell = table.rows[table_row_idx].cells[col_idx]
                cell.text = str(value)
                filled_range["end_row"] = table_row_idx
                filled_range["end_col"] = col_idx
            else:
                # 跳过不规则单元格
                skipped_regions.append({
                    "row": table_row_idx,
                    "col": col_idx,
                    "reason": "irregular_cell"
                })

    return create_change_tracked_response(
        session,
        message="Table filled successfully",
        element_id=table_id,
        filled_range=filled_range,
        skipped_regions=skipped_regions
    )
```

### 2.2 表格结构可视化 (R-002)

#### 2.2.1 ASCII 可视化生成

**生成算法**：

```python
def generate_ascii_visualization(table: Table) -> str:
    """生成 ASCII 格式的表格可视化"""

    rows_count = len(table.rows)
    cols_count = len(table.columns) if table.rows else 0

    # 检测不规则结构
    structure_info = detect_irregular_structure(table)

    lines = []
    lines.append(f"Table: {rows_count} rows x {cols_count} cols "
                 f"(has merged cells: {'yes' if structure_info['has_merged_cells'] else 'no'})")
    lines.append("")

    # 计算每列的最大宽度
    col_widths = [20] * cols_count  # 默认宽度 20

    # 生成表格行
    for row_idx, row in enumerate(table.rows):
        # 顶部边框
        border = "+" + "+".join(["-" * (w + 2) for w in col_widths]) + "+"
        lines.append(border)

        # 单元格内容
        cell_texts = []
        for col_idx, cell in enumerate(row.cells):
            text = cell.text.replace('\n', ' ')
            if len(text) > 20:
                text = text[:17] + "..."
            if not text:
                text = "[empty]"

            # 检查是否为合并单元格
            # (简化处理，实际需要更复杂的逻辑)
            cell_texts.append(f" {text:<{col_widths[col_idx]}} ")

        lines.append("|" + "|".join(cell_texts) + "|")

    # 底部边框
    border = "+" + "+".join(["-" * (w + 2) for w in col_widths]) + "+"
    lines.append(border)

    return "\n".join(lines)
```

#### 2.2.2 新增工具

```python
def docx_get_table_structure(session_id: str, table_id: str) -> str:
    """
    获取表格结构的 ASCII 可视化

    Args:
        session_id: 会话 ID
        table_id: 表格 ID

    Returns:
        JSON 响应，包含 ASCII 可视化和元数据
    """
    session = session_manager.get_session(session_id)
    if not session:
        return create_error_response(
            f"Session {session_id} not found",
            error_type="SessionNotFound"
        )

    table = session.get_object(table_id)
    if not table or not isinstance(table, Table):
        return create_error_response(
            f"Table {table_id} not found",
            error_type="ElementNotFound"
        )

    # 生成可视化
    ascii_viz = generate_ascii_visualization(table)
    structure_info = detect_irregular_structure(table)

    return create_success_response(
        message="Table structure retrieved successfully",
        element_id=table_id,
        ascii_visualization=ascii_viz,
        structure_info=structure_info,
        rows=len(table.rows),
        cols=len(table.columns) if table.rows else 0
    )
```

### 2.3 变更追踪与对比 (R-003)

#### 2.3.1 变更捕获机制

**通用变更捕获装饰器**：

```python
def track_changes(operation_name: str):
    """装饰器：自动追踪变更"""
    def decorator(func):
        def wrapper(session_id: str, *args, **kwargs):
            session = session_manager.get_session(session_id)
            if not session:
                return create_error_response(...)

            # 1. 捕获修改前状态
            before_state = capture_state(session, *args, **kwargs)

            # 2. 执行修改操作
            result = func(session_id, *args, **kwargs)

            # 3. 捕获修改后状态
            after_state = capture_state(session, *args, **kwargs)

            # 4. 创建 commit
            changes = {
                "before": before_state,
                "after": after_state,
                "context": get_context_info(session, *args)
            }
            commit_id = session.create_commit(
                operation=operation_name,
                changes=changes,
                affected_elements=extract_affected_elements(*args)
            )

            # 5. 在响应中包含变更信息
            return enhance_response_with_changes(result, changes, commit_id)

        return wrapper
    return decorator
```

#### 2.3.2 状态捕获策略

**针对不同元素类型的状态捕获**：

```python
def capture_state(session: Session, element_id: str, **kwargs) -> Dict[str, Any]:
    """捕获元素当前状态"""
    element = session.get_object(element_id)
    if not element:
        return {}

    if isinstance(element, Paragraph):
        return {
            "text": element.text,
            "style": element.style.name if element.style else None,
            "alignment": str(element.alignment) if element.alignment else None
        }
    elif isinstance(element, Run):
        return {
            "text": element.text,
            "bold": element.bold,
            "italic": element.italic,
            "font_size": element.font.size.pt if element.font.size else None
        }
    elif isinstance(element, Table):
        return {
            "rows": len(element.rows),
            "cols": len(element.columns) if element.rows else 0,
            "cells": capture_table_cells(element)
        }
    else:
        return {"type": type(element).__name__}
```

### 2.4 历史记录系统 (R-004)

#### 2.4.1 Commit 创建

```python
def create_commit(
    self,
    operation: str,
    changes: Dict[str, Any],
    affected_elements: List[str],
    description: str = ""
) -> str:
    """创建新的 commit 记录"""
    import uuid
    from datetime import datetime

    commit_id = str(uuid.uuid4())
    commit = Commit(
        commit_id=commit_id,
        timestamp=datetime.utcnow().isoformat() + "Z",
        operation=operation,
        changes=changes,
        affected_elements=affected_elements,
        description=description
    )

    # 如果当前不在最新位置，删除后续历史
    if self.current_commit_index < len(self.history_stack) - 1:
        self.history_stack = self.history_stack[:self.current_commit_index + 1]

    self.history_stack.append(commit)
    self.current_commit_index = len(self.history_stack) - 1

    logger.info(f"Commit created: {commit_id} ({operation})")
    return commit_id
```

#### 2.4.2 历史记录查询

```python
def docx_log(session_id: str, limit: int = 10) -> str:
    """获取历史记录"""
    session = session_manager.get_session(session_id)
    if not session:
        return create_error_response(...)

    # 获取最近 N 条记录
    commits = session.history_stack[-limit:]
    commits.reverse()  # 最新的在前

    log_entries = []
    for commit in commits:
        log_entries.append({
            "commit_id": commit.commit_id,
            "timestamp": commit.timestamp,
            "operation": commit.operation,
            "affected_elements": commit.affected_elements,
            "description": commit.description
        })

    return create_success_response(
        message=f"Retrieved {len(log_entries)} commit(s)",
        commits=log_entries,
        total_commits=len(session.history_stack)
    )
```

### 2.5 回撤与恢复 (R-005)

#### 2.5.1 Rollback 实现

```python
def rollback(self, commit_id: Optional[str] = None) -> Dict[str, Any]:
    """回撤到指定 commit 或上一个 commit"""
    if not self.history_stack:
        raise ValueError("No commits to rollback")

    # 确定目标索引
    if commit_id is None:
        # 回撤到上一个 commit
        target_index = self.current_commit_index - 1
    else:
        # 查找指定 commit
        target_index = None
        for i, commit in enumerate(self.history_stack):
            if commit.commit_id == commit_id:
                target_index = i
                break
        if target_index is None:
            raise ValueError(f"Commit {commit_id} not found")

    if target_index < -1:
        raise ValueError("Cannot rollback beyond initial state")

    # 反向应用变更
    rollback_info = {
        "rolled_back_commits": [],
        "restored_elements": []
    }

    for i in range(self.current_commit_index, target_index, -1):
        commit = self.history_stack[i]
        self._apply_reverse_changes(commit)
        rollback_info["rolled_back_commits"].append(commit.commit_id)
        rollback_info["restored_elements"].extend(commit.affected_elements)

    self.current_commit_index = target_index
    return rollback_info
```

#### 2.5.2 反向变更应用

```python
def _apply_reverse_changes(self, commit: Commit):
    """应用反向变更"""
    changes = commit.changes
    before_state = changes.get("before", {})

    for element_id in commit.affected_elements:
        element = self.get_object(element_id)
        if not element:
            logger.warning(f"Element {element_id} not found, skipping")
            continue

        # 根据元素类型恢复状态
        if isinstance(element, Paragraph):
            if "text" in before_state:
                element.text = before_state["text"]
        elif isinstance(element, Run):
            if "text" in before_state:
                element.text = before_state["text"]
            if "bold" in before_state:
                element.bold = before_state["bold"]
        elif isinstance(element, Table):
            if "cells" in before_state:
                self._restore_table_cells(element, before_state["cells"])
```

## 3. 接口设计

### 3.1 新增工具

#### 3.1.1 docx_get_table_structure

```python
def docx_get_table_structure(session_id: str, table_id: str) -> str:
    """
    获取表格结构的 ASCII 可视化

    Args:
        session_id: 会话 ID
        table_id: 表格 ID

    Returns:
        JSON 响应，包含 ASCII 可视化和元数据
    """
```

#### 3.1.2 docx_log

```python
def docx_log(session_id: str, limit: int = 10) -> str:
    """
    获取历史记录

    Args:
        session_id: 会话 ID
        limit: 返回的最大记录数，默认 10

    Returns:
        JSON 响应，包含 commit 列表
    """
```

#### 3.1.3 docx_rollback

```python
def docx_rollback(session_id: str, commit_id: Optional[str] = None) -> str:
    """
    回撤到指定 commit 或上一个 commit

    Args:
        session_id: 会话 ID
        commit_id: 目标 commit ID，None 表示回撤到上一个

    Returns:
        JSON 响应，包含回撤详情
    """
```

#### 3.1.4 docx_checkout

```python
def docx_checkout(session_id: str, commit_id: str) -> str:
    """
    切换到指定 commit 状态

    Args:
        session_id: 会话 ID
        commit_id: 目标 commit ID

    Returns:
        JSON 响应，包含 checkout 详情
    """
```

### 3.2 增强现有工具

所有修改类工具需要集成变更追踪，在响应中包含 `changes` 字段：

- `docx_update_paragraph_text`
- `docx_update_run_text`
- `docx_set_font`
- `docx_fill_table`
- `docx_smart_fill_table`
- `docx_replace_text`
- `docx_batch_replace_text`
- `docx_set_alignment`
- `docx_set_properties`

**响应格式示例**：

```json
{
  "status": "success",
  "message": "Paragraph text updated successfully",
  "data": {
    "element_id": "para_abc123",
    "changes": {
      "before": {"text": "old text"},
      "after": {"text": "new text"},
      "context": {"parent_id": "document_body", "position": 5}
    },
    "commit_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

## 4. 实施计划

### 4.1 模块依赖关系

```
Phase 1: 核心基础设施
  ├── Commit 数据结构 (src/docx_mcp_server/core/commit.py)
  ├── Session 增强 (src/docx_mcp_server/core/session.py)
  └── Response 增强 (src/docx_mcp_server/core/response.py)

Phase 2: 表格分析
  ├── TableStructureAnalyzer (src/docx_mcp_server/core/table_analyzer.py)
  └── docx_get_table_structure (src/docx_mcp_server/tools/table_tools.py)

Phase 3: 智能填充
  ├── 增强 docx_fill_table
  └── 增强 docx_smart_fill_table

Phase 4: 历史记录工具
  ├── docx_log
  ├── docx_rollback
  └── docx_checkout

Phase 5: 变更追踪集成
  ├── 集成到 paragraph_tools
  ├── 集成到 run_tools
  ├── 集成到 format_tools
  └── 集成到 advanced_tools
```

### 4.2 测试策略

#### 4.2.1 单元测试

- `test_commit.py` - Commit 数据结构测试
- `test_session_history.py` - Session 历史记录功能测试
- `test_table_analyzer.py` - 表格分析器测试
- `test_change_tracking.py` - 变更追踪测试

#### 4.2.2 集成测试

- `test_smart_fill_irregular_table.py` - 不规则表格填充测试
- `test_rollback_workflow.py` - 回撤工作流测试
- `test_change_tracking_integration.py` - 变更追踪集成测试

### 4.3 性能考虑

#### 4.3.1 内存优化

- 使用增量存储，只保存变更的部分
- 避免保存完整文档快照
- 对于大型表格，只保存修改的单元格

#### 4.3.2 时间复杂度

- Commit 创建: O(1)
- 历史查询: O(n)，n 为 limit
- Rollback: O(m)，m 为回撤的 commit 数量

## 5. 风险与挑战

### 5.1 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 合并单元格检测不准确 | 填充错误 | 充分测试各种合并场景 |
| 反向变更应用失败 | 回撤失败 | 添加错误处理和日志 |
| 内存占用过大 | 性能下降 | 限制历史记录数量（可选） |
| 状态捕获不完整 | 回撤不准确 | 完善状态捕获逻辑 |

### 5.2 兼容性风险

- 需要确保与现有工具的兼容性
- 响应格式变更可能影响现有客户端
- 建议采用渐进式集成策略

## 6. 文档更新

需要更新以下文档：

- `README.md` - 添加新工具说明
- `CLAUDE.md` - 更新架构说明和工具列表
- API 文档 - 添加新工具的详细说明

---

**设计完成日期**: 2026-01-22
**设计者**: AI Team
**审核状态**: 待审核


