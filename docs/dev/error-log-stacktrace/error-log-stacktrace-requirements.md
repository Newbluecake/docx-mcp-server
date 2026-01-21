---
feature: error-log-stacktrace
complexity: standard
generated_by: clarify
generated_at: 2026-01-21T14:30:00Z
version: 1
---

# 需求文档: Error 日志调用栈增强

> **功能标识**: error-log-stacktrace
> **复杂度**: standard
> **生成方式**: clarify
> **生成时间**: 2026-01-21

## 1. 概述

### 1.1 一句话描述
为所有 error 级别的日志添加完整的调用栈信息，便于快速定位和调试生产环境问题。

### 1.2 核心价值
- **快速定位问题**：通过调用栈快速找到错误发生的代码路径
- **提升调试效率**：减少在生产环境中重现问题的时间
- **改善可观测性**：增强日志的诊断价值，便于问题分析

### 1.3 目标用户
- **主要用户**：开发者（调试和维护代码）
- **次要用户**：运维人员（生产环境问题排查）

---

## 2. 需求与用户故事

### 2.1 需求清单

| ID | 需求点 | 优先级 | 用户故事 |
|----|--------|--------|----------|
| R-001 | 自动添加调用栈 | P0 | 作为开发者，我希望所有 error 日志自动包含调用栈，以便快速定位问题源头 |
| R-002 | 异常场景增强 | P0 | 作为开发者，我希望在捕获异常时使用 logger.exception()，以便同时记录异常信息和调用栈 |
| R-003 | 集中式配置 | P1 | 作为维护者，我希望通过自定义 logging 配置统一管理，而非手动修改每个日志调用 |
| R-004 | 向后兼容 | P1 | 作为用户，我希望现有日志格式保持兼容，只是增加调用栈信息 |

### 2.2 验收标准

#### R-001: 自动添加调用栈
- **WHEN** 任何模块调用 `logger.error()`，**THEN** 日志输出 **SHALL** 包含完整的调用栈信息
- **WHEN** 查看日志文件，**THEN** 调用栈 **SHALL** 清晰显示函数调用路径和行号

#### R-002: 异常场景增强
- **WHEN** 在 `except` 块中记录错误，**THEN** 代码 **SHALL** 使用 `logger.exception()` 而非 `logger.error()`
- **WHEN** 使用 `logger.exception()`，**THEN** 日志 **SHALL** 同时包含异常类型、消息和完整 traceback

#### R-003: 集中式配置
- **WHEN** 需要修改调用栈格式，**THEN** 只需修改 logging 配置文件，**SHALL NOT** 修改业务代码
- **WHEN** 新增模块使用 `logger.error()`，**THEN** 自动继承调用栈配置

#### R-004: 向后兼容
- **WHEN** 现有日志解析工具读取日志，**THEN** **SHALL** 正常工作，调用栈作为额外信息附加

---

## 3. 功能验收清单

| ID | 功能点 | 验收步骤 | 优先级 | 关联需求 | 通过 |
|----|--------|----------|--------|----------|------|
| F-001 | 自定义 Formatter | 1. 创建自定义 StackTraceFormatter 2. 配置 exc_info=True 或 stack_info=True 3. 验证日志包含调用栈 | P0 | R-001, R-003 | ☐ |
| F-002 | 更新 logging 配置 | 1. 修改 logging 配置使用自定义 Formatter 2. 确保所有 logger 继承配置 | P0 | R-001, R-003 | ☐ |
| F-003 | 替换 logger.error() | 1. 在所有 except 块中使用 logger.exception() 2. 验证异常信息和调用栈都被记录 | P0 | R-002 | ☐ |
| F-004 | 单元测试 | 1. 编写测试验证 error 日志包含调用栈 2. 测试 logger.exception() 正确记录异常 | P0 | R-001, R-002 | ☐ |
| F-005 | 向后兼容验证 | 1. 运行现有测试套件 2. 验证日志格式兼容 | P1 | R-004 | ☐ |

---

## 4. 技术约束

### 4.1 技术栈
- **语言**: Python 3.10+
- **日志框架**: Python 标准库 `logging`
- **配置方式**: 自定义 `logging.Formatter` 或 `logging.Handler`

### 4.2 实现方案

#### 方案 1: 自定义 Formatter（推荐）

创建自定义 Formatter，自动为 error 级别添加调用栈：

```python
import logging
import traceback

class StackTraceFormatter(logging.Formatter):
    def format(self, record):
        # 调用父类格式化
        result = super().format(record)

        # 如果是 ERROR 级别且没有异常信息，添加调用栈
        if record.levelno >= logging.ERROR:
            if not record.exc_info:
                # 添加当前调用栈
                stack = ''.join(traceback.format_stack())
                result += f'\nCall Stack:\n{stack}'

        return result
```

#### 方案 2: 使用 logger.exception()

在所有 `except` 块中使用 `logger.exception()` 替代 `logger.error()`：

```python
# 修改前
try:
    session = self.sessions[session_id]
except KeyError:
    logger.error(f"Session {session_id} not found")

# 修改后
try:
    session = self.sessions[session_id]
except KeyError:
    logger.exception(f"Session {session_id} not found")
```

### 4.3 集成点
- **修改文件**:
  - 新增: `src/docx_mcp_server/utils/logging_config.py`（自定义 Formatter）
  - 修改: `src/docx_mcp_server/server.py`（应用 logging 配置）
  - 修改: 所有模块中的 `except` 块（使用 logger.exception()）
- **影响范围**: 所有使用 `logger.error()` 的模块
- **向后兼容**: 日志格式保持兼容，调用栈作为额外信息附加

### 4.4 性能考虑
- **调用栈开销**: `traceback.format_stack()` 有一定性能开销，但仅在 error 级别触发
- **日志大小**: 调用栈会增加日志文件大小，建议配置日志轮转

---

## 5. 排除项

- **不修改**: info/debug/warning 级别的日志（保持轻量）
- **不添加**: 自定义的调用栈过滤或简化逻辑（使用完整调用栈）
- **不改变**: 现有日志的输出目标（仍然输出到 stderr）
- **不实现**: 调用栈的可视化或格式化工具（使用原始文本格式）

---

## 6. 实施建议

### 6.1 分阶段实施

1. **阶段 1**: 创建自定义 Formatter 和 logging 配置（1 小时）
2. **阶段 2**: 更新所有 `except` 块使用 `logger.exception()`（2 小时）
3. **阶段 3**: 编写单元测试验证调用栈（1 小时）
4. **阶段 4**: 运行完整测试套件，确保向后兼容（0.5 小时）

**总工作量**: 4-5 小时

### 6.2 质量检查
- 所有 error 日志包含调用栈
- 所有 `except` 块使用 `logger.exception()`
- 测试覆盖率 ≥85%
- 现有测试全部通过

---

## 7. 下一步

✅ 在新会话中执行：
```bash
/clouditera:dev:spec-dev error-log-stacktrace --skip-requirements
```

或者，如果希望在当前会话继续：

<function_calls>
<invoke name="AskUserQuestion">
<parameter name="questions">[{"header": "下一步", "multiSelect": false, "options": [{"description": "创建隔离工作区，在当前会话继续执行 spec-dev", "label": "🔧 创建 worktree 并继续（推荐）"}, {"description": "创建隔离工作区，稍后手动执行", "label": "📂 创建 worktree，稍后执行"}, {"description": "不创建 worktree，在当前会话执行 spec-dev", "label": "📝 在主工作区继续"}], "question": "需求已澄清，下一步操作？"}]