# 任务清单: Docx Server Windows GUI Launcher

## Group 1: 基础架构与核心逻辑

- [ ] **T-001**: 初始化项目结构与依赖
  - 创建 `src/docx_server_launcher` 目录结构
  - 添加 `PyQt6`, `pyinstaller` 到 `pyproject.toml` (作为 dev 依赖或 extras)
  - 创建空的 `main.py` 确保能启动空窗口
  - **验证**: 运行 `python -m src.docx_server_launcher.main` 显示窗口

- [ ] **T-002**: 实现 ServerManager
  - 使用 `QProcess` 封装 `docx-mcp-server` 的启动与停止
  - 实现 stdout/stderr 的信号转发
  - **验证**: 单元测试模拟进程启动，检查信号发射

- [ ] **T-003**: 实现 ConfigInjector
  - 编写 JSON 读写逻辑
  - 实现针对 `claude_desktop_config.json` 的注入逻辑
  - **验证**: 单元测试读取 sample json 并验证修改后的内容

## Group 2: GUI 实现

- [ ] **T-004**: 实现主界面布局
  - 使用 PyQt6 编写 `MainWindow`
  - 包含 Host, Port, Cwd 输入框
  - 包含 Start/Stop 按钮和 Log 区域
  - **验证**: 运行查看界面布局是否符合设计

- [ ] **T-005**: 集成 ServerManager 到 GUI
  - 绑定 Start/Stop 按钮事件
  - 将日志信号连接到 Log 文本框
  - 处理进程异常退出的情况
  - **验证**: 点击 Start 能启动 server，Log 区域显示 server 输出

- [ ] **T-006**: 集成 ConfigInjector 到 GUI
  - 添加 "Inject Config" 按钮
  - 添加文件选择对话框选择 Claude 配置
  - **验证**: 点击按钮能成功修改配置文件并提示成功

## Group 3: 打包与交付

- [ ] **T-007**: PyInstaller 打包配置
  - 编写 `build.spec`
  - 处理 hidden imports (如果有)
  - **验证**: 生成的 .exe 在无 Python 环境下(模拟)能运行
