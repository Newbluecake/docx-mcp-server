---
feature: element-id-enhancement
version: 1
created_at: 2026-01-23
status: draft
---

# 任务拆分文档: Element ID Enhancement

> **功能标识**: element-id-enhancement
> **复杂度**: complex
> **任务版本**: v1
> **拆分日期**: 2026-01-23

## 任务概览

| 统计项 | 数量 |
|--------|------|
| 总任务数 | 12 |
| P0 任务 | 8 |
| P1 任务 | 2 |
| P2 任务 | 2 |
| 并行组数 | 3 |

## 任务依赖关系图

```
T-001 (基础设施)
  ↓
┌─────────────────────────────────────┐
│ T-002, T-003, T-004 (核心解析器)    │ ← 并行组 1
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ T-005, T-006, T-007, T-008 (工具层) │ ← 并行组 2
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ T-009, T-010 (测试)                 │ ← 并行组 3
└─────────────────────────────────────┘
  ↓
T-011 (性能测试)
  ↓
T-012 (文档更新)
```

---

## 任务详情

### T-001: 增强 Session._get_element_id() 方法

**优先级**: P0
**复杂度**: Simple
**预计工时**: 1 小时
**依赖**: 无
**并行组**: 独立

#### 任务描述

增强 `Session._get_element_id()` 方法，确保缓存机制正确工作，并添加详细日志。

#### 验收标准

- [ ] `_get_element_id()` 方法支持 `auto_register=True` 参数
- [ ] 缓存命中时直接返回，不重复注册
- [ ] 缓存未命中时自动注册并更新缓存
- [ ] 添加 DEBUG 级别日志记录缓存命中/未命中
- [ ] 单元测试覆盖缓存逻辑

#### 实现要点

1. 检查现有 `_get_element_id()` 实现（已存在于 `session.py`）
2. 确认缓存逻辑正确：
   - 使用 `id(element._element)` 作为缓存键
   - 缓存命中时直接返回
   - 缓存未命中且 `auto_register=True` 时注册
3. 添加日志：
   ```python
   logger.debug(f"Element ID cache hit: {element_id}")
   logger.debug(f"Element ID cache miss, registering: {element_id}")
   ```

#### 测试用例

```python
def test_get_element_id_cache():
    session_id = docx_create()
    session = session_manager.get_session(session_id)

    para = session.document.add_paragraph("Test")

    # 第一次调用，缓存未命中
    id1 = session._get_element_id(para, auto_register=True)
    assert id1.startswith("para_")

    # 第二次调用，缓存命中
    id2 = session._get_element_id(para, auto_register=True)
    assert id1 == id2  # 应该返回相同 ID
```

#### 涉及文件

- `src/docx_mcp_server/core/session.py`
- `tests/unit/test_session.py`

---

### T-002: 修改 TemplateParser.extract_heading_structure()

**优先级**: P0
**复杂度**: Standard
**预计工时**: 2 小时
**依赖**: T-001
**并行组**: 1

#### 任务描述

为 `extract_heading_structure()` 方法添加 `session` 参数，并在返回值中添加 `element_id` 字段。

#### 验收标准

- [ ] 方法签名添加 `session: Optional[Session] = None` 参数
- [ ] 当 `session` 不为 `None` 时，调用 `session._get_element_id(paragraph, auto_register=True)`
- [ ] 返回的字典包含 `element_id` 字段
- [ ] 当 `session` 为 `None` 时，不添加 `element_id` 字段（向后兼容）
- [ ] 单元测试覆盖两种情况

#### 实现要点

```python
def extract_heading_structure(
    self,
    paragraph: Paragraph,
    session: Optional[Session] = None
) -> Dict[str, Any]:
    # 现有逻辑...
    result = {
        "type": "heading",
        "level": level,
        "text": text,
        "style": style
    }

    # 新增逻辑
    if session is not None:
        try:
            element_id = session._get_element_id(paragraph, auto_register=True)
            if element_id:
                result["element_id"] = element_id
        except Exception as e:
            logger.warning(f"Failed to generate element_id for heading: {e}")

    return result
```

