---
feature: format-copy-system
status: todo
---

# 任务拆分: 格式复制与模板系统

## 阶段 1: 基础设施与核心引擎

- [ ] **T-000: Spike - 验证 XML DeepCopy 方案**
  - 创建临时脚本验证 `deepcopy(element._element)`
  - 验证如何将 XML 元素正确包装回 `Paragraph` / `Table` 对象
  - 验证插入到文档指定位置的可行性
  - 输出: 技术验证报告或更新后的设计文档

- [ ] **T-001: 扩展 Session 支持元数据**
  - 修改 `src/docx_mcp_server/core/session.py`
  - 增加 `element_metadata` 字典
  - 更新 `register_object` 签名: `def register_object(self, obj, prefix, metadata=None)` (保持兼容)
  - 实现 `get_metadata` 方法
  - 增加单元测试，确保现有工具调用不受影响

- [ ] **T-002: 实现 TemplateManager (基于 FormatPainter)**
  - 创建 `src/docx_mcp_server/utils/format_template.py`
  - 复用 `src/docx_mcp_server/core/format_painter.py` 中的逻辑
  - 实现 `extract_properties` (支持 Paragraph, Run, Table)
  - 实现 `apply_properties`
  - 实现 JSON 序列化/反序列化 (建议使用 dataclass)
  - 增加单元测试

- [ ] **T-003: 实现 CopyEngine 核心 (XML DeepCopy)**
  - 创建 `src/docx_mcp_server/utils/copy_engine.py`
  - 实现基于 `lxml` 的 `copy_element_xml`
  - 封装为 python-docx 对象并注册到 Session 的逻辑
  - 验证格式保留情况 (包含 Runs)

- [ ] **T-004: 实现 CopyEngine 区间逻辑**
  - 在 `CopyEngine` 中实现 `get_elements_between(start_el, end_el)`
  - 增加元素过滤逻辑: 仅处理 `w:p` (paragraph) 和 `w:tbl` (table)
  - 实现 `copy_range` 逻辑：遍历 -> 复制 -> 插入文档末尾 -> 注册
  - 处理 XML 命名空间和父子关系

## 阶段 2: MCP 工具实现

- [ ] **T-005: 实现原子复制工具**
  - 在 `server.py` (或分拆的 tools 模块) 实现 `docx_copy_paragraph`
  - 实现 `docx_copy_heading` (或合并到 paragraph 工具)
  - 集成 `track_source` 功能
  - 实现 `docx_get_element_source` 查询工具

- [ ] **T-006: 实现区间复制工具**
  - 实现 `docx_copy_elements_range`
  - 集成 CopyEngine 的 range 逻辑
  - 返回 ID 映射列表
  - 增加性能测试: 验证批量复制 100+ 段落耗时 < 5s

- [ ] **T-007: 实现模板管理工具**
  - 实现 `docx_extract_format_template`
  - 实现 `docx_apply_format_template`
  - 集成 TemplateManager

- [ ] **T-008: 实现批量替换工具**
  - 创建 `src/docx_mcp_server/utils/text_tools.py`
  - 明确 MVP 策略: 仅支持 Run 级别替换 (记录跨 Run 替换限制)
  - 实现 `batch_replace_text`
  - 注册 MCP 工具 `docx_batch_replace_text`

## 阶段 3: 验证与验收

- [ ] **T-009: E2E 测试**
  - 编写 `tests/e2e/test_format_copy.py`
  - 场景: 加载模板 -> 提取格式 -> 复制章节 -> 批量替换 -> 导出
  - 验证生成的 docx 文件属性

- [ ] **T-010: 文档更新**
  - 更新 `README.md` 添加新工具说明
  - 更新 `CLAUDE.md` 常用工具组合示例
