---
feature: launcher-command-display
complexity: standard
generated_by: clarify
generated_at: 2026-01-26T05:30:00Z
version: 1
---

# 需求文档: Launcher Command Display

> **功能标识**: launcher-command-display
> **复杂度**: standard
> **生成方式**: clarify
> **生成时间**: 2026-01-26T05:30:00Z

## 1. 概述

### 1.1 一句话描述

将 Launcher 的 "Launch Claude" 自动启动功能改为显示可复制的启动命令，让用户手动执行。

### 1.2 核心价值

- **提高可靠性**：避免自动启动失败（如 WinError 2）的问题
- **增强灵活性**：用户可以在任意终端环境中执行命令
- **简化维护**：移除复杂的进程启动和错误处理逻辑
- **提升透明度**：用户清楚看到执行的完整命令

### 1.3 目标用户

- **主要用户**：使用 docx-mcp-server launcher 的开发者
- **次要用户**：需要在特定终端环境启动 Claude 的用户

---

## 2. 需求与用户故事

### 2.1 需求清单

| ID | 需求点 | 优先级 | 用户故事 |
|----|--------|--------|----------|
| R-001 | 移除自动启动功能 | P0 | As a user, I want to see the command instead of auto-launching, so that I can execute it in my preferred terminal |
| R-002 | 显示完整启动命令 | P0 | As a user, I want to see the complete command with all parameters, so that I know exactly what will be executed |
| R-003 | 一键复制命令 | P0 | As a user, I want to copy the command with one click, so that I can paste it into my terminal quickly |
| R-004 | 实时命令更新 | P1 | As a user, I want the command to update automatically when I change settings, so that I always see the current command |
| R-005 | 简化 CLI 参数配置 | P1 | As a user, I want a simpler parameter configuration, so that the interface is less cluttered |

### 2.2 验收标准

#### R-001: 移除自动启动功能
- **WHEN** 用户点击原 "Launch Claude" 按钮位置, **THEN** 系统 **SHALL NOT** 启动 Claude 进程
- **WHEN** 用户查看 Integration Section, **THEN** 系统 **SHALL** 显示命令框而非启动按钮

#### R-002: 显示完整启动命令
- **WHEN** 服务器配置完成, **THEN** 系统 **SHALL** 显示包含 MCP 配置的完整 claude 命令
- **WHEN** 命令包含 JSON 配置, **THEN** 系统 **SHALL** 正确转义特殊字符
- **WHEN** 在 Windows 平台, **THEN** 系统 **SHALL** 显示 `cmd.exe /c` 前缀

#### R-003: 一键复制命令
- **WHEN** 用户点击复制按钮, **THEN** 系统 **SHALL** 将完整命令复制到剪贴板
- **WHEN** 复制成功, **THEN** 系统 **SHALL** 显示视觉反馈（如按钮文字变为 "Copied!"）
- **WHEN** 复制失败, **THEN** 系统 **SHALL** 显示错误提示

#### R-004: 实时命令更新
- **WHEN** 用户修改端口号, **THEN** 系统 **SHALL** 立即更新命令中的端口参数
- **WHEN** 用户修改主机地址, **THEN** 系统 **SHALL** 立即更新命令中的 URL
- **WHEN** 用户修改 CLI 参数, **THEN** 系统 **SHALL** 立即更新命令中的参数部分

#### R-005: 简化 CLI 参数配置
- **WHEN** 用户查看 Integration Section, **THEN** 系统 **SHALL NOT** 显示 --model、--agent、--verbose、--debug 配置项
- **WHEN** 用户查看 CLI 参数输入框, **THEN** 系统 **SHALL** 提供 --dangerously-skip-permission 作为示例
- **WHEN** 用户输入自定义参数, **THEN** 系统 **SHALL** 将其附加到生成的命令中

---

## 3. 功能验收清单

| ID | 功能点 | 验收步骤 | 优先级 | 关联需求 | 通过 |
|----|--------|----------|--------|----------|------|
| F-001 | 命令框显示 | 1. 启动 launcher 2. 查看 Integration Section 3. 确认显示只读命令框 | P0 | R-001, R-002 | ☐ |
| F-002 | 复制按钮功能 | 1. 点击复制按钮 2. 粘贴到终端 3. 确认命令完整 | P0 | R-003 | ☐ |
| F-003 | 命令格式正确 | 1. 检查命令包含 claude --mcp-config 2. 检查 JSON 格式正确 3. Windows 上检查 cmd.exe 前缀 | P0 | R-002 | ☐ |
| F-004 | 实时更新 | 1. 修改端口号 2. 确认命令立即更新 3. 修改 CLI 参数 4. 确认命令立即更新 | P1 | R-004 | ☐ |
| F-005 | 简化配置 | 1. 查看 Integration Section 2. 确认移除 model/agent/verbose/debug 配置 3. 确认保留自定义参数输入框 | P1 | R-005 | ☐ |
| F-006 | 复制反馈 | 1. 点击复制按钮 2. 确认按钮文字变为 "Copied!" 3. 2秒后恢复原文字 | P1 | R-003 | ☐ |

