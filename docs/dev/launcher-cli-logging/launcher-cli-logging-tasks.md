---
feature: launcher-cli-logging
complexity: standard
version: 1
generated_at: 2026-01-25T11:00:00Z
total_tasks: 12
parallel_groups: 3
---

# 任务拆分文档: Launcher CLI Logging Enhancement

> **功能标识**: launcher-cli-logging
> **复杂度**: standard
> **任务总数**: 12
> **并行分组**: 3

---

## 任务依赖关系图

```
Group 1 (基础设施)
├── T-001: 日志格式规范定义
└── T-002: QSettings 配置管理工具类

Group 2 (核心功能 - 可并行)
├── T-003: ServerManager 启动命令日志
├── T-004: CLILauncher 启动命令日志
└── T-005: MainWindow CLI 参数复选框 UI

Group 3 (增强功能 - 依赖 Group 2)
├── T-006: CLI 参数配置持久化
├── T-007: 错误弹窗复制按钮
├── T-008: 日志文件权限设置
└── T-009: 敏感信息过滤

Group 4 (测试 - 依赖 Group 3)
├── T-010: 单元测试
├── T-011: 集成测试
└── T-012: E2E 测试和文档更新
```

---

## 任务清单

### Group 1: 基础设施（2 个任务）

#### T-001: 日志格式规范定义

**优先级**: P0
**预估复杂度**: Simple
**依赖**: 无
**并行组**: 1

**描述**:
定义统一的日志格式规范，包括 MCP 服务器启动日志和 Claude CLI 启动日志的 JSON 结构。

**实施步骤**:
1. 在 `src/docx_server_launcher/core/` 创建 `log_formatter.py`
2. 定义 `format_mcp_command()` 函数
3. 定义 `format_cli_command()` 函数
4. 添加日志级别常量（INFO, ERROR 等）

**验收标准**:
- [ ] `format_mcp_command()` 返回正确的 JSON 格式
- [ ] `format_cli_command()` 返回正确的日志字符串
- [ ] 包含时间戳、级别、消息和数据字段
- [ ] 通过单元测试验证格式正确性

**涉及文件**:
- `src/docx_server_launcher/core/log_formatter.py` (新建)

---

#### T-002: QSettings 配置管理工具类

**优先级**: P0
**预估复杂度**: Simple
**依赖**: 无
**并行组**: 1

**描述**:
创建配置管理工具类，封装 QSettings 的读写操作，提供类型安全的接口。

**实施步骤**:
1. 在 `src/docx_server_launcher/core/` 创建 `config_manager.py`
2. 定义 `ConfigManager` 类
3. 实现 `save_cli_param()` 方法
4. 实现 `load_cli_param()` 方法
5. 实现 `get_all_cli_params()` 方法

**验收标准**:
- [ ] 支持保存和加载所有 CLI 参数类型（bool, str）
- [ ] 提供默认值回退机制
- [ ] 配置文件位置符合操作系统规范
- [ ] 通过单元测试验证读写正确性

**涉及文件**:
- `src/docx_server_launcher/core/config_manager.py` (新建)

---

### Group 2: 核心功能（3 个任务，可并行）

#### T-003: ServerManager 启动命令日志

**优先级**: P0
**预估复杂度**: Standard
**依赖**: T-001
**并行组**: 2

**描述**:
在 ServerManager 中添加 MCP 服务器启动命令日志记录功能。

**实施步骤**:
1. 修改 `src/docx_server_launcher/core/server_manager.py`
2. 在 `start_server()` 方法中添加日志记录
3. 使用 `log_formatter.format_mcp_command()` 格式化命令
4. 记录到 GUI 日志文件
5. 配置 MCP 服务器日志文件路径（通过环境变量或配置）

**验收标准**:
- [ ] 启动 MCP 服务器前记录完整命令
- [ ] 日志包含 command 和 args 字段
- [ ] 使用 INFO 级别
- [ ] GUI 日志文件包含启动命令
- [ ] MCP 服务器日志文件包含启动命令

**涉及文件**:
- `src/docx_server_launcher/core/server_manager.py` (修改)

---

#### T-004: CLILauncher 启动命令日志

**优先级**: P0
**预估复杂度**: Standard
**依赖**: T-001
**并行组**: 2

**描述**:
在 CLILauncher 中添加 Claude CLI 启动命令日志记录功能。

**实施步骤**:
1. 修改 `src/docx_server_launcher/core/cli_launcher.py`
2. 在 `launch_claude_cli()` 方法中添加日志记录
3. 使用 `log_formatter.format_cli_command()` 格式化命令
4. 记录完整命令字符串
5. 记录 MCP 配置 JSON
6. 记录额外参数

