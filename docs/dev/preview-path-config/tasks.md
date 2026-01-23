# 任务清单: 预览路径配置 (preview-path-config)

## Execution 阶段

### Group 1: GUI Implementation
- [ ] **T-001**: 更新 `MainWindow` UI 布局
  - 在 `init_ui` 中添加 "Preview Settings" GroupBox。
  - 添加 WPS Path 输入框和 Browse 按钮。
  - 添加 Word Path 输入框和 Browse 按钮。
  - 添加 Priority 下拉框 (Auto, Prefer WPS, Prefer Word)。
  - **验收标准**: 界面正确显示新控件，布局合理。

- [ ] **T-002**: 实现 GUI 逻辑与持久化
  - 实现 Browse 按钮点击槽函数，仅允许选择 .exe。
  - 在 `load_settings` 中读取 `preview/*` 配置。
  - 在 `save_settings` 中保存 `preview/*` 配置。
  - **验收标准**: 重启应用后配置不丢失。

### Group 2: Server & Preview Logic
- [ ] **T-003**: 更新 `ServerManager` 传递环境变量
  - 修改 `start_server` 方法。
  - 从 `QSettings` 或参数中获取 preview 配置。
  - 将配置转换为 `DOCX_PREVIEW_*` 环境变量注入 `QProcess`。
  - **验收标准**: 启动 Server 后，在 Server 进程中能读取到环境变量。

- [ ] **T-004**: 增强 `Win32PreviewController`
  - 修改 `src/docx_mcp_server/preview/win32.py`。
  - 读取新的环境变量。
  - 实现"启动并连接"逻辑：当 `GetActiveObject` 失败且存在配置路径时，尝试 `subprocess.Popen` 启动应用。
  - 优化优先级处理逻辑。
  - **验收标准**: 配置 WPS 路径后，即使 WPS 未运行也能自动启动并预览。

### Group 3: Integration & Review
- [ ] **T-005**: 集成测试与验证
  - 手动测试流程 F-001 ~ F-004。
  - 验证优先级切换是否生效。
  - 验证无效路径的容错处理。
  - **验收标准**: 所有验收标准通过。

## 依赖关系
- T-002 依赖 T-001
- T-003 依赖 T-002
- T-004 依赖 T-003 (逻辑上独立，但测试依赖 T-003 传递参数)