#### 测试用例

```python
def test_extract_heading_structure_with_session():
    session_id = docx_create()
    session = session_manager.get_session(session_id)

    para = session.document.add_heading("Test Heading", level=1)
    parser = TemplateParser()

    result = parser.extract_heading_structure(para, session=session)

    assert "element_id" in result
    assert result["element_id"].startswith("para_")
    assert result["type"] == "heading"
    assert result["level"] == 1

def test_extract_heading_structure_without_session():
    doc = Document()
    para = doc.add_heading("Test Heading", level=1)
    parser = TemplateParser()

    result = parser.extract_heading_structure(para, session=None)

    assert "element_id" not in result  # 向后兼容
    assert result["type"] == "heading"
```

#### 涉及文件

- `src/docx_mcp_server/core/template_parser.py`
- `tests/unit/test_template_parser.py`

---

### T-003: 修改 TemplateParser.extract_paragraph_structure()

**优先级**: P0
**复杂度**: Standard
**预计工时**: 2 小时
**依赖**: T-001
**并行组**: 1

#### 任务描述

为 `extract_paragraph_structure()` 方法添加 `session` 参数，并在返回值中添加 `element_id` 字段。

#### 验收标准

- [ ] 方法签名添加 `session: Optional[Session] = None` 参数
- [ ] 当 `session` 不为 `None` 时，调用 `session._get_element_id(paragraph, auto_register=True)`
- [ ] 返回的字典包含 `element_id` 字段
- [ ] 当 `session` 为 `None` 时，不添加 `element_id` 字段（向后兼容）
- [ ] 单元测试覆盖两种情况

#### 实现要点

```python
def extract_paragraph_structure(
    self,
    paragraph: Paragraph,
    session: Optional[Session] = None
) -> Dict[str, Any]:
    # 现有逻辑...
    result = {
        "type": "paragraph",
        "text": text,
        "style": style
    }

    # 新增逻辑
    if session is not None:
        try:
            element_id = session._get_element_id(paragraph, auto_register=True)
            if element_id:
                result["element_id"] = element_id
        except Exception as e:
            logger.warning(f"Failed to generate element_id for paragraph: {e}")

    return result
```

#### 测试用例

```python
def test_extract_paragraph_structure_with_session():
    session_id = docx_create()
    session = session_manager.get_session(session_id)

    para = session.document.add_paragraph("Test paragraph")
    parser = TemplateParser()

    result = parser.extract_paragraph_structure(para, session=session)

    assert "element_id" in result
    assert result["element_id"].startswith("para_")
    assert result["type"] == "paragraph"

def test_extract_paragraph_structure_without_session():
    doc = Document()
    para = doc.add_paragraph("Test paragraph")
    parser = TemplateParser()

    result = parser.extract_paragraph_structure(para, session=None)

    assert "element_id" not in result  # 向后兼容
    assert result["type"] == "paragraph"
```

#### 涉及文件

- `src/docx_mcp_server/core/template_parser.py`
- `tests/unit/test_template_parser.py`

---

### T-004: 修改 TemplateParser.extract_table_structure()

**优先级**: P0
**复杂度**: Standard
**预计工时**: 2 小时
**依赖**: T-001
**并行组**: 1

#### 任务描述

为 `extract_table_structure()` 方法添加 `session` 参数，并在返回值中添加 `element_id` 字段。

#### 验收标准

- [ ] 方法签名添加 `session: Optional[Session] = None` 参数
- [ ] 当 `session` 不为 `None` 时，调用 `session._get_element_id(table, auto_register=True)`
- [ ] 返回的字典包含 `element_id` 字段
- [ ] 当 `session` 为 `None` 时，不添加 `element_id` 字段（向后兼容）
- [ ] 单元测试覆盖两种情况

#### 实现要点

