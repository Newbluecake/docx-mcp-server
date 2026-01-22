# 需求文档: File Logging

> **功能标识**: file-logging
> **复杂度**: standard
> **生成方式**: clarify
> **生成时间**: 2026-01-23T12:00:00Z

---

## 1. 概述

### 1.1 一句话描述

为 docx-mcp-server 添加日志文件保存功能，支持自动轮转和灵活配置，便于问题排查和调试。

### 1.2 核心价值

**解决的问题**：
- 当前日志仅输出到控制台，服务器重启或关闭后日志丢失
- 长时间运行的服务器无法回溯历史日志
- 问题排查时需要重现错误才能看到日志

**带来的价值**：
- 持久化日志记录，支持事后分析和问题排查
- 自动轮转机制，防止日志文件无限增长
- 灵活的配置选项，适应不同部署环境
- 双路输出（控制台+文件），兼顾实时查看和持久化存储

### 1.3 目标用户

- **主要用户**：docx-mcp-server 的开发者和运维人员，需要排查问题和分析系统行为
- **次要用户**：使用 docx-mcp-server 的集成方，需要监控服务运行状态

---

## 2. 需求与用户故事

### 2.1 需求清单

| ID | 需求点 | 优先级 | 用户故事 |
|----|--------|--------|----------|
| R-001 | 文件日志输出 | P0 | As a developer, I want logs to be saved to files, so that I can review them after the server restarts |
| R-002 | 自动轮转机制 | P0 | As an operator, I want log files to rotate automatically, so that disk space is not exhausted |
| R-003 | 双路输出 | P0 | As a developer, I want logs to output to both console and file, so that I can see real-time logs while debugging |
| R-004 | 命令行配置 | P0 | As an operator, I want to configure logging via CLI arguments, so that I can customize settings without code changes |
| R-005 | 日志级别控制 | P1 | As a developer, I want to control log levels, so that I can filter out noise in production |
| R-006 | 可配置路径 | P1 | As an operator, I want to specify log file location, so that I can comply with deployment requirements |

### 2.2 验收标准

#### R-001: 文件日志输出
- **WHEN** 服务器启动时, **THEN** 系统 **SHALL** 在指定目录创建日志文件
- **WHEN** 日志事件发生时, **THEN** 系统 **SHALL** 将日志同时写入控制台和文件
- **WHEN** 日志级别为 INFO 或更高时, **THEN** 系统 **SHALL** 记录到文件

#### R-002: 自动轮转机制
- **WHEN** 日志文件大小达到 10MB 时, **THEN** 系统 **SHALL** 自动创建新文件并归档旧文件
- **WHEN** 归档文件数量超过 5 个时, **THEN** 系统 **SHALL** 删除最旧的文件
- **WHEN** 轮转发生时, **THEN** 系统 **SHALL** 在文件名中添加时间戳或序号

#### R-003: 双路输出
- **WHEN** 服务器运行时, **THEN** 系统 **SHALL** 同时输出日志到控制台和文件
- **WHEN** 控制台日志失败时, **THEN** 系统 **SHALL** 仍然写入文件
- **WHEN** 文件日志失败时, **THEN** 系统 **SHALL** 仍然输出到控制台并记录错误

#### R-004: 命令行配置
- **WHEN** 使用 `--log-file` 参数时, **THEN** 系统 **SHALL** 启用文件日志
- **WHEN** 使用 `--no-log-file` 参数时, **THEN** 系统 **SHALL** 禁用文件日志
- **WHEN** 使用 `--log-dir` 参数时, **THEN** 系统 **SHALL** 使用指定的日志目录
- **WHEN** 未指定参数时, **THEN** 系统 **SHALL** 使用默认配置（启用文件日志，默认目录）

#### R-005: 日志级别控制
- **WHEN** 使用 `--log-level` 参数时, **THEN** 系统 **SHALL** 只记录指定级别及以上的日志
- **WHEN** 未指定日志级别时, **THEN** 系统 **SHALL** 使用 INFO 级别

#### R-006: 可配置路径
- **WHEN** 指定的日志目录不存在时, **THEN** 系统 **SHALL** 自动创建目录
- **WHEN** 日志目录无写权限时, **THEN** 系统 **SHALL** 输出错误并降级到控制台日志
- **WHEN** 使用相对路径时, **THEN** 系统 **SHALL** 相对于项目根目录解析

---

## 3. 功能验收清单

