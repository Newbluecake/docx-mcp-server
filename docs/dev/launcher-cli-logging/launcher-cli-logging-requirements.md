---
feature: launcher-cli-logging
complexity: standard
generated_by: clarify
generated_at: 2026-01-25T10:45:00Z
version: 1
---

# 需求文档: Launcher CLI Logging Enhancement

> **功能标识**: launcher-cli-logging
> **复杂度**: standard
> **生成方式**: clarify
> **生成时间**: 2026-01-25 10:45:00

## 1. 概述

### 1.1 一句话描述
在 GUI 启动器中增强日志记录功能，记录 MCP 服务器和 Claude CLI 的启动命令，并改进错误信息的可用性。

### 1.2 核心价值
- **可追溯性**：记录完整的启动命令，便于问题排查和复现
- **用户体验**：通过复选框简化常用参数配置，通过复制按钮方便错误报告
- **调试效率**：结构化的日志格式便于自动化分析和问题定位

### 1.3 目标用户
- **主要用户**：docx-mcp-server 的开发者和高级用户
- **次要用户**：需要报告问题的普通用户

---

## 2. 需求与用户故事

### 2.1 需求清单

| ID | 需求点 | 优先级 | 用户故事 |
|----|--------|--------|----------|
| R-001 | MCP 服务器启动命令日志 | P0 | As a developer, I want the MCP server startup command logged, so that I can reproduce issues |
| R-002 | Claude CLI 启动命令日志 | P0 | As a developer, I want the Claude CLI startup command logged, so that I can debug CLI integration issues |
| R-003 | Claude CLI 参数复选框 | P1 | As a user, I want to select common CLI options via checkboxes, so that I don't need to remember command syntax |
| R-004 | 错误信息复制按钮 | P1 | As a user, I want to copy error messages easily, so that I can report issues accurately |

### 2.2 验收标准

#### R-001: MCP 服务器启动命令日志
- **WHEN** GUI 启动器启动 MCP 服务器, **THEN** 系统 **SHALL**:
  - 在启动前记录完整的启动命令到 GUI 日志文件
  - 在启动前记录完整的启动命令到 MCP 服务器日志文件
  - 使用 INFO 级别
  - 使用 JSON 结构化格式（包含 command 和 args）
  - 示例格式：`{"command": "uv", "args": ["run", "mcp-server-docx", "--transport", "sse", "--port", "3000"]}`

#### R-002: Claude CLI 启动命令日志
- **WHEN** GUI 启动器启动 Claude CLI, **THEN** 系统 **SHALL**:
  - 记录完整的 Claude CLI 命令到 GUI 日志文件
  - 使用 INFO 级别
  - 记录完整命令字符串（如：`claude --mcp-config {...} --model opus`）
  - 记录 MCP 配置的 JSON 内容
  - 记录用户输入的额外参数

#### R-003: Claude CLI 参数复选框
- **WHEN** 用户在 GUI 中勾选 Claude CLI 参数选项, **THEN** 系统 **SHALL**:
  - 自动将选中的参数添加到启动命令中
  - 支持常用参数（如 --model, --agent 等）
  - 保存用户的选择到配置文件
  - 下次启动时恢复用户的选择

#### R-004: 错误信息复制按钮
- **WHEN** 错误弹窗显示时, **THEN** 系统 **SHALL**:
  - 在弹窗中显示"复制"按钮
  - 点击按钮后将错误信息复制到剪贴板
  - 显示复制成功的提示

---

## 3. 功能验收清单

| ID | 功能点 | 验收步骤 | 优先级 | 关联需求 | 通过 |
|----|--------|----------|--------|----------|------|
| F-001 | MCP 服务器启动日志 | 1. 启动 MCP 服务器 2. 检查 GUI 日志文件 3. 检查 MCP 服务器日志文件 4. 验证 JSON 格式 | P0 | R-001 | ☐ |
| F-002 | Claude CLI 启动日志 | 1. 启动 Claude CLI 2. 检查 GUI 日志文件 3. 验证命令字符串 4. 验证 MCP 配置 | P0 | R-002 | ☐ |
| F-003 | CLI 参数复选框 | 1. 勾选参数选项 2. 启动 Claude CLI 3. 验证命令包含选中参数 4. 重启 GUI 5. 验证选择被恢复 | P1 | R-003 | ☐ |
| F-004 | 错误复制按钮 | 1. 触发错误弹窗 2. 点击复制按钮 3. 验证剪贴板内容 4. 验证提示显示 | P1 | R-004 | ☐ |

---

## 4. 技术约束

### 4.1 技术栈
- **GUI 框架**: PyQt6
- **日志库**: Python logging + RotatingFileHandler
- **配置管理**: QSettings

### 4.2 集成点
- **现有模块**:
  - `src/docx_server_launcher/core/cli_launcher.py` - CLI 启动器
  - `src/docx_server_launcher/gui/main_window.py` - 主窗口
  - `src/docx_server_launcher/core/server_manager.py` - 服务器管理器

### 4.3 日志格式规范
- **MCP 服务器启动日志**:
  ```
  [2026-01-25 10:30:45] INFO: Starting MCP server with command: {"command": "uv", "args": ["run", "mcp-server-docx", "--transport", "sse", "--port", "3000"]}
  ```

- **Claude CLI 启动日志**:
  ```
  [2026-01-25 10:30:50] INFO: Launching Claude CLI
  [2026-01-25 10:30:50] INFO: Command: claude --mcp-config {"mcpServers": {...}} --model opus
  [2026-01-25 10:30:50] INFO: MCP Config: {"mcpServers": {"docx-server": {"url": "http://127.0.0.1:8000/sse", "transport": "sse"}}}
  [2026-01-25 10:30:50] INFO: Extra Params: --model opus
  ```

### 4.4 Claude CLI 常用参数
需要支持的复选框选项（优先级从高到低）：
1. `--model` (选项: sonnet, opus, haiku)
2. `--agent` (选项: 自定义输入)
3. `--verbose` (布尔值)
4. `--debug` (布尔值)

---

## 5. 排除项

- **不支持的功能**:
  - 不支持编辑历史日志
  - 不支持日志搜索功能（可在后续版本添加）
  - 不支持自定义日志格式（使用固定格式）

- **不修改的部分**:
  - 不修改现有的日志轮转机制
  - 不修改现有的错误弹窗布局（仅添加复制按钮）

---

## 6. 下一步

✅ 在新会话中执行：
```bash
/clouditera:dev:spec-dev launcher-cli-logging --skip-requirements
```

或者，如果需要创建 worktree：
```bash
# 选项 1: 创建 worktree 并在当前会话继续
# （推荐）

# 选项 2: 创建 worktree，稍后执行
cd .worktrees/feature/launcher-cli-logging-{date}
/clouditera:dev:spec-dev launcher-cli-logging --skip-requirements

# 选项 3: 在主工作区继续
/clouditera:dev:spec-dev launcher-cli-logging --skip-requirements --no-worktree
```