```python
def extract_table_structure(
    self,
    table: Table,
    session: Optional[Session] = None
) -> Dict[str, Any]:
    # 现有逻辑...
    result = {
        "type": "table",
        "rows": rows,
        "cols": cols,
        "header_row": header_row,
        "headers": headers,
        "style": style
    }

    # 新增逻辑
    if session is not None:
        try:
            element_id = session._get_element_id(table, auto_register=True)
            if element_id:
                result["element_id"] = element_id
        except Exception as e:
            logger.warning(f"Failed to generate element_id for table: {e}")

    return result
```

#### 测试用例

```python
def test_extract_table_structure_with_session():
    session_id = docx_create()
    session = session_manager.get_session(session_id)

    table = session.document.add_table(rows=2, cols=2)
    # 设置表头（加粗）
    for cell in table.rows[0].cells:
        cell.paragraphs[0].add_run("Header").bold = True

    parser = TemplateParser()
    result = parser.extract_table_structure(table, session=session)

    assert "element_id" in result
    assert result["element_id"].startswith("table_")
    assert result["type"] == "table"

def test_extract_table_structure_without_session():
    doc = Document()
    table = doc.add_table(rows=2, cols=2)
    for cell in table.rows[0].cells:
        cell.paragraphs[0].add_run("Header").bold = True

    parser = TemplateParser()
    result = parser.extract_table_structure(table, session=None)

    assert "element_id" not in result  # 向后兼容
    assert result["type"] == "table"
```

#### 涉及文件

- `src/docx_mcp_server/core/template_parser.py`
- `tests/unit/test_template_parser.py`

---

### T-005: 修改 TemplateParser.extract_structure()

**优先级**: P0
**复杂度**: Standard
**预计工时**: 2 小时
**依赖**: T-002, T-003, T-004
**并行组**: 2

#### 任务描述

修改 `extract_structure()` 方法，在调用子方法时传入 `session` 参数。

#### 验收标准

- [ ] 方法签名添加 `session: Optional[Session] = None` 参数
- [ ] 调用 `extract_heading_structure()` 时传入 `session`
- [ ] 调用 `extract_paragraph_structure()` 时传入 `session`
- [ ] 调用 `extract_table_structure()` 时传入 `session`
- [ ] 单元测试验证返回的结构包含 `element_id`

#### 实现要点

```python
def extract_structure(
    self,
    document: DocumentType,
    session: Optional[Session] = None
) -> Dict[str, Any]:
    result = {
        "metadata": {...},
        "document_structure": []
    }

    for element in document.element.body:
        tag = element.tag.split('}')[-1]

        if tag == 'p':
            para = Paragraph(element, document)
            if para.style and 'Heading' in para.style.name:
                result["document_structure"].append(
                    self.extract_heading_structure(para, session=session)
                )
            elif para.text.strip():
                result["document_structure"].append(
                    self.extract_paragraph_structure(para, session=session)
                )

        elif tag == 'tbl':
            table = Table(element, document)
            try:
                result["document_structure"].append(
                    self.extract_table_structure(table, session=session)
                )
            except ValueError:
                pass

    return result
```

#### 涉及文件

- `src/docx_mcp_server/core/template_parser.py`
- `tests/unit/test_template_parser.py`

---

### T-006: 修改 docx_extract_template_structure()

**优先级**: P0
**复杂度**: Simple
**预计工时**: 1 小时
**依赖**: T-005
**并行组**: 2

#### 任务描述

修改 `docx_extract_template_structure()` 工具，在调用 `TemplateParser.extract_structure()` 时传入 `session`。

#### 验收标准

- [ ] 调用 `parser.extract_structure()` 时传入 `session` 参数
- [ ] 返回的 JSON 包含 `element_id` 字段
- [ ] 单元测试验证 `element_id` 可用于其他工具

#### 实现要点

```python
def docx_extract_template_structure(
    session_id: str,
    max_depth: int = None,
    include_content: bool = True,
    max_items_per_type: str = None
) -> str:
    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    parser = TemplateParser()
    # 传入 session 以启用 element_id 生成
    structure = parser.extract_structure(session.document, session=session)

    # 现有的过滤逻辑...
    return json.dumps(structure, indent=2, ensure_ascii=False)
```

