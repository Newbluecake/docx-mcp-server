---
feature: template-structure-extraction
complexity: standard
generated_by: architect-planner
generated_at: 2026-01-21T10:42:00Z
version: 1
---

# 任务拆分: Word 模板结构提取

> **功能标识**: template-structure-extraction
> **复杂度**: standard
> **生成时间**: 2026-01-21T10:42:00Z

## 任务列表

### T-001: 创建 TemplateParser 核心类

**描述**: 创建 `template_parser.py` 模块和 `TemplateParser` 类，实现基础结构

**优先级**: P0

**依赖**: 无

**验收标准**:
- 创建 `src/docx_mcp_server/core/template_parser.py`
- 实现 `TemplateParser` 类，包含 `__init__` 方法
- 实现 `extract_structure(document)` 主方法框架
- 添加基础导入和类型注解

**预估工作量**: 30 分钟

**文件变更**:
- 新增: `src/docx_mcp_server/core/template_parser.py`

---

### T-002: 实现智能表头检测算法

**描述**: 实现 `detect_header_row()` 和 `has_background_color()` 方法

**优先级**: P0

**依赖**: T-001

**验收标准**:
- 实现 `detect_header_row(table)` 方法
- 实现 `has_background_color(cell)` 辅助方法
- 检测逻辑：加粗 OR 背景色 → 表头
- 检测失败抛出 ValueError: "无法检测表头行：第一行既无加粗也无背景色"
- 添加单元测试: `test_detect_header_row_bold()`, `test_detect_header_row_background()`, `test_detect_header_row_fail()`

**预估工作量**: 1 小时

**文件变更**:
- 修改: `src/docx_mcp_server/core/template_parser.py`
- 新增: `tests/unit/test_template_parser.py`

---

### T-003: 实现表格结构提取

**描述**: 实现 `extract_table_structure()` 方法，提取表格行列数、表头、样式

**优先级**: P0

**依赖**: T-002

**验收标准**:
- 实现 `extract_table_structure(table)` 方法
- 提取行数、列数、表头行索引、列名列表
- 提取表格边框样式（top/bottom/left/right）
- 提取单元格样式（字体、对齐、背景色）
- 调用 `detect_header_row()` 进行表头检测
- 添加单元测试: `test_extract_table_structure()`

**预估工作量**: 1.5 小时

**文件变更**:
- 修改: `src/docx_mcp_server/core/template_parser.py`
- 修改: `tests/unit/test_template_parser.py`

---

### T-004: 实现标题结构提取

**描述**: 实现 `extract_heading_structure()` 方法，识别 Heading 1/2/3 样式

**优先级**: P0

**依赖**: T-001

**验收标准**:
- 实现 `extract_heading_structure(paragraph)` 方法
- 识别标题层级（level: 1/2/3）
- 提取标题文本和样式（字体、大小、加粗、颜色）
- 添加单元测试: `test_extract_heading_structure()`

**预估工作量**: 45 分钟

**文件变更**:
- 修改: `src/docx_mcp_server/core/template_parser.py`
- 修改: `tests/unit/test_template_parser.py`

---

### T-005: 实现段落结构提取

**描述**: 实现 `extract_paragraph_structure()` 方法，提取段落文本和样式

**优先级**: P1

**依赖**: T-001

**验收标准**:
- 实现 `extract_paragraph_structure(paragraph)` 方法
- 提取段落文本
- 提取样式：字体、大小、加粗、斜体、下划线、颜色
- 提取对齐方式（left/center/right/justify）
- 提取缩进（left_indent, right_indent, first_line_indent）
- 添加单元测试: `test_extract_paragraph_structure()`

**预估工作量**: 1 小时

**文件变更**:
- 修改: `src/docx_mcp_server/core/template_parser.py`
- 修改: `tests/unit/test_template_parser.py`

---

### T-006: 实现图片结构提取

**描述**: 实现 `extract_image_structure()` 方法，提取图片尺寸和对齐

**优先级**: P1

**依赖**: T-001

**验收标准**:
- 实现 `extract_image_structure(paragraph)` 方法
- 提取图片宽度和高度（单位：英寸）
- 提取对齐方式
- 提取替代文本（alt_text）
- 添加单元测试: `test_extract_image_structure()`

**预估工作量**: 1 小时