**验收标准**:
- [ ] 启动 Claude CLI 前记录完整命令
- [ ] 日志包含命令字符串、MCP 配置和额外参数
- [ ] 使用 INFO 级别
- [ ] GUI 日志文件包含所有信息

**涉及文件**:
- `src/docx_server_launcher/core/cli_launcher.py` (修改)

---

#### T-005: MainWindow CLI 参数复选框 UI

**优先级**: P1
**预估复杂度**: Standard
**依赖**: 无
**并行组**: 2

**描述**:
在 MainWindow 中添加 Claude CLI 参数复选框 UI 组件。

**实施步骤**:
1. 修改 `src/docx_server_launcher/gui/main_window.py`
2. 创建 `cli_params_group` QGroupBox
3. 添加 `--model` 复选框和下拉框（sonnet, opus, haiku）
4. 添加 `--agent` 复选框和输入框
5. 添加 `--verbose` 复选框
6. 添加 `--debug` 复选框
7. 布局调整，放置在 Claude CLI 启动按钮附近

**验收标准**:
- [ ] UI 包含所有 4 个参数选项
- [ ] 复选框和输入控件正确关联
- [ ] 布局美观，不影响现有 UI
- [ ] 可折叠的参数区域（可选）

**涉及文件**:
- `src/docx_server_launcher/gui/main_window.py` (修改)

---

### Group 3: 增强功能（4 个任务，依赖 Group 2）

#### T-006: CLI 参数配置持久化

**优先级**: P1
**预估复杂度**: Standard
**依赖**: T-002, T-005
**并行组**: 3

**描述**:
实现 CLI 参数的保存和加载功能，使用 ConfigManager 持久化用户选择。

**实施步骤**:
1. 修改 `src/docx_server_launcher/gui/main_window.py`
2. 实现 `save_cli_params()` 方法
3. 实现 `load_cli_params()` 方法
4. 在窗口关闭时自动保存
5. 在窗口初始化时自动加载
6. 连接复选框的 `stateChanged` 信号到保存方法

**验收标准**:
- [ ] 勾选参数后关闭 GUI，重启后参数选择被恢复
- [ ] 所有参数类型（bool, str）正确保存和加载
- [ ] 使用 ConfigManager 进行配置管理
- [ ] 首次启动时使用默认值

**涉及文件**:
- `src/docx_server_launcher/gui/main_window.py` (修改)

---

#### T-007: 错误弹窗复制按钮

**优先级**: P1
**预估复杂度**: Simple
**依赖**: T-005
**并行组**: 3

**描述**:
在错误弹窗中添加复制按钮，方便用户复制错误信息。

**实施步骤**:
1. 修改 `src/docx_server_launcher/gui/main_window.py`
2. 修改 `show_error_dialog()` 方法
3. 添加 "Copy" 按钮到 QMessageBox
4. 实现 `copy_to_clipboard()` 方法
5. 显示复制成功提示

**验收标准**:
- [ ] 错误弹窗包含 "Copy" 按钮
- [ ] 点击按钮后错误信息被复制到剪贴板
- [ ] 显示 "Copied" 提示
- [ ] 复制内容限制在 10KB 以内

**涉及文件**:
- `src/docx_server_launcher/gui/main_window.py` (修改)

---

#### T-008: 日志文件权限设置

**优先级**: P2
**预估复杂度**: Simple
**依赖**: T-003, T-004
**并行组**: 3

**描述**:
设置日志文件权限，确保仅当前用户可读写。

**实施步骤**:
1. 修改 `src/docx_server_launcher/core/server_manager.py`
2. 修改 `src/docx_server_launcher/core/cli_launcher.py`
3. 在创建日志文件后设置权限（chmod 600）
4. 使用 `os.chmod()` 或 `pathlib.Path.chmod()`

**验收标准**:
- [ ] 日志文件权限为 600（仅所有者可读写）
- [ ] 在 Linux/macOS 上验证权限正确
- [ ] 在 Windows 上使用等效的权限设置

**涉及文件**:
- `src/docx_server_launcher/core/server_manager.py` (修改)
- `src/docx_server_launcher/core/cli_launcher.py` (修改)

---

#### T-009: 敏感信息过滤

**优先级**: P2
**预估复杂度**: Simple
**依赖**: T-001
**并行组**: 3

**描述**:
在日志记录前过滤敏感信息，如完整文件路径、环境变量等。

**实施步骤**:
1. 修改 `src/docx_server_launcher/core/log_formatter.py`
2. 添加 `filter_sensitive_info()` 函数
3. 过滤完整文件路径（仅保留文件名）
4. 过滤环境变量值
5. 在 `format_mcp_command()` 和 `format_cli_command()` 中应用过滤