#### 涉及文件

- `src/docx_mcp_server/tools/content_tools.py`
- `tests/unit/test_content_tools.py`

---

### T-007: 修改 docx_get_structure_summary()

**优先级**: P0
**复杂度**: Standard
**预计工时**: 2 小时
**依赖**: T-001
**并行组**: 2

#### 任务描述

修改 `docx_get_structure_summary()` 工具，为返回的 headings、tables、paragraphs 添加 `element_id` 字段。

#### 验收标准

- [ ] headings 数组中每个对象包含 `element_id` 字段
- [ ] tables 数组中每个对象包含 `element_id` 字段
- [ ] paragraphs 数组中每个对象包含 `element_id` 字段
- [ ] 单元测试验证 `element_id` 存在且可用

#### 实现要点

```python
def docx_get_structure_summary(...) -> str:
    session = session_manager.get_session(session_id)
    doc = session.document
    structure = {"headings": [], "tables": [], "paragraphs": []}

    for element in doc.element.body:
        if element.tag.endswith('p'):
            para = next((p for p in doc.paragraphs if p._element == element), None)
            if para and para.style.name.startswith('Heading'):
                if heading_count < max_headings:
                    heading_info = {
                        "level": ...,
                        "style": para.style.name,
                        "element_id": session._get_element_id(para, auto_register=True)
                    }
                    if include_content:
                        heading_info["text"] = para.text
                    structure["headings"].append(heading_info)
                    heading_count += 1

        elif element.tag.endswith('tbl') and table_count < max_tables:
            table = next((t for t in doc.tables if t._element == element), None)
            if table:
                table_info = {
                    "rows": len(table.rows),
                    "cols": len(table.columns),
                    "element_id": session._get_element_id(table, auto_register=True)
                }
                # ...
                structure["tables"].append(table_info)

    return json.dumps(structure, ensure_ascii=False, indent=2)
```

#### 涉及文件

- `src/docx_mcp_server/tools/composite_tools.py`
- `tests/unit/test_composite_tools.py`

---

### T-008: 修改 docx_read_content() 默认参数

**优先级**: P0
**复杂度**: Simple
**预计工时**: 0.5 小时
**依赖**: 无
**并行组**: 2

#### 任务描述

将 `docx_read_content()` 的 `include_ids` 参数默认值从 `False` 改为 `True`。

#### 验收标准

- [ ] `include_ids` 参数默认值为 `True`
- [ ] 不传 `include_ids` 时默认返回 `element_id`
- [ ] 传 `include_ids=False` 时不返回 `element_id`
- [ ] 更新 docstring 说明默认行为
- [ ] 单元测试覆盖两种情况

#### 实现要点

```python
def docx_read_content(
    session_id: str,
    max_paragraphs: Optional[int] = None,
    start_from: int = 0,
    include_tables: bool = False,
    return_json: bool = False,
    include_ids: bool = True,  # 从 False 改为 True
    ...
) -> str:
    """
    ...
    Args:
        ...
        include_ids (bool, optional): Include element IDs. Defaults to True.
        ...
    """
    # 现有逻辑保持不变
```

#### 涉及文件

- `src/docx_mcp_server/tools/content_tools.py`
- `tests/unit/test_content_tools.py`

---


### T-009: 修改 TableStructureAnalyzer.detect_irregular_structure()

**优先级**: P1
**复杂度**: Standard
**预计工时**: 2 小时
**依赖**: T-001
**并行组**: 3

#### 任务描述

为 `detect_irregular_structure()` 方法添加 `session` 参数，并在返回的 `grid_structure` 中为每个单元格添加 `cell_id` 字段。

#### 验收标准

- [ ] 方法签名添加 `session: Optional[Session] = None` 参数
- [ ] `grid_structure` 中每个单元格对象包含 `cell_id` 字段
- [ ] 当 `session` 为 `None` 时，不添加 `cell_id` 字段（向后兼容）
- [ ] 单元测试覆盖两种情况

