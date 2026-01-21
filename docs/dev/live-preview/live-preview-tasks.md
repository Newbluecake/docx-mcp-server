# 任务清单: Word/WPS 实时预览

> **功能**: live-preview
> **依赖**: 无
> **预估工时**: 4h

## 任务分组

### Group 1: 核心基础结构 (Core Infrastructure)

- [ ] **T-001**: 创建 `preview` 模块与抽象接口
  - 定义 `PreviewController` 抽象基类
  - 实现 `NoOpPreviewController` (Linux/Mac 默认实现)
  - 创建 `PreviewManager` 工厂类
  - 验证点：在 Linux 环境下调用工厂返回 NoOp 实现

- [ ] **T-002**: 集成 `Session` 与 `PreviewController`
  - 修改 `Session` 类，初始化时获取 Controller 实例
  - 扩展 `docx_save` 工具，在保存前后调用 Controller 的钩子方法 (prepare/refresh)
  - 验证点：调用 save 时能触发 Controller 的日志/空操作

### Group 2: Windows COM 实现 (Windows Implementation)

- [ ] **T-003**: 实现 `Win32PreviewController` (核心逻辑)
  - 实现 COM 连接逻辑 (`GetActiveObject`)
  - 实现 WPS/Word 双适配 (ProgID 探测)
  - 实现 `prepare_for_save`: 查找并关闭目标文档
  - 实现 `refresh`: 重新打开文档
  - 注意：添加 `sys.platform` 保护和 `try-import pywin32`
  - 验证点：单元测试中使用 `unittest.mock` 模拟 `win32com.client` 验证逻辑流

- [ ] **T-004**: 依赖与环境配置
  - 更新 `pyproject.toml`，添加 `pywin32` 为 Windows 平台特定依赖 (或 `optional-dependencies`)
  - 确保 CI/CD 流程在 Linux 下不因缺失 pywin32 报错

### Group 3: 健壮性与测试 (Robustness)

- [ ] **T-005**: 错误处理与日志增强
  - 为 COM 操作添加全局异常捕获
  - 确保 Word 卡死或弹窗时 MCP 不会崩溃
  - 完善单元测试，覆盖 COM 连接失败、文件未打开等场景

- [ ] **T-006**: 手动测试指南 (Manual Test Plan)
  - 由于无法在 CI 环境测试真实的 Word 交互，编写 `docs/manual_test_live_preview.md`
  - 描述如何在 Windows 机器上验证功能

## 依赖关系
T-001 -> T-002 -> T-003
T-003 -> T-004
T-003 -> T-005