---

## 4. 技术约束

### 4.1 技术栈

- **GUI 框架**: PyQt6
- **剪贴板操作**: PyQt6.QtWidgets.QApplication.clipboard()
- **命令生成**: 复用现有 `cli_launcher.py` 的 `build_command()` 方法
- **平台检测**: `platform.system()` 判断 Windows/Linux/Mac

### 4.2 集成点

**修改的模块**:
- `src/docx_server_launcher/gui/main_window.py`: UI 布局和事件处理
- `src/docx_server_launcher/core/cli_launcher.py`: 移除启动逻辑，保留命令生成

**保留的功能**:
- MCP 配置生成逻辑
- 命令参数验证逻辑
- 平台特定的命令格式化（Windows cmd.exe 包装）

### 4.3 UI 组件

**新增组件**:
- `QLineEdit` (只读): 显示完整命令
- `QPushButton`: 复制按钮，文字为 "Copy Command"

**移除组件**:
- `QPushButton` "Launch Claude": 原启动按钮
- `QGroupBox` "CLI Parameters": 包含 --model、--agent、--verbose、--debug 的配置组
- 相关的 `QCheckBox` 和 `QComboBox` 控件

**保留组件**:
- `QLineEdit` "Additional Parameters": 自定义参数输入框
- `QLabel` "Hint": 提示文字（更新为新的示例）

---

## 5. UI 设计

### 5.1 布局变更

**原布局**:
```
Integration Section
├── CLI Parameters Group
│   ├── --model [checkbox] [combo]
│   ├── --agent [checkbox] [input]
│   └── --verbose [checkbox] --debug [checkbox]
├── Hint Label
├── Additional Parameters [input]
└── Launch Claude [button]
```

**新布局**:
```
Integration Section
├── Command Display [readonly input] [Copy Command button]
├── Hint Label (updated)
└── Additional Parameters [input]
```

### 5.2 命令格式示例

**Linux/Mac**:
```bash
claude --mcp-config {"mcpServers":{"docx-server":{"url":"http://127.0.0.1:8000/sse","transport":"sse"}}} --dangerously-skip-permission
```

**Windows**:
```cmd
cmd.exe /c claude --mcp-config {"mcpServers":{"docx-server":{"url":"http://127.0.0.1:8000/sse","transport":"sse"}}} --dangerously-skip-permission
```

---

## 6. 排除项

- **不做**：保留自动启动功能作为可选项
  - **原因**：简化功能，避免维护两套逻辑
- **不做**：支持多种命令格式（如 PowerShell、Bash）
  - **原因**：当前只支持 cmd.exe（Windows）和默认 shell（Linux/Mac）
- **不做**：命令历史记录
  - **原因**：命令是实时生成的，无需历史记录
- **不做**：命令编辑功能
  - **原因**：命令框只读，用户可以复制后手动编辑

---

## 7. 实施建议

### 7.1 实施步骤

1. **Phase 1: 移除启动逻辑**
   - 移除 `cli_launcher.py` 中的 `launch()` 方法调用
   - 移除进程管理相关代码
   - 保留 `build_command()` 方法

2. **Phase 2: UI 重构**
   - 移除 CLI Parameters Group 及相关控件
   - 添加命令显示框和复制按钮
   - 更新布局和样式

3. **Phase 3: 实时更新机制**
   - 连接配置变更信号到命令更新槽函数
   - 实现命令生成和显示逻辑

4. **Phase 4: 复制功能**
   - 实现复制到剪贴板功能
   - 添加视觉反馈（按钮文字变化）

5. **Phase 5: 测试和文档**
   - 单元测试：命令生成逻辑
   - GUI 测试：复制功能和实时更新
   - 更新用户文档

### 7.2 风险点

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| JSON 转义问题 | 命令在终端执行失败 | 使用 `json.dumps()` 确保正确转义 |
| 剪贴板权限 | 复制功能失败 | 捕获异常并显示错误提示 |
| 跨平台兼容性 | Windows/Linux/Mac 命令格式不同 | 使用 `platform.system()` 判断并生成对应格式 |

---

## 8. 下一步

✅ 需求已澄清，可以开始技术设计和实施。

**推荐执行**:
```bash
/clouditera:dev:spec-dev launcher-command-display --skip-requirements
```

或者在新会话中执行：
```bash
cd .worktrees/feature/launcher-command-display-{date}
/clouditera:dev:spec-dev launcher-command-display --skip-requirements
```

---

**文档版本**: v1
**最后更新**: 2026-01-26
**作者**: Claude Sonnet 4.5 (via clarify)
