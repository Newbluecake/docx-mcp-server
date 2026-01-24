---
feature: launcher-cli-mode
complexity: standard
generated_by: clarify
generated_at: 2026-01-24T10:30:00Z
version: 1
---

# 需求文档: GUI Launcher CLI 启动模式

> **功能标识**: launcher-cli-mode
> **复杂度**: standard
> **生成方式**: clarify
> **生成时间**: 2026-01-24T10:30:00Z

## 1. 概述

### 1.1 一句话描述
修改 docx-server-launcher GUI 工具，从"注入配置文件"模式改为"直接启动 Claude CLI"模式，通过命令行参数传递 MCP 配置。

### 1.2 核心价值
- **简化工作流**：用户无需手动修改 Claude Desktop 配置文件，点击按钮即可启动配置好的 Claude CLI
- **灵活性提升**：支持用户自定义 Claude CLI 参数（如 --model, --agent 等），满足不同使用场景
- **降低错误率**：避免手动编辑配置文件可能导致的 JSON 格式错误
- **即时生效**：配置更改立即生效，无需重启 Claude Desktop

### 1.3 目标用户
- **主要用户**：docx-mcp-server 的开发者和测试人员，需要频繁切换 MCP 配置进行测试
- **次要用户**：希望快速体验 docx-mcp-server 功能的普通用户

---

## 2. 需求与用户故事

### 2.1 需求清单

| ID | 需求点 | 优先级 | 用户故事 |
|----|--------|--------|----------|
| R-001 | CLI 启动功能 | P0 | As a 开发者, I want 点击按钮直接启动 Claude CLI, so that 无需手动配置文件 |
| R-002 | 自定义 CLI 参数 | P0 | As a 用户, I want 添加额外的 Claude CLI 参数, so that 可以指定模型、Agent 等选项 |
| R-003 | Claude CLI 检测 | P0 | As a 用户, I want 系统检测 Claude CLI 是否安装, so that 在未安装时获得明确提示 |
| R-004 | 启动日志记录 | P1 | As a 开发者, I want 查看启动日志, so that 可以排查启动失败的原因 |
| R-005 | 保留原有配置表单 | P0 | As a 用户, I want 保留传输方式、端口等配置项, so that 可以灵活配置 MCP 服务器 |

### 2.2 验收标准

#### R-001: CLI 启动功能
- **WHEN** 用户点击"启动 Claude"按钮, **THEN** 系统 **SHALL**:
  1. 生成 MCP 配置 JSON 字符串（包含 docx-server 配置）
  2. 构建 `claude --mcp-config '{...}'` 命令
  3. 启动 Claude CLI 进程
  4. Claude CLI 进入交互式会话

#### R-002: 自定义 CLI 参数
- **WHEN** 用户在"额外参数"输入框中填写 `--model opus --agent reviewer`, **THEN** 系统 **SHALL**:
  1. 解析用户输入的参数
  2. 将参数附加到 `claude` 命令中
  3. 最终命令格式为: `claude --mcp-config '{...}' --model opus --agent reviewer`

#### R-003: Claude CLI 检测
- **WHEN** 用户点击"启动 Claude"按钮且 Claude CLI 未安装, **THEN** 系统 **SHALL**:
  1. 显示错误对话框："Claude CLI 未找到"
  2. 提供安装指引链接或命令
  3. 不执行启动操作

#### R-004: 启动日志记录
- **WHEN** 系统启动 Claude CLI, **THEN** 系统 **SHALL**:
  1. 记录启动时间、命令、MCP 配置到日志文件
  2. 日志文件路径: `~/.docx-launcher/launch.log`
  3. 记录 Claude CLI 的 stdout/stderr 输出（前 100 行）

#### R-005: 保留原有配置表单
- **WHEN** 用户打开 GUI, **THEN** 系统 **SHALL**:
  1. 显示原有的传输方式选择（STDIO/SSE/Streamable HTTP）
  2. 显示端口配置（仅 SSE/HTTP 模式）
  3. 显示工作目录配置
  4. 新增"额外 CLI 参数"输入框

---

## 3. 功能验收清单