| ID | 功能点 | 验收步骤 | 优先级 | 关联需求 | 通过 |
|----|--------|----------|--------|----------|------|
| F-001 | 基本文件日志 | 1. 启动服务器 2. 检查日志目录是否生成文件 3. 触发操作 4. 检查日志内容 | P0 | R-001 | ☐ |
| F-002 | 双路输出验证 | 1. 启动服务器 2. 触发日志事件 3. 同时检查控制台和文件输出 | P0 | R-003 | ☐ |
| F-003 | 轮转机制 | 1. 生成大量日志（>10MB）2. 检查是否生成新文件 3. 检查旧文件是否保留 4. 检查最多保留 5 个文件 | P0 | R-002 | ☐ |
| F-004 | 禁用文件日志 | 1. 使用 `--no-log-file` 启动 2. 检查是否只输出到控制台 | P0 | R-004 | ☐ |
| F-005 | 自定义日志路径 | 1. 使用 `--log-dir /custom/path` 启动 2. 检查日志文件是否在指定路径 | P1 | R-006 | ☐ |
| F-006 | 日志级别过滤 | 1. 使用 `--log-level WARNING` 启动 2. 检查 INFO 日志是否被过滤 | P1 | R-005 | ☐ |
| F-007 | 目录自动创建 | 1. 指定不存在的目录 2. 启动服务器 3. 检查目录是否自动创建 | P1 | R-006 | ☐ |
| F-008 | 权限降级 | 1. 指定无写权限的目录 2. 启动服务器 3. 检查是否降级到控制台并有错误提示 | P2 | R-006 | ☐ |

---

## 4. 技术约束

### 4.1 技术栈

**编程语言**: Python 3.x（项目现有语言）

**日志库**:
- 使用 Python 标准库 `logging` 模块
- 使用 `logging.handlers.RotatingFileHandler` 实现轮转

**依赖**: 无需新增外部依赖

### 4.2 集成点

**修改的模块**:
- 日志配置模块（可能需要新建或修改现有配置）
- 服务器启动脚本（添加命令行参数解析）

**影响的组件**:
- 所有使用 logger 的模块（无需修改，通过配置自动生效）

### 4.3 配置参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--log-file` / `--no-log-file` | boolean | True | 是否启用文件日志 |
| `--log-dir` | string | `./logs` | 日志文件目录 |
| `--log-level` | string | `INFO` | 日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）|
| `--log-max-bytes` | int | 10485760 (10MB) | 单个日志文件最大大小 |
| `--log-backup-count` | int | 5 | 保留的历史日志文件数量 |

### 4.4 文件命名规范

- 主日志文件: `docx-mcp-server.log`
- 轮转文件: `docx-mcp-server.log.1`, `docx-mcp-server.log.2`, ... `docx-mcp-server.log.5`

### 4.5 日志格式

```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

示例输出:
```
2026-01-23 12:00:00,123 - docx_mcp_server.session - INFO - Session abc-123 created
2026-01-23 12:00:01,456 - docx_mcp_server.tools - ERROR - Failed to create paragraph: Invalid position
```

---

## 5. 排除项

- ❌ **日志压缩**: 轮转的日志文件不进行自动压缩（可在未来版本添加）
- ❌ **远程日志**: 不支持将日志发送到远程日志服务器（Syslog、CloudWatch 等）
- ❌ **日志搜索**: 不提供内置的日志搜索和分析功能
- ❌ **结构化日志**: 不支持 JSON 格式的结构化日志（当前版本使用文本格式）
- ❌ **日志加密**: 日志文件不进行加密存储
- ❌ **实时监控**: 不提供日志实时监控和告警功能

---

## 6. 非功能性需求

### 6.1 性能要求

- 日志写入不应显著影响服务器性能（延迟 < 1ms）
- 轮转操作应在后台执行，不阻塞主线程

### 6.2 兼容性

- 支持 Linux、macOS、Windows 三大平台
- 日志文件路径处理需考虑跨平台兼容性

### 6.3 可维护性

- 日志配置应集中管理，便于未来扩展
- 日志格式应统一，便于解析和分析

---

## 7. 下一步

✅ **需求已澄清，准备进入设计阶段**

推荐操作：

### 选项 1: 创建 worktree 并继续（推荐）
在隔离的工作区中执行 spec-dev，避免污染主分支。

### 选项 2: 创建 worktree，稍后执行
创建 worktree 后手动切换并执行：
```bash
cd .worktrees/feature/file-logging-{date}
/clouditera:dev:spec-dev file-logging --skip-requirements
```

### 选项 3: 在主工作区继续
不创建 worktree，直接在当前会话执行：
```bash
/clouditera:dev:spec-dev file-logging --skip-requirements --no-worktree
```

---

**文档版本**: v1
**最后更新**: 2026-01-23