#### 实现要点

```python
@staticmethod
def detect_irregular_structure(
    table: Table,
    session: Optional[Session] = None
) -> Dict[str, Any]:
    # 现有逻辑...
    grid_structure = []
    
    for row_idx, row in enumerate(table.rows):
        row_data = []
        for col_idx, cell in enumerate(row.cells):
            cell_info = {
                "row": row_idx,
                "col": col_idx,
                "text": cell.text[:50]
            }
            
            # 新增逻辑
            if session is not None:
                try:
                    cell_id = session._get_element_id(cell, auto_register=True)
                    if cell_id:
                        cell_info["cell_id"] = cell_id
                except Exception as e:
                    logger.warning(f"Failed to generate cell_id: {e}")
            
            row_data.append(cell_info)
        grid_structure.append(row_data)
    
    return {
        "is_irregular": ...,
        "merged_cells": ...,
        "grid_structure": grid_structure
    }
```

#### 涉及文件

- `src/docx_mcp_server/core/table_analyzer.py`
- `tests/unit/test_table_analyzer.py`

---

### T-010: 修改 docx_get_table_structure()

**优先级**: P1
**复杂度**: Simple
**预计工时**: 1 小时
**依赖**: T-009
**并行组**: 3

#### 任务描述

修改 `docx_get_table_structure()` 工具，在调用 `TableStructureAnalyzer.detect_irregular_structure()` 时传入 `session`。

#### 验收标准

- [ ] 调用 `detect_irregular_structure()` 时传入 `session` 参数
- [ ] 返回的 `structure_info` 包含 `cell_id` 字段
- [ ] 单元测试验证 `cell_id` 可用于其他工具

#### 实现要点

```python
def docx_get_table_structure(session_id: str, table_id: str) -> str:
    session = session_manager.get_session(session_id)
    table = session.get_object(table_id)
    
    # 传入 session 以启用 cell_id 生成
    structure_info = TableStructureAnalyzer.detect_irregular_structure(
        table,
        session=session
    )
    
    return create_success_response(
        message="Table structure retrieved successfully",
        element_id=table_id,
        structure_info=structure_info,
        ...
    )
```

#### 涉及文件

- `src/docx_mcp_server/tools/table_tools.py`
- `tests/unit/test_table_tools.py`

---


### T-011: 编写单元测试和 E2E 测试

**优先级**: P0
**复杂度**: Standard
**预计工时**: 3 小时
**依赖**: T-002, T-003, T-004, T-005, T-006, T-007, T-008, T-009, T-010
**并行组**: 独立

#### 任务描述

编写完整的单元测试和 E2E 测试，验证所有修改的功能正常工作。

#### 验收标准

- [ ] 所有修改的方法都有对应的单元测试
- [ ] 测试覆盖 `session` 为 `None` 和非 `None` 两种情况
- [ ] E2E 测试验证完整工作流：提取结构 → 获取 ID → 修改元素
- [ ] 测试验证 `element_id` 可用于其他工具
- [ ] 测试验证缓存机制正常工作
- [ ] 所有现有测试通过（向后兼容性）

#### 测试文件

1. **单元测试**：
   - `tests/unit/test_session.py` - Session 缓存测试
   - `tests/unit/test_template_parser.py` - TemplateParser 测试
   - `tests/unit/test_content_tools.py` - content_tools 测试
   - `tests/unit/test_composite_tools.py` - composite_tools 测试
   - `tests/unit/test_table_tools.py` - table_tools 测试
   - `tests/unit/test_table_analyzer.py` - TableStructureAnalyzer 测试

2. **E2E 测试**：
   - `tests/e2e/test_element_id_workflow.py` - 完整工作流测试

#### 关键测试用例