| ID | 功能点 | 验收步骤 | 优先级 | 关联需求 | 通过 |
|----|--------|----------|--------|----------|------|
| F-001 | 按钮文本修改 | 1. 打开 GUI<br>2. 确认按钮文本为"启动 Claude"（原为"注入配置"） | P0 | R-001 | ☐ |
| F-002 | 新增参数输入框 | 1. 打开 GUI<br>2. 确认存在"额外 CLI 参数"输入框<br>3. 输入 `--model opus`<br>4. 确认输入被保存 | P0 | R-002 | ☐ |
| F-003 | CLI 检测功能 | 1. 临时重命名 `claude` 命令<br>2. 点击"启动 Claude"<br>3. 确认显示错误提示 | P0 | R-003 | ☐ |
| F-004 | 成功启动 Claude | 1. 配置 SSE 模式，端口 8000<br>2. 点击"启动 Claude"<br>3. 确认 Claude CLI 启动<br>4. 在 Claude 中执行 MCP 工具调用 | P0 | R-001 | ☐ |
| F-005 | 自定义参数生效 | 1. 在"额外参数"中输入 `--model haiku`<br>2. 点击"启动 Claude"<br>3. 在 Claude 中确认使用的是 Haiku 模型 | P0 | R-002 | ☐ |
| F-006 | 日志文件生成 | 1. 点击"启动 Claude"<br>2. 检查 `~/.docx-launcher/launch.log` 存在<br>3. 确认日志包含启动时间、命令、MCP 配置 | P1 | R-004 | ☐ |
| F-007 | 配置表单保留 | 1. 打开 GUI<br>2. 确认传输方式、端口、工作目录配置项存在<br>3. 修改配置并保存<br>4. 重新打开 GUI，确认配置被保留 | P0 | R-005 | ☐ |

---

## 4. 技术约束

### 4.1 技术栈
- **GUI 框架**: PyQt6（保持不变）
- **进程管理**: Python `subprocess` 模块
- **配置存储**: QSettings（保持不变）
- **日志记录**: Python `logging` 模块

### 4.2 集成点
- **Claude CLI**: 通过 `subprocess.Popen` 启动，传递 `--mcp-config` 参数
- **MCP 配置**: 生成符合 MCP 规范的 JSON 配置字符串
- **日志文件**: 写入 `~/.docx-launcher/launch.log`

### 4.3 关键技术决策

#### 4.3.1 MCP 配置传递方式
**选择**: 使用 `--mcp-config` 参数传递 JSON 字符串

**原因**:
- Claude CLI 已支持此参数（见 `claude --help`）
- 无需创建临时文件，减少文件系统操作
- 配置即时生效，无需重启 Claude Desktop

**格式示例**:
```bash
claude --mcp-config '{"mcpServers":{"docx-server":{"url":"http://127.0.0.1:8000/sse","transport":"sse"}}}'
```

#### 4.3.2 Claude CLI 检测方式
**选择**: 使用 `shutil.which("claude")` 检测

**原因**:
- 跨平台兼容（Windows/Linux/macOS）
- 自动搜索 PATH 环境变量
- 返回可执行文件的完整路径

#### 4.3.3 进程启动方式
**选择**: 使用 `subprocess.Popen` 而非 `subprocess.run`

**原因**:
- 需要启动后台进程，不阻塞 GUI
- 可以捕获 stdout/stderr 用于日志记录
- 支持进程管理（如需要时可终止进程）

### 4.4 性能要求
- CLI 检测响应时间 < 100ms
- 启动 Claude CLI 响应时间 < 2s
- 日志文件大小限制 < 10MB（自动轮转）

---

## 5. 界面变更

### 5.1 修改的 UI 元素

| 元素 | 原有 | 修改后 |
|------|------|--------|
| 主按钮 | "注入配置到 Claude Desktop" | "启动 Claude" |
| 配置路径输入框 | 显示 | **移除**（不再需要配置文件路径） |
| 配置路径浏览按钮 | 显示 | **移除** |

### 5.2 新增的 UI 元素

| 元素 | 类型 | 位置 | 说明 |
|------|------|------|------|
| 额外 CLI 参数输入框 | QLineEdit | 配置组底部 | 允许用户输入额外的 Claude CLI 参数 |
| 参数说明标签 | QLabel | 输入框上方 | 提示用户可用参数（如 --model, --agent） |
| 查看日志按钮 | QPushButton | 状态栏 | 点击打开日志文件 |

