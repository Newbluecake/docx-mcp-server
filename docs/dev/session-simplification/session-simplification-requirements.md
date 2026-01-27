---
feature: session-simplification
complexity: complex
generated_by: clarify
generated_at: 2026-01-27T10:30:00+08:00
version: 1
---

# 需求文档: Session 简化 - 移除 session_id 参数

> **功能标识**: session-simplification
> **复杂度**: complex
> **生成方式**: clarify
> **生成时间**: 2026-01-27

## 1. 概述

### 1.1 一句话描述

简化会话管理：移除 `docx_create` 工具，让 switch 文件时自动创建会话，所有工具不再需要传入 `session_id` 参数。

### 1.2 核心价值

- **简化 API**：Claude 调用工具时无需管理 session_id，降低认知负担
- **减少错误**：消除 session_id 传递错误、过期等问题
- **更直观**：switch 文件 = 开始编辑，符合用户心智模型

### 1.3 目标用户

- **主要用户**：Claude（通过 MCP 协议调用工具）
- **次要用户**：Launcher GUI 用户（通过 switch 按钮选择文件）

---

## 2. 需求与用户故事

### 2.1 需求清单

| ID | 需求点 | 优先级 | 用户故事 |
|----|--------|--------|----------|
| R-001 | switch 自动创建会话 | P0 | As Claude, I want switch_file to auto-create session, so that I don't need to call docx_create |
| R-002 | 移除 session_id 参数 | P0 | As Claude, I want tools without session_id param, so that API is simpler |
| R-003 | 移除 docx_create | P0 | As a developer, I want to remove docx_create, so that API is cleaner |
| R-004 | 新增 session 管理工具 | P1 | As Claude, I want docx_get_current_session(), so that I can check session status |
| R-005 | 保留 docx_switch_session | P2 | As Claude, I want to switch between sessions, so that I can restore previous work |

### 2.2 验收标准

#### R-001: switch 自动创建会话
- **WHEN** 用户通过 Launcher 点击 switch 按钮选择文件, **THEN** 系统 **SHALL** 自动关闭旧会话并创建新会话
- **WHEN** switch_file API 被调用, **THEN** 返回值 **SHALL** 包含新创建的 sessionId
- **WHEN** 存在未保存更改且 force=false, **THEN** 系统 **SHALL** 返回 409 错误

#### R-002: 移除 session_id 参数
- **WHEN** 调用任何文档操作工具（如 docx_insert_paragraph）, **THEN** 工具 **SHALL** 自动使用全局活跃会话
- **WHEN** 没有活跃会话时调用工具, **THEN** 系统 **SHALL** 返回明确的错误信息

#### R-003: 移除 docx_create
- **WHEN** 尝试调用 docx_create, **THEN** 系统 **SHALL** 返回工具不存在的错误
- **WHEN** 查看 MCP 工具列表, **THEN** docx_create **SHALL NOT** 出现

#### R-004: 新增 session 管理工具
- **WHEN** 调用 docx_get_current_session(), **THEN** 系统 **SHALL** 返回当前会话的 session_id、file_path、状态信息

---

## 3. 功能验收清单

| ID | 功能点 | 验收步骤 | 优先级 | 关联需求 | 通过 |
|----|--------|----------|--------|----------|------|
| F-001 | switch 自动创建会话 | 1. 调用 switch_file API 2. 验证返回包含 sessionId | P0 | R-001 | ☐ |
| F-002 | 工具无 session_id | 1. 调用 docx_insert_paragraph(text, position) 2. 验证成功执行 | P0 | R-002 | ☐ |
| F-003 | docx_create 已移除 | 1. 查看 MCP 工具列表 2. 确认无 docx_create | P0 | R-003 | ☐ |
| F-004 | 获取当前会话 | 1. 调用 docx_get_current_session() 2. 验证返回会话信息 | P1 | R-004 | ☐ |
| F-005 | 无会话时报错 | 1. 不 switch 文件直接调用工具 2. 验证返回 NoActiveSession 错误 | P0 | R-002 | ☐ |

---

## 4. 技术约束

### 4.1 技术栈
- Python 3.10+
- FastMCP (MCP Server Framework)
- python-docx

### 4.2 架构变更

**当前架构**:
```
Launcher → switch_file → 设置 active_file
Claude → docx_create(session_id) → 创建会话
Claude → docx_insert_*(session_id, ...) → 操作文档
```

**目标架构**:
```
Launcher → switch_file → 设置 active_file + 自动创建会话
Claude → docx_insert_*(...) → 自动使用全局会话
```

### 4.3 影响范围

| 模块 | 文件数 | 变更类型 |
|------|--------|----------|
| session_tools.py | 1 | 移除 docx_create，新增 docx_get_current_session |
| file_controller.py | 1 | switch_file 自动创建会话 |
| 所有 *_tools.py | ~10 | 移除 session_id 参数 |
| 测试文件 | ~60 | 更新所有测试用例 |
| CLAUDE.md | 1 | 更新文档 |

---

## 5. 排除项

- **多会话并行编辑**：本次只支持单会话模式，不支持同时编辑多个文档
- **会话持久化**：会话仍然是内存中的，服务器重启后丢失
- **向后兼容**：这是 Breaking Change，不提供兼容层

---

## 6. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 大量测试需要更新 | 高 | 编写脚本批量更新测试 |
| 文档需要全面更新 | 中 | 同步更新 CLAUDE.md 和 README |
| 用户习惯变更 | 低 | 提供清晰的迁移指南 |

---

## 7. 下一步

✅ 在新会话中执行：
```bash
/clouditera:dev:spec-dev session-simplification --skip-requirements
```

或直接开始实施（由于变更范围大，建议走完整 SDD 流程）。