```python
# E2E 测试示例
def test_extract_and_modify_workflow():
    """测试：提取结构 → 获取 ID → 修改元素"""
    session_id = docx_create()
    session = session_manager.get_session(session_id)
    
    # 添加内容
    session.document.add_heading("Test Heading", level=1)
    session.document.add_paragraph("Test paragraph")
    
    # 提取结构
    structure_json = docx_extract_template_structure(session_id)
    structure = json.loads(structure_json)
    
    # 验证包含 element_id
    assert len(structure["document_structure"]) == 2
    heading = structure["document_structure"][0]
    para = structure["document_structure"][1]
    
    assert "element_id" in heading
    assert "element_id" in para
    
    # 使用 element_id 修改元素
    heading_id = heading["element_id"]
    para_id = para["element_id"]
    
    # 修改段落文本
    docx_update_paragraph_text(session_id, para_id, "Modified text")
    
    # 验证修改成功
    modified_para = session.get_object(para_id)
    assert modified_para.text == "Modified text"
```

#### 涉及文件

- `tests/unit/test_*.py`
- `tests/e2e/test_element_id_workflow.py`

---

### T-012: 性能测试

**优先级**: P1
**复杂度**: Standard
**预计工时**: 2 小时
**依赖**: T-011
**并行组**: 独立

#### 任务描述

编写性能测试，验证修改后的性能影响在可接受范围内。

#### 验收标准

- [ ] 内存增长 < 10%
- [ ] 调用延迟增加 < 5%
- [ ] 大文档（1000+ 段落）处理时间增加 < 10%
- [ ] 缓存命中率 > 90%（重复调用场景）

#### 测试场景

1. **小文档性能测试**（10 段落，2 表格）
2. **中文档性能测试**（100 段落，10 表格）
3. **大文档性能测试**（1000+ 段落，50+ 表格）
4. **缓存命中率测试**（重复调用 `_get_element_id()`）

#### 实现要点

```python
import time
import tracemalloc

def test_performance_large_document():
    """测试大文档性能"""
    session_id = docx_create()
    session = session_manager.get_session(session_id)
    
    # 创建大文档
    for i in range(1000):
        session.document.add_paragraph(f"Paragraph {i}")
    
    # 测量内存和时间
    tracemalloc.start()
    start_time = time.time()
    
    structure_json = docx_extract_template_structure(session_id)
    
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    # 验证性能指标
    elapsed_time = end_time - start_time
    memory_mb = peak / 1024 / 1024
    
    print(f"Time: {elapsed_time:.2f}s, Memory: {memory_mb:.2f}MB")
    
    # 断言（根据基准调整）
    assert elapsed_time < 5.0  # 5秒内完成
    assert memory_mb < 100  # 内存占用 < 100MB
```

#### 涉及文件

- `tests/performance/test_element_id_performance.py`

---


### T-013: 更新文档

**优先级**: P2
**复杂度**: Simple
**预计工时**: 2 小时
**依赖**: T-011
**并行组**: 独立

#### 任务描述

更新项目文档，说明新增的 `element_id` 功能。

#### 验收标准

- [ ] 更新 `README.md` 的工具列表，说明返回值包含 `element_id`
- [ ] 更新 `CLAUDE.md` 的快速参考部分
- [ ] 更新工具的 docstring，说明返回值变化
- [ ] 添加使用示例

#### 需要更新的文档

1. **README.md**：
   - 更新 `docx_extract_template_structure()` 说明
   - 更新 `docx_get_structure_summary()` 说明
   - 更新 `docx_read_content()` 说明（默认参数变化）
   - 更新 `docx_get_table_structure()` 说明

2. **CLAUDE.md**：
   - 更新快速参考部分
   - 添加使用示例

3. **工具 docstring**：
   - 更新所有修改的工具的 docstring

#### 示例更新