### 5.3 UI 布局示意

```
┌─────────────────────────────────────────┐
│  Docx MCP Server Launcher               │
├─────────────────────────────────────────┤
│  [配置]                                  │
│  工作目录: [___________] [浏览] [历史▼] │
│  □ 允许局域网访问    语言: [中文▼]      │
│  端口: [8000]                            │
│                                          │
│  额外 CLI 参数 (可选):                   │
│  提示: 如 --model opus --agent reviewer  │
│  [_________________________________]     │
│                                          │
│  [启动 Claude]                           │
├─────────────────────────────────────────┤
│  [日志输出区域]                          │
│                                          │
├─────────────────────────────────────────┤
│  状态: 就绪          [查看日志]          │
└─────────────────────────────────────────┘
```

---

## 6. 数据模型

### 6.1 MCP 配置 JSON 结构

```json
{
  "mcpServers": {
    "docx-server": {
      "url": "http://127.0.0.1:8000/sse",
      "transport": "sse"
    }
  }
}
```

**字段说明**:
- `url`: MCP 服务器的 URL，根据传输方式和端口动态生成
- `transport`: 传输方式，可选值: `sse`, `stdio`, `streamable-http`

### 6.2 启动日志格式

```
[2026-01-24 10:30:00] INFO: Starting Claude CLI
[2026-01-24 10:30:00] INFO: Command: claude --mcp-config '{"mcpServers":{"docx-server":{"url":"http://127.0.0.1:8000/sse","transport":"sse"}}}' --model opus
[2026-01-24 10:30:00] INFO: MCP Config: {"mcpServers":{"docx-server":{"url":"http://127.0.0.1:8000/sse","transport":"sse"}}}
[2026-01-24 10:30:01] INFO: Claude CLI started successfully (PID: 12345)
[2026-01-24 10:30:01] INFO: Claude CLI stdout: [前 100 行输出]
```

---

## 7. 错误处理

### 7.1 错误场景与处理

| 错误场景 | 检测方式 | 用户提示 | 系统行为 |
|---------|---------|---------|---------|
| Claude CLI 未安装 | `shutil.which("claude")` 返回 None | "Claude CLI 未找到，请先安装 Claude CLI" | 显示错误对话框，提供安装链接 |
| MCP 服务器未启动 | 启动 Claude 后无法连接 | "MCP 服务器连接失败，请先启动服务器" | 记录到日志，提示用户检查服务器状态 |
| 参数格式错误 | 解析用户输入的参数失败 | "参数格式错误，请检查输入" | 显示错误对话框，不执行启动 |
| 日志文件写入失败 | 文件权限或磁盘空间不足 | "日志记录失败，但 Claude 已启动" | 显示警告，继续启动 Claude |

### 7.2 安装指引

**Claude CLI 未找到时的提示内容**:

```
Claude CLI 未找到

请先安装 Claude CLI：

方法 1: 使用 npm（推荐）
  npm install -g @anthropic-ai/claude-code

方法 2: 使用 pip
  pip install claude-code

安装完成后，请重启本工具。

[确定]  [查看文档]
```

---

## 8. 排除项

以下功能**不在本次需求范围内**：

- ❌ **不修改配置文件注入功能的代码**：完全移除 `ConfigInjector` 类及相关调用
- ❌ **不支持同时启动多个 Claude 实例**：每次只启动一个 Claude CLI 进程
- ❌ **不提供进程管理功能**：不支持在 GUI 中停止/重启 Claude CLI
- ❌ **不支持 STDIO 模式的 CLI 启动**：STDIO 模式下 Claude CLI 无法直接连接，仍需配置文件
- ❌ **不重新设计 GUI 界面**：保持现有布局和风格，只做必要的元素调整
- ❌ **不支持配置文件导入/导出**：用户配置仅通过 QSettings 保存

---

## 9. 下一步

✅ 在当前会话中执行：
```bash
/clouditera:dev:spec-dev launcher-cli-mode --skip-requirements --no-worktree
```

这将生成：
- `launcher-cli-mode-design.md`（技术设计文档）
- `launcher-cli-mode-tasks.md`（任务分解）
- 实施代码（TDD 流程）

---

**文档版本**: v1.0
**最后更新**: 2026-01-24
