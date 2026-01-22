# 文档与代码冲突分析报告

**生成时间**: 2026-01-21
**分析范围**: CLAUDE.md, README.md, 源代码
**工具总数**: 42 个

---

## 🔴 严重冲突（需要立即修复）

### 1. 函数调用签名错误

**位置**: `CLAUDE.md:69`

**错误代码**:
```python
run_id = docx_insert_run(session_id, "World", position=f"inside:{para_id}")
```

**正确代码**:
```python
run_id = docx_insert_run(session_id, "World", position=f"inside:{para_id}")
```

**实际函数签名**:
```python
def docx_insert_run(session_id: str, text: str, position: str) -> str:
```

**影响**: 用户按照文档示例编写代码会导致运行时错误。

---

## 🟡 中等冲突（需要更新文档）

### 2. 工具列表不完整

#### 2.1 README.md 缺失的工具（4 个）

**缺失工具**:
1. `docx_cursor_get(session_id)` - 获取光标位置
2. `docx_cursor_move(session_id, element_id, position)` - 移动光标
3. `docx_insert_paragraph(session_id, text, position)` - 按 position 插入段落
4. `docx_insert_table(session_id, rows, cols, position)` - 按 position 插入表格

**建议**: 在 README.md 的"MCP 工具列表"章节添加"Cursor 定位系统"小节。

#### 2.2 CLAUDE.md 缺失的详细工具说明

**已有示例但缺少详细说明的工具**:
- `docx_cursor_*` 系列（4 个工具）
- `docx_batch_replace_text` - 批量替换
- `docx_copy_elements_range` - 范围复制
- `docx_get_element_source` - 获取元素来源

**建议**: 在 CLAUDE.md 的"快速参考"章节补充完整工具列表。

---

### 3. 项目结构描述过时

**位置**: `README.md:237-251`

**当前描述**:
```
docx-mcp-server/
├── src/docx_mcp_server/
│   ├── server.py          # MCP 工具定义
│   ├── core/              # 核心逻辑
│   │   ├── session.py     # 会话管理
│   │   ├── copier.py      # 对象克隆引擎
│   │   ├── replacer.py    # 文本替换引擎
│   │   └── properties.py  # 属性设置引擎
```

**实际结构**（缺失 tools/ 模块）:
```
docx-mcp-server/
├── src/docx_mcp_server/
│   ├── server.py          # MCP 主入口（非工具定义）
│   ├── tools/             # 🚨 新增：工具模块
│   │   ├── session_tools.py
│   │   ├── content_tools.py
│   │   ├── paragraph_tools.py
│   │   ├── run_tools.py
│   │   ├── table_tools.py
│   │   ├── format_tools.py
│   │   ├── advanced_tools.py
│   │   ├── cursor_tools.py
│   │   ├── copy_tools.py
│   │   └── system_tools.py
│   ├── core/              # 核心逻辑
│   │   ├── session.py
│   │   ├── cursor.py      # 🚨 新增：光标系统
│   │   ├── copier.py
│   │   ├── replacer.py
│   │   └── properties.py
```

**建议**: 更新 README.md 中的项目结构图，反映模块化架构。

---

### 4. 示例代码引用错误的参数顺序

**位置**: `README.md:179-187`

**示例 2 标题重复**:
- 第 177 行：`### 示例 2：模板填充（智能替换）`
- 第 189 行：`### 示例 2：表格克隆与填充`

两个"示例 2"，应该改为"示例 3"。

---

## 🟢 轻微冲突（建议优化）

### 5. 文档风格不一致

#### 5.1 工具描述格式

**CLAUDE.md**: 使用完整的 Google 风格 docstring（Args、Returns、Raises）
**README.md**: 仅列出函数签名，无详细说明

**建议**: 统一风格，或在 README.md 中链接到详细 API 文档。

#### 5.2 示例代码风格

**CLAUDE.md**: 使用内联注释和完整流程
**README.md**: 使用独立代码块 + 输出示例

**建议**: 两者互补，保持各自特色即可。

---

### 6. 缺少模块化架构说明

**位置**: `CLAUDE.md:14`

**现状**:
```markdown
- **模块化架构**：工具按领域拆分，便于维护和扩展
```

**缺失内容**:
- 各模块的职责说明
- 模块间的依赖关系
- 如何选择在哪个模块添加新工具

**建议**: 在 CLAUDE.md 的"核心架构"章节添加"模块划分"小节。

---

## 📊 工具完整性统计

### 按模块分类（实际代码）

| 模块 | 工具数 | 主要功能 |
|------|--------|----------|
| session_tools | 4 | 会话生命周期管理 |
| content_tools | 4 | 内容检索与浏览 |
| paragraph_tools | 6 | 段落操作 |
| run_tools | 3 | 文本块操作 |
| table_tools | 9 | 表格操作 |
| format_tools | 6 | 格式化与样式 |
| advanced_tools | 3 | 高级编辑（替换、图片） |
| cursor_tools | 4 | 光标定位系统 |
| copy_tools | 2 | 复制与元数据 |
| system_tools | 1 | 系统状态 |
| **总计** | **42** | |

### 文档覆盖情况

| 文档 | 已列出工具数 | 覆盖率 | 缺失工具数 |
|------|------------|--------|-----------|
| README.md | 约 35 | 83% | 7 |
| CLAUDE.md | 约 20（示例） | 48% | 22 |

---

## ✅ 修复建议优先级

### P0（立即修复）
1. 修复 `CLAUDE.md:69` 的 `docx_insert_run` 调用签名错误
2. 修复 `README.md` 的示例编号重复问题

### P1（本周修复）
3. 更新 README.md 的项目结构图
4. 在 README.md 添加 Cursor 系统工具列表
5. 补充 CLAUDE.md 中缺失的工具说明

### P2（下周完成）
6. 统一文档风格（可选）
7. 添加模块化架构详细说明
8. 创建独立的 API 参考文档（如 docs/API.md）

---

## 🔧 自动化检查建议

为避免未来文档与代码不一致，建议添加 CI 检查：

```bash
# 1. 提取所有工具函数
grep -h "^def docx_" src/docx_mcp_server/tools/*.py | sed 's/(.*//g' > /tmp/actual_tools.txt

# 2. 提取 README.md 中列出的工具
grep -E "^- \`docx_" README.md | sed 's/.*`\(docx_[^(]*\).*/\1/' > /tmp/documented_tools.txt

# 3. 对比差异
diff /tmp/actual_tools.txt /tmp/documented_tools.txt
```

---

## 📝 总结

- **冲突总数**: 6 类
- **严重程度**: 1 个严重，3 个中等，2 个轻微
- **主要原因**: 代码重构后文档未同步更新（feature/dev 合并后）
- **推荐行动**: 按优先级逐步修复，添加自动化检查防止回归

---

**下一步行动**:
1. 创建 Issue 追踪这些冲突
2. 分配修复任务
3. 设置文档更新的 Git Hook
