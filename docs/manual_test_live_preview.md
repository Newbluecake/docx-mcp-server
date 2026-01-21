# Word/WPS 实时预览 - 手动测试指南

> 由于实时预览功能依赖本地安装的 Office/WPS 软件和 Windows 桌面环境，无法在 CI 环境中自动测试。本指南用于指导开发者或用户在 Windows 环境下进行手动验证。

## 1. 测试环境准备

- **操作系统**: Windows 10/11
- **软件依赖**:
  - Python 3.10+
  - Microsoft Word 或 WPS Office
  - `uv` (包管理器)

## 2. 安装步骤

```powershell
# 1. 克隆项目
git clone https://github.com/your-org/docx-mcp-server.git
cd docx-mcp-server

# 2. 安装依赖 (会自动包含 pywin32)
uv sync --extra gui
# 或者
uv pip install -e .[gui]
```

## 3. 测试场景 A: Word 已打开文档 (核心功能)

此场景验证 "Close-Write-Reopen" 核心逻辑。

1. **准备文件**:
   - 在桌面创建一个名为 `preview_test.docx` 的空文档。
   - 使用 Word 打开它，放在屏幕一侧。

2. **启动 MCP Server**:
   - 打开终端，运行:
     ```powershell
     uv run mcp-server-docx
     ```

3. **执行 MCP 操作** (模拟 Claude):
   - 这里的“模拟”是指你可以编写一个简单的 Python 脚本来调用 server，或者如果你是在 Claude Desktop 中集成，直接对话。
   - 假设使用 Python 脚本 `test_script.py`:

   ```python
   # test_script.py
   import os
   from docx_mcp_server.core.session import SessionManager
   from docx_mcp_server.preview.manager import PreviewManager

   # 1. 初始化
   print("Initializing...")
   manager = SessionManager()

   # 2. 绑定绝对路径
   file_path = os.path.abspath("preview_test.docx")
   session_id = manager.create_session(file_path)
   session = manager.get_session(session_id)

   # 3. 修改内容
   print("Adding paragraph...")
   session.document.add_paragraph("Hello from MCP Live Preview!")

   # 4. 触发保存 (关键时刻)
   print("Saving...")
   # 手动模拟 server.py 中的保存逻辑
   try:
       session.preview_controller.prepare_for_save(file_path)
       session.document.save(file_path)
       session.preview_controller.refresh(file_path)
       print("✅ Save complete!")
   except Exception as e:
       print(f"❌ Save failed: {e}")
   ```

4. **观察结果**:
   - **预期**:
     - 运行脚本时，你会看到 Word 窗口短暂闪烁（文档被关闭）。
     - 脚本提示 "Save complete"。
     - Word 窗口重新出现，且文档内容已更新，显示 "Hello from MCP Live Preview!"。
   - **失败**:
     - 脚本报错 `PermissionError` (说明文件未成功解锁)。
     - Word 仍显示旧内容 (说明未重载)。

## 4. 测试场景 B: 文档未打开 (无副作用)

1. **关闭 Word**。
2. 再次运行上述脚本。
3. **预期**:
   - 脚本正常运行，不报错。
   - 文件被修改。
   - Word **不会** 自动弹出来 (Controller 检测到未打开，所以只保存不重开)。

## 5. 常见问题排查

- **Q: 脚本卡住不动了？**
  - **A**: 检查 Word 是否弹出了对话框（如“保存更改吗？”或“激活向导”）。COM 调用会被模态对话框阻塞。手动处理对话框后脚本应继续。

- **Q: 报错 `ImportError: pywin32 is required`？**
  - **A**: 确保你是在 Windows 环境且运行了 `uv sync` 安装了 pywin32。

- **Q: WPS 支持吗？**
  - **A**: 支持。代码会自动探测 `KWPS.Application`。请确保只打开了一个 Office 软件，避免混淆。
