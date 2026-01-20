---
feature: docx-full-features
status: pending
---

# 任务分解: Docx MCP Server 全功能重构

## 分组 1: 核心架构升级
> 基础上下文管理和属性引擎，是后续功能的基础。

- [ ] **T-001: 实现混合上下文 Session 机制**
  - 修改 `Session` 类，添加 `last_created_id`, `last_accessed_id`。
  - 实现 `update_context` 方法。
  - 实现 `auto_save` 触发逻辑。
  - 单元测试: 验证上下文指针更新正确。

- [ ] **T-002: 实现属性映射引擎 (Property Engine)**
  - 创建 `src/docx_mcp_server/core/properties.py`。
  - 实现字典到 python-docx 对象的递归设值逻辑。
  - 处理 Enum (对齐方式) 和 Color (RGB) 的转换。
  - 单元测试: 测试 font, paragraph_format 等属性设置。

## 分组 2: 核心工具重构
> 升级现有工具以支持上下文和新属性引擎。

- [ ] **T-003: 重构 docx_create 和 docx_add_paragraph/run**
  - 更新 `docx_create` 支持 `auto_save` 参数。
  - 更新 `add_paragraph`, `add_run` 支持可选 `parent_id` (使用上下文)。
  - 集成 `auto_save` 逻辑。
  - 验证: 连续调用无需 ID。

- [ ] **T-004: 实现 docx_set_properties 工具**
  - 在 `server.py` 暴露新工具。
  - 连接 T-002 的引擎。
  - 废弃或保留旧的独立 setter 工具 (建议保留但标记为 legacy，或通过 shim 调用新引擎)。

## 分组 3: 表格与导航增强
> 复杂的表格操作和文档定位。

- [ ] **T-005: 实现增强型导航工具**
  - 创建 `src/docx_mcp_server/core/finder.py`。
  - 实现 `docx_get_table(index)`, `docx_find_paragraph(text)`。
  - 实现 `docx_list_files(path)` (带安全检查)。

- [ ] **T-006: 实现表格深拷贝 (XML Clone)**
  - 研究 `copy.deepcopy(table._tbl)` 的可行性。
  - 实现 `docx_copy_table`: 深度复制表格结构和样式。
  - 确保复制后能正确插入文档流。
  - 集成上下文：新复制的表格成为当前上下文。

- [ ] **T-009: 实现表格行/列操作与批量填充**
  - 实现 `docx_add_table_row/col`。
  - 实现 `docx_fill_table(data, start_row)`: 支持二维数组批量填充。

## 分组 4: 高级功能与收尾
> 图片、替换和 E2E 测试。

- [ ] **T-007: 实现图片插入与跨 Run 文本替换**
  - 实现 `docx_insert_image`: 支持本地路径和尺寸调整。
  - 实现 `docx_replace_text`: **关键** 实现跨 Run 文本拼接与替换算法 (Text Stitching)。

- [ ] **T-010: 上下文查询与辅助工具**
  - 实现 `docx_get_context`: 返回当前 ID 指针状态。
  - 实现 `docx_delete`: 删除当前选中的段落或表格。

- [ ] **T-008: 全链路 E2E 测试**
  - 编写 `tests/e2e/test_full_workflow.py`。
  - 模拟完整场景: 打开模板 -> 查找表格 -> 复制表格 -> 批量填入数据 -> 替换占位符 -> 插入图片 -> 保存。