**验收标准**:
- [ ] 日志不包含完整文件路径
- [ ] 日志不包含敏感环境变量
- [ ] 过滤后的日志仍然可读和有用

**涉及文件**:
- `src/docx_server_launcher/core/log_formatter.py` (修改)

---

### Group 4: 测试和文档（3 个任务，依赖 Group 3）

#### T-010: 单元测试

**优先级**: P0
**预估复杂度**: Standard
**依赖**: T-001 到 T-009
**并行组**: 4

**描述**:
为新增和修改的模块编写单元测试。

**实施步骤**:
1. 创建 `tests/unit/test_log_formatter.py`
2. 创建 `tests/unit/test_config_manager.py`
3. 修改 `tests/unit/test_server_manager.py`
4. 修改 `tests/unit/test_cli_launcher.py`
5. 修改 `tests/unit/test_main_window.py`
6. 测试日志格式、配置管理、命令日志记录

**验收标准**:
- [ ] 所有新增模块有单元测试
- [ ] 测试覆盖率 > 80%
- [ ] 所有测试通过
- [ ] 使用 pytest 运行测试

**涉及文件**:
- `tests/unit/test_log_formatter.py` (新建)
- `tests/unit/test_config_manager.py` (新建)
- `tests/unit/test_server_manager.py` (修改)
- `tests/unit/test_cli_launcher.py` (修改)
- `tests/unit/test_main_window.py` (修改)

---

#### T-011: 集成测试

**优先级**: P1
**预估复杂度**: Standard
**依赖**: T-010
**并行组**: 4

**描述**:
编写集成测试，验证各组件协同工作。

**实施步骤**:
1. 创建 `tests/integration/test_launcher_logging.py`
2. 测试启动 MCP 服务器并验证日志
3. 测试启动 Claude CLI 并验证日志
4. 测试 CLI 参数持久化
5. 测试错误弹窗复制功能

**验收标准**:
- [ ] 启动 MCP 服务器后日志文件包含正确命令
- [ ] 启动 Claude CLI 后日志文件包含完整信息
- [ ] CLI 参数在重启后正确恢复
- [ ] 错误复制功能正常工作

**涉及文件**:
- `tests/integration/test_launcher_logging.py` (新建)

---

#### T-012: E2E 测试和文档更新

**优先级**: P1
**预估复杂度**: Standard
**依赖**: T-011
**并行组**: 4

**描述**:
编写 E2E 测试，更新用户文档和 CHANGELOG。

**实施步骤**:
1. 创建 `tests/e2e/test_gui_launcher.py`
2. 使用 pytest-qt 进行 GUI 自动化测试
3. 测试完整的用户工作流
4. 更新 `README.md` - 添加 CLI 参数说明
5. 更新 `docs/user-guide.md` - 添加日志查看指南
6. 更新 `CHANGELOG.md` - 记录新功能

**验收标准**:
- [ ] E2E 测试覆盖主要用户场景
- [ ] 所有测试通过
- [ ] 文档更新完整且准确
- [ ] CHANGELOG 包含所有新功能

**涉及文件**:
- `tests/e2e/test_gui_launcher.py` (新建)
- `README.md` (修改)
- `docs/user-guide.md` (修改)
- `CHANGELOG.md` (修改)

---

## 并行执行策略

### Group 1: 基础设施（串行）
- T-001 和 T-002 必须先完成，为后续任务提供基础

### Group 2: 核心功能（并行）
- T-003, T-004, T-005 可以并行开发
- 互不依赖，可由不同开发者同时进行

### Group 3: 增强功能（部分并行）
- T-006 依赖 T-002 和 T-005
- T-007 依赖 T-005
- T-008 依赖 T-003 和 T-004
- T-009 依赖 T-001
- T-007, T-008, T-009 可以并行

### Group 4: 测试和文档（串行）
- T-010 必须在所有功能完成后进行
- T-011 依赖 T-010
- T-012 依赖 T-011

---

## 风险评估

| 任务 | 风险 | 缓解措施 |
|------|------|----------|
| T-003 | MCP 服务器日志配置复杂 | 使用环境变量简化配置 |
| T-005 | UI 布局调整影响现有功能 | 使用可折叠区域，最小化影响 |
| T-006 | QSettings 跨平台兼容性 | 在所有平台上测试 |
| T-008 | Windows 权限设置不同 | 使用跨平台的权限设置方法 |

---

## 预估工作量

| 分组 | 任务数 | 预估时间 |
|------|--------|----------|
| Group 1 | 2 | 2 小时 |
| Group 2 | 3 | 4 小时 |
| Group 3 | 4 | 3 小时 |
| Group 4 | 3 | 4 小时 |
| **总计** | **12** | **13 小时** |

---

**维护者**: AI Team
**最后更新**: 2026-01-25