```markdown
### docx_extract_template_structure()

提取文档结构，包括标题、段落、表格。

**返回值**：
```json
{
  "document_structure": [
    {
      "type": "heading",
      "level": 1,
      "text": "Chapter 1",
      "element_id": "para_a1b2c3d4"  // 新增：可直接用于修改
    },
    {
      "type": "paragraph",
      "text": "Content...",
      "element_id": "para_e5f6g7h8"  // 新增：可直接用于修改
    },
    {
      "type": "table",
      "rows": 5,
      "cols": 3,
      "element_id": "table_i9j0k1l2"  // 新增：可直接用于修改
    }
  ]
}
```

**使用示例**：
```python
# 提取结构并直接修改
structure = json.loads(docx_extract_template_structure(session_id))
para_id = structure["document_structure"][1]["element_id"]
docx_update_paragraph_text(session_id, para_id, "New text")
```
```

#### 涉及文件

- `README.md`
- `CLAUDE.md`
- `src/docx_mcp_server/tools/content_tools.py`
- `src/docx_mcp_server/tools/composite_tools.py`
- `src/docx_mcp_server/tools/table_tools.py`

---

## 并行执行计划

### 并行组 1（依赖 T-001）

可以并行执行的任务：
- T-002: 修改 TemplateParser.extract_heading_structure()
- T-003: 修改 TemplateParser.extract_paragraph_structure()
- T-004: 修改 TemplateParser.extract_table_structure()

**预计总工时**: 2 小时（并行）

### 并行组 2（依赖并行组 1）

可以并行执行的任务：
- T-005: 修改 TemplateParser.extract_structure()
- T-006: 修改 docx_extract_template_structure()
- T-007: 修改 docx_get_structure_summary()
- T-008: 修改 docx_read_content() 默认参数

**预计总工时**: 2 小时（并行）

### 并行组 3（依赖 T-001）

可以并行执行的任务：
- T-009: 修改 TableStructureAnalyzer.detect_irregular_structure()
- T-010: 修改 docx_get_table_structure()

**预计总工时**: 2 小时（并行）

---

## 总体时间估算

| 阶段 | 任务 | 工时（串行） | 工时（并行） |
|------|------|-------------|-------------|
| 基础设施 | T-001 | 1h | 1h |
| 核心解析器 | T-002, T-003, T-004 | 6h | 2h |
| 工具层 | T-005, T-006, T-007, T-008 | 5.5h | 2h |
| 表格分析 | T-009, T-010 | 3h | 2h |
| 测试 | T-011 | 3h | 3h |
| 性能测试 | T-012 | 2h | 2h |
| 文档更新 | T-013 | 2h | 2h |
| **总计** | | **22.5h** | **14h** |

**说明**：
- 串行执行需要约 22.5 小时
- 并行执行需要约 14 小时（节省 38%）
- 建议采用并行执行策略

---

## 风险与缓解措施

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 缓存不一致导致 ID 重复 | 中 | 高 | T-001 中添加缓存验证逻辑 |
| 现有测试失败 | 低 | 高 | T-011 中运行完整回归测试 |
| 性能下降超过预期 | 低 | 中 | T-012 中及时发现并优化 |
| 向后兼容性破坏 | 低 | 高 | 所有修改保持参数签名不变 |

---

## 验收清单

### 功能验收

- [ ] F-001: docx_extract_template_structure 返回 element_id
- [ ] F-002: docx_get_structure_summary 返回 element_id
- [ ] F-003: docx_read_content 默认返回 element_id
- [ ] F-004: docx_get_table_structure 返回 cell_id
- [ ] F-005: 返回的 element_id 可用于其他工具
- [ ] F-006: 所有现有测试通过

### 性能验收

- [ ] P-001: 内存增长 < 10%
- [ ] P-002: 调用延迟增加 < 5%
- [ ] P-003: 大文档处理时间增加 < 10%
- [ ] P-004: 缓存命中率 > 90%

### 文档验收

- [ ] D-001: README.md 已更新
- [ ] D-002: CLAUDE.md 已更新
- [ ] D-003: 工具 docstring 已更新
- [ ] D-004: 添加使用示例

---

**任务拆分者**: AI Team
**审核者**: 待定
**批准者**: 待定
**版本历史**:
- v1 (2026-01-23): 初始拆分

