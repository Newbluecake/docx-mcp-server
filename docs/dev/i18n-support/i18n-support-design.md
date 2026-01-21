# 技术设计: i18n Support

> **Feature**: i18n-support
> **Status**: Draft

## 1. 架构设计

### 1.1 核心组件
- **LanguageManager**: 单例类，负责加载 `.qm` 文件、安装/移除 `QTranslator`、保存/读取用户偏好。
- **MainWindow Refactoring**: 将 UI 文本设置逻辑分离到 `retranslateUi()` 方法中，以便在语言切换事件 (`QEvent.LanguageChange`) 发生时重新调用。
- **Resources**: 翻译文件存放于 `src/docx_server_launcher/resources/translations/`。

### 1.2 工作流
1. **启动时**:
   - `LanguageManager` 读取 `QSettings` 中的语言配置（默认为 System Locale）。
   - 加载对应的 `.qm` 文件。
   - 安装 Translator 到 `QApplication`。
2. **运行时切换**:
   - 用户在 ComboBox 选择新语言。
   - `LanguageManager` 加载新 Translator，卸载旧 Translator。
   - 触发 `QEvent.LanguageChange`。
   - 所有 Widget 响应事件，调用 `retranslateUi()` 刷新文本。
3. **打包**:
   - `.qm` 文件作为数据文件包含在 PyInstaller spec 中。
   - 运行时通过 `sys._MEIPASS` 解析路径。

## 2. 模块详细设计

### 2.1 LanguageManager (`core/language_manager.py`)
```python
class LanguageManager(QObject):
    language_changed = pyqtSignal(str) # emit locale code (e.g., "zh_CN")

    def load_language(self, locale: str):
        # 1. Remove old translator
        # 2. Load new .qm file
        # 3. Install new translator
        # 4. Save to QSettings
```

### 2.2 MainWindow 改造
- **Before**: `init_ui()` 包含 `self.label.setText("Hello")`
- **After**:
  ```python
  def init_ui(self):
      # create widgets...
      self.retranslateUi()

  def retranslateUi(self):
      self.setWindowTitle(self.tr("Docx MCP Server Launcher"))
      self.start_btn.setText(self.tr("Start Server"))
      # ... sets all texts

  def changeEvent(self, event):
      if event.type() == QEvent.Type.LanguageChange:
          self.retranslateUi()
      super().changeEvent(event)
  ```

### 2.3 翻译流程
- 使用 `self.tr("Text")` 包裹所有硬编码字符串。
- 运行 `pylupdate6` 提取字符串到 `.ts` 文件。
- 使用 `Linguist` 或手动编辑 `.ts` 文件进行翻译。
- 运行 `lrelease6` 编译为 `.qm`。

## 3. 文件变更
- `src/docx_server_launcher/core/language_manager.py` (New)
- `src/docx_server_launcher/gui/main_window.py` (Modify)
- `src/docx_server_launcher/resources/translations/*.ts` (New)
- `docx-server-launcher.spec` (Modify)
