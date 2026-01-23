# 技术设计: 实时文档预览 (Realtime Preview)

> **功能标识**: realtime-preview
> **状态**: Draft
> **作者**: architect-planner
> **日期**: 2026-01-23

## 1. 系统架构

本功能旨在为 MCP 操作提供实时的视觉反馈。架构设计遵循 "非侵入式" 和 "平台抽象" 原则。

### 1.1 核心组件图

```mermaid
graph TD
    A[Session] -->|trigger| B[PreviewManager]
    B -->|get_controller| C[PreviewController]
    C <|-- D[WindowsPreviewController]
    C <|-- E[MacOSPreviewController]
    C <|-- F[DummyPreviewController]

    A -->|export| G[Preview File (.docx)]
    D -->|open/refresh| G
    E -->|open/refresh| G
```

### 1.2 模块设计

#### 1.2.1 PreviewController (Abstract Base)
定义预览控制器的标准接口。
- `is_available() -> bool`: 当前环境是否支持预览。
- `open(file_path: str)`: 打开预览窗口。
- `refresh(file_path: str)`: 刷新预览内容（如果支持）。

#### 1.2.2 Platform Implementations
- **Windows**: 使用 `os.startfile` 或 `subprocess.Popen(['start', ...], shell=True)`。
- **macOS**: 使用 `subprocess.Popen(['open', ...])`。
- **Linux/Headless**: 空实现，记录日志。

#### 1.2.3 Session Integration
在 `Session` 类中增加预览状态管理：
- `preview_enabled`: bool
- `preview_file_path`: str (e.g., `original_preview.docx`)
- Hook method: `_on_modification()` 触发预览刷新。

## 2. 数据流

1. **初始化**:
   - 用户调用 `docx_create(..., preview=True)`。
   - Session 初始化 `PreviewManager`。
   - 创建初始预览文件副本。
   - 调用 `controller.open(preview_path)`。

2. **更新**:
   - 用户调用 `docx_insert_paragraph` 等工具。
   - 工具内部调用 `session.update_context()` 或直接修改 document。
   - Session 检测到变更，调用 `_trigger_preview()`。
   - `_trigger_preview()` 将当前 `document` 保存到 `preview_file_path`。
   - 调用 `controller.refresh()` (对于简单的文件打开，通常操作系统会自动检测文件变更或再次调用 open 会聚焦窗口)。

3. **关闭**:
   - `docx_close()` 清理预览临时文件（可选，根据配置）。

## 3. 关键技术决策

### 3.1 文件锁定处理 (R-002)
- **问题**: Word 打开文件时会锁定文件，导致 Python 无法写入。
- **解决方案**: **分离式写入**。
    - MCP 始终操作内存中的 `Document` 对象。
    - 预览时，尝试写入 `preview.docx`。
    - 如果写入失败（PermissionError），则写入 `preview_{timestamp}.docx` 并打开新文件（Fallback策略），或者跳过本次预览并警告。
    - *优化*: 大多数现代编辑器（VS Code, WPS, 甚至部分版本的 Word）允许在只读模式下打开，或者不完全锁定。但在 Windows 上 Word 的锁定是强强制的。
    - *改进策略*: 写入临时文件 `temp.docx`，然后尝试 `shutil.move` 或 `copy` 到预览路径。如果失败，则仅记录日志，不阻塞主流程。

### 3.2 性能控制
- 避免过于频繁的 IO。
- 引入 **Debounce (防抖)** 机制：如果是批处理操作，不要每一步都保存预览。
- *本次迭代*：暂不实现复杂的防抖，假设 MCP 操作频率较低（每步几秒）。

## 4. 接口变更

### 4.1 docx_create
新增参数 `preview: bool = False`。

```python
def docx_create(file_path: str = None, preview: bool = False, ...):
    ...
```

## 5. 安全性考量
- `validate_path_safety` 必须确保存储预览文件的路径是安全的。
- 避免预览文件覆盖用户的重要数据。使用特定的后缀 `_preview.docx`。