**文件变更**:
- 修改: `src/docx_mcp_server/core/template_parser.py`
- 修改: `tests/unit/test_template_parser.py`

---

### T-007: 实现主提取方法

**描述**: 完善 `extract_structure()` 方法，遍历文档元素并调用各提取方法

**优先级**: P0

**依赖**: T-002, T-003, T-004, T-005, T-006

**验收标准**:
- 完善 `extract_structure(document)` 方法
- 遍历 `document.element.body` 识别元素类型
- 按顺序调用对应的提取方法
- 构建 JSON 结构（包含 metadata 和 document_structure）
- 返回 Python dict（不序列化为 JSON 字符串）
- 添加单元测试: `test_extract_structure_order()`

**预估工作量**: 45 分钟

**文件变更**:
- 修改: `src/docx_mcp_server/core/template_parser.py`
- 修改: `tests/unit/test_template_parser.py`

---

### T-008: 添加 MCP 工具接口

**描述**: 在 `server.py` 中添加 `docx_extract_template_structure()` 工具

**优先级**: P0

**依赖**: T-007

**验收标准**:
- 在 `server.py` 中添加 `@mcp.tool()` 装饰的函数
- 函数签名: `docx_extract_template_structure(session_id: str) -> str`
- 获取 Session，调用 `TemplateParser.extract_structure()`
- 将结果序列化为 JSON 字符串返回
- 添加错误处理（Session 不存在、文档为空）
- 添加 docstring 说明工具用途

**预估工作量**: 30 分钟

**文件变更**:
- 修改: `src/docx_mcp_server/server.py`

---

### T-009: E2E 测试 - 完整模板提取

**描述**: 创建 E2E 测试，验证完整模板提取流程

**优先级**: P0

**依赖**: T-008

**验收标准**:
- 创建 `tests/e2e/test_template_extraction.py`
- 测试用例: `test_extract_complete_template()`
  - 创建包含标题、段落、表格的文档
  - 调用 `docx_extract_template_structure()`
  - 验证 JSON 结构完整性
  - 验证元素顺序正确
- 测试用例: `test_extract_with_header_detection()`
  - 创建带加粗表头的表格
  - 验证表头检测成功
- 测试用例: `test_extract_header_detection_fail()`
  - 创建无加粗无背景色的表格
  - 验证抛出 ValueError

**预估工作量**: 1 小时

**文件变更**:
- 新增: `tests/e2e/test_template_extraction.py`

---

### T-010: 文档更新

**描述**: 更新 README.md 和 CLAUDE.md，添加新工具说明

**优先级**: P1

**依赖**: T-008

**验收标准**:
- 在 README.md 的工具列表中添加 `docx_extract_template_structure`
- 添加使用示例和输出格式说明
- 在 CLAUDE.md 的"快速参考"中添加模板提取示例
- 更新"最后更新"时间

**预估工作量**: 30 分钟

**文件变更**:
- 修改: `README.md`
- 修改: `CLAUDE.md`

---

## 任务依赖图

```
T-001 (TemplateParser 核心类)
  ├── T-002 (智能表头检测)
  │     └── T-003 (表格结构提取)
  ├── T-004 (标题结构提取)
  ├── T-005 (段落结构提取)
  └── T-006 (图片结构提取)
        ↓
      T-007 (主提取方法)
        ↓
      T-008 (MCP 工具接口)
        ├── T-009 (E2E 测试)
        └── T-010 (文档更新)
```

## 并行执行建议

### 组 1 (并行)
- T-001 (核心类)

### 组 2 (并行，依赖 T-001)
- T-002 (表头检测)
- T-004 (标题提取)
- T-005 (段落提取)
- T-006 (图片提取)

### 组 3 (串行，依赖组 2)
- T-003 (表格提取，依赖 T-002)

### 组 4 (串行，依赖组 2 和 T-003)
- T-007 (主提取方法)

### 组 5 (串行，依赖 T-007)
- T-008 (MCP 工具)

### 组 6 (并行，依赖 T-008)
- T-009 (E2E 测试)
- T-010 (文档更新)

## 总预估工作量

- P0 任务: 6.5 小时
- P1 任务: 2.5 小时
- **总计**: 9 小时

---

**文档版本**: v1
**最后更新**: 2026-01-21T10:42:00Z
