# 技术设计文档: Log Search Feature

> **功能标识**: log-search
> **复杂度**: standard
> **设计版本**: v1.0
> **创建时间**: 2026-01-22

---

## 1. 架构设计

### 1.1 系统架构

```
MainWindow
    └── log_group (QGroupBox)
        ├── search_toolbar (QHBoxLayout)
        │   ├── search_input (QLineEdit)
        │   ├── prev_btn (QPushButton)
        │   ├── next_btn (QPushButton)
        │   ├── match_label (QLabel)
        │   ├── case_checkbox (QCheckBox)
        │   ├── regex_checkbox (QCheckBox)
        │   └── clear_btn (QPushButton)
        └── log_area (QPlainTextEdit)
```

### 1.2 核心组件

| 组件 | 职责 | 技术实现 |
|------|------|----------|
| `LogSearchToolbar` | 搜索控件封装（可选） | QWidget 子类或直接在 main_window.py |
| `HighlightManager` | 管理高亮状态 | 使用 QTextEdit.ExtraSelection API |
| `SearchEngine` | 执行搜索逻辑 | Python re 模块 + QTextDocument.find() |
| `SettingsManager` | 持久化搜索选项 | QSettings (现有机制) |

### 1.3 数据流

```
用户输入搜索文本
    ↓
[防抖 300ms]
    ↓
SearchEngine.find_matches()
    ├── 构建正则表达式（根据选项）
    ├── 遍历 QTextDocument
    └── 返回匹配位置列表 [(start_pos, length), ...]
    ↓
HighlightManager.apply_highlights()
    ├── 清除旧高亮
    ├── 创建 ExtraSelection 列表
    │   ├── 普通匹配：黄色背景 (#FFFF00)
    │   └── 当前匹配：橙色背景 (#FFA500)
    └── setExtraSelections()
    ↓
更新匹配计数显示 (1/5)
```

---

## 2. 模块设计

### 2.1 文件结构

```
src/docx_server_launcher/
    gui/
        main_window.py          # 修改：添加搜索工具栏
        log_search.py           # 新建：搜索逻辑封装（可选）
    core/
        (无变更)
```

**决策**：优先在 `main_window.py` 中实现，如果代码量 > 200 行，则提取到 `log_search.py`。

### 2.2 类设计

#### 2.2.1 MainWindow 扩展

```python
class MainWindow(QMainWindow):
    # 新增属性
    search_input: QLineEdit
    prev_btn: QPushButton
    next_btn: QPushButton
    match_label: QLabel
    case_checkbox: QCheckBox
    regex_checkbox: QCheckBox
    clear_log_btn: QPushButton

    # 搜索状态
    _search_matches: List[Tuple[int, int]] = []  # [(start, length), ...]
    _current_match_index: int = -1
    _search_timer: QTimer = None  # 防抖定时器

    # 新增方法
    def init_search_toolbar(self) -> None:
        """初始化搜索工具栏"""

    def on_search_text_changed(self, text: str) -> None:
        """搜索框文本变化处理（防抖）"""

    def perform_search(self) -> None:
        """执行搜索并高亮"""

    def navigate_to_match(self, direction: int) -> None:
        """导航到上一个/下一个匹配（direction: -1 或 1）"""

    def clear_highlights(self) -> None:
        """清除所有高亮"""

    def update_match_label(self) -> None:
        """更新匹配计数显示"""

    def clear_log_area(self) -> None:
        """清空日志内容"""

    def save_search_settings(self) -> None:
        """保存搜索选项到 QSettings"""

    def load_search_settings(self) -> None:
        """从 QSettings 加载搜索选项"""
```

#### 2.2.2 搜索引擎（内嵌或独立）

```python
class LogSearchEngine:
    """日志搜索引擎（如果提取独立文件）"""

    @staticmethod
    def find_matches(
        text: str,
        pattern: str,
        case_sensitive: bool,
        use_regex: bool
    ) -> List[Tuple[int, int]]:
        """
        查找所有匹配位置

        Returns:
            [(start_pos, length), ...]
        """

    @staticmethod
    def validate_regex(pattern: str) -> Tuple[bool, str]:
        """
        验证正则表达式

        Returns:
            (is_valid, error_message)
        """
```

---

## 3. 接口设计

### 3.1 用户界面接口

#### 搜索工具栏布局

```python
search_toolbar_layout = QHBoxLayout()

# Row 1: 搜索输入 + 导航按钮 + 匹配数
search_row = QHBoxLayout()
search_row.addWidget(QLabel("Search:"))
search_row.addWidget(self.search_input)  # stretch=1
search_row.addWidget(self.prev_btn)      # 图标: ↑
search_row.addWidget(self.next_btn)      # 图标: ↓
search_row.addWidget(self.match_label)   # "1 / 5"

# Row 2: 选项 + 清空按钮
options_row = QHBoxLayout()
options_row.addWidget(self.case_checkbox)   # "Case Sensitive"
options_row.addWidget(self.regex_checkbox)  # "Regex"
options_row.addStretch()
options_row.addWidget(self.clear_log_btn)   # "Clear Logs"

search_toolbar_layout.addLayout(search_row)
search_toolbar_layout.addLayout(options_row)
```

### 3.2 高亮接口（QTextEdit API）

```python
from PyQt6.QtGui import QTextEdit, QTextCharFormat, QColor

def apply_highlights(
    text_edit: QPlainTextEdit,
    matches: List[Tuple[int, int]],
    current_index: int = -1
) -> None:
    """应用搜索高亮"""

    extra_selections = []

    for i, (start, length) in enumerate(matches):
        selection = QTextEdit.ExtraSelection()

        # 设置光标位置
        cursor = text_edit.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(start + length, QTextCursor.MoveMode.KeepAnchor)
        selection.cursor = cursor

        # 设置背景颜色
        format = QTextCharFormat()
        if i == current_index:
            format.setBackground(QColor("#FFA500"))  # 橙色（当前匹配）
        else:
            format.setBackground(QColor("#FFFF00"))  # 黄色（普通匹配）
        selection.format = format

        extra_selections.append(selection)

    text_edit.setExtraSelections(extra_selections)
```

### 3.3 设置接口（QSettings）

```python
# 保存
settings = QSettings("DocxMCP", "Launcher")
settings.setValue("search/case_sensitive", self.case_checkbox.isChecked())
settings.setValue("search/use_regex", self.regex_checkbox.isChecked())

# 加载
case_sensitive = settings.value("search/case_sensitive", False, type=bool)
use_regex = settings.value("search/use_regex", False, type=bool)
```

---

## 4. 数据设计

### 4.1 搜索状态

```python
# 实例变量
self._search_matches: List[Tuple[int, int]] = []
    # [(start_pos, length), ...]
    # 示例: [(10, 5), (50, 5), (120, 5)]  # "ERROR" 出现 3 次

self._current_match_index: int = -1
    # -1: 无导航
    # 0-N: 当前高亮的匹配索引

self._search_timer: QTimer | None = None
    # 防抖定时器（300ms 延迟）
```

### 4.2 持久化数据

```python
QSettings 键值对:
    "search/case_sensitive": bool
    "search/use_regex": bool
```

---

## 5. 核心算法

### 5.1 搜索算法（普通模式）

```python
def find_matches_plain(text: str, pattern: str, case_sensitive: bool):
    """普通文本搜索（不使用正则）"""
    matches = []

    if not case_sensitive:
        text_lower = text.lower()
        pattern_lower = pattern.lower()
    else:
        text_lower = text
        pattern_lower = pattern

    start = 0
    while True:
        pos = text_lower.find(pattern_lower, start)
        if pos == -1:
            break
        matches.append((pos, len(pattern)))
        start = pos + 1  # 允许重叠匹配

    return matches
```

### 5.2 搜索算法（正则模式）

```python
import re

def find_matches_regex(text: str, pattern: str, case_sensitive: bool):
    """正则表达式搜索"""
    try:
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)
    except re.error as e:
        raise ValueError(f"Invalid regex: {e}")

    matches = []
    for match in regex.finditer(text):
        matches.append((match.start(), match.end() - match.start()))

    return matches
```

### 5.3 防抖机制

```python
def on_search_text_changed(self, text: str):
    """搜索框文本变化（防抖 300ms）"""
    if self._search_timer:
        self._search_timer.stop()

    self._search_timer = QTimer()
    self._search_timer.setSingleShot(True)
    self._search_timer.timeout.connect(self.perform_search)
    self._search_timer.start(300)  # 300ms 延迟
```

### 5.4 性能优化策略

| 优化点 | 实现方式 | 预期效果 |
|--------|----------|----------|
| 批量高亮 | 使用 `setExtraSelections()` 一次性设置 | 避免逐个高亮导致的重绘 |
| 防抖搜索 | QTimer 延迟 300ms | 减少不必要的搜索次数 |
| 限制匹配数 | 最多高亮前 1000 个匹配 | 防止大量匹配导致内存溢出 |
| 使用 QRegularExpression | 可选：使用 Qt C++ 正则 | 比 Python re 更快（未实施） |

---

## 6. 安全考量

### 6.1 正则表达式 DoS 防护

**风险**：恶意正则表达式（如 `(a+)+b`）可能导致 CPU 100% 卡死。

**缓解措施**：
1. **超时机制**：使用 `QTimer` 限制搜索时间（最多 500ms）
2. **复杂度检测**：拒绝嵌套量词过多的正则（如 `(x+)+` 或 `(x*)*`）
3. **用户提示**：检测到高复杂度正则时显示警告

```python
def validate_regex_safety(pattern: str) -> Tuple[bool, str]:
    """检测危险正则表达式"""
    # 简单启发式：检测嵌套量词
    dangerous_patterns = [
        r'\([^)]*[+*]\)[+*]',  # (x+)+ or (x*)*
        r'\([^)]*[+*]\)\{',    # (x+){n,m}
    ]
    for dp in dangerous_patterns:
        if re.search(dp, pattern):
            return False, "Potentially dangerous regex (nested quantifiers)"
    return True, ""
```

### 6.2 输入验证

- **搜索框长度限制**：最多 200 字符（防止超长输入）
- **日志行数限制**：清空日志时，超过 100 行显示确认对话框

---

## 7. 错误处理

### 7.1 错误场景

| 错误场景 | 处理方式 | 用户反馈 |
|---------|---------|---------|
| 无效正则表达式 | 捕获 `re.error` | 搜索框红色边框 + Tooltip 显示错误 |
| 正则超时 | QTimer 超时中断 | 显示警告："搜索超时，请简化正则" |
| 匹配数过多 (>1000) | 只高亮前 1000 个 | 匹配数显示 "1000+ matches" |

### 7.2 错误处理代码

```python
def perform_search(self):
    """执行搜索（带错误处理）"""
    pattern = self.search_input.text()
    if not pattern:
        self.clear_highlights()
        return

    try:
        # 正则验证
        if self.regex_checkbox.isChecked():
            is_safe, msg = validate_regex_safety(pattern)
            if not is_safe:
                self.show_search_error(msg)
                return

        # 执行搜索
        text = self.log_area.toPlainText()
        matches = find_matches(
            text, pattern,
            self.case_checkbox.isChecked(),
            self.regex_checkbox.isChecked()
        )

        # 限制匹配数
        if len(matches) > 1000:
            matches = matches[:1000]
            self.match_label.setText("1000+ matches")

        # 应用高亮
        self._search_matches = matches
        self._current_match_index = 0 if matches else -1
        self.apply_highlights()
        self.update_match_label()

        # 清除错误状态
        self.search_input.setStyleSheet("")

    except re.error as e:
        self.show_search_error(f"Invalid regex: {e}")
    except Exception as e:
        self.show_search_error(f"Search error: {e}")

def show_search_error(self, message: str):
    """显示搜索错误"""
    self.search_input.setStyleSheet("border: 1px solid red;")
    self.search_input.setToolTip(message)
    self.match_label.setText("Error")
```

---

## 8. 测试策略

### 8.1 单元测试

**测试文件**: `tests/unit/test_log_search.py`

| 测试用例 | 输入 | 预期输出 |
|---------|------|---------|
| 普通搜索（大小写不敏感） | text="Error error ERROR", pattern="error" | 3 matches |
| 普通搜索（大小写敏感） | text="Error error ERROR", pattern="error" | 1 match |
| 正则搜索 | text="2026-01-22 10:00", pattern=r"\d{4}-\d{2}-\d{2}" | 1 match |
| 无效正则 | pattern="[(" | ValueError |
| 空搜索 | pattern="" | 0 matches, 清除高亮 |

### 8.2 集成测试

**测试文件**: `tests/integration/test_log_search_ui.py`

| 测试场景 | 操作步骤 | 验证点 |
|---------|---------|--------|
| 搜索高亮 | 1. 输入"ERROR"<br>2. 等待 300ms | log_area 中"ERROR"被黄色高亮 |
| 结果导航 | 1. 搜索"INFO"<br>2. 点击"下一个" | 滚动到第 2 个匹配，橙色高亮 |
| 清空日志 | 1. 生成 150 行日志<br>2. 点击"Clear" | 显示确认对话框 |
| 设置持久化 | 1. 勾选"Case Sensitive"<br>2. 重启 GUI | 选项状态保持 |

### 8.3 性能测试

**测试脚本**: `tests/performance/test_large_log_search.py`

```python
def test_large_log_performance():
    """测试 15000 行日志的搜索性能"""
    # 生成 15000 行日志
    log_text = "\n".join([f"[2026-01-22 10:{i:04d}] INFO Message {i}" for i in range(15000)])

    # 测试搜索时间
    start = time.time()
    matches = find_matches(log_text, "INFO", case_sensitive=False, use_regex=False)
    elapsed = time.time() - start

    assert elapsed < 0.5, f"Search took {elapsed}s, expected < 500ms"
    assert len(matches) == 15000
```

---

## 9. 部署计划

### 9.1 开发步骤

| 阶段 | 任务 | 预计时间 |
|------|------|---------|
| 1 | UI 布局（搜索工具栏） | 1h |
| 2 | 搜索引擎（普通 + 正则） | 2h |
| 3 | 高亮管理（ExtraSelection） | 1.5h |
| 4 | 结果导航（上一个/下一个） | 1h |
| 5 | 清空日志按钮 | 0.5h |
| 6 | 键盘快捷键 | 1h |
| 7 | 设置持久化 | 0.5h |
| 8 | 性能优化 | 1h |
| 9 | 单元测试 + 集成测试 | 2h |
| **总计** | | **10.5h** |

### 9.2 回滚计划

如果新功能导致问题，可通过以下方式回滚：

1. **Git revert** 提交
2. **特性开关**（可选）：在 `QSettings` 中添加 `enable_search_feature` 开关

---

## 10. 附录

### 10.1 关键 API 参考

#### QPlainTextEdit.setExtraSelections()

```python
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QTextCharFormat, QColor

# 创建高亮选区
selection = QTextEdit.ExtraSelection()
selection.cursor = text_cursor  # QTextCursor
selection.format = text_format  # QTextCharFormat

# 批量设置
text_edit.setExtraSelections([selection1, selection2, ...])
```

#### QTextCursor 定位

```python
cursor = text_edit.textCursor()
cursor.setPosition(100)  # 定位到第 100 个字符
cursor.setPosition(105, QTextCursor.MoveMode.KeepAnchor)  # 选中 100-105
text_edit.setTextCursor(cursor)  # 应用（触发滚动）
```

### 10.2 颜色方案

| 用途 | 颜色 | 说明 |
|------|------|------|
| 普通匹配 | `#FFFF00` (黄色) | 所有匹配项的默认高亮 |
| 当前匹配 | `#FFA500` (橙色) | 导航时的当前结果 |
| 错误边框 | `#FF0000` (红色) | 无效正则时的输入框边框 |

### 10.3 键盘快捷键映射

```python
# 在 MainWindow.__init__() 中添加
from PyQt6.QtGui import QShortcut, QKeySequence

# Ctrl+F: 聚焦搜索框
QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(
    lambda: self.search_input.setFocus()
)

# Enter / F3: 下一个结果
QShortcut(QKeySequence("Return"), self.search_input).activated.connect(
    lambda: self.navigate_to_match(1)
)
QShortcut(QKeySequence("F3"), self).activated.connect(
    lambda: self.navigate_to_match(1)
)

# Shift+Enter / Shift+F3: 上一个结果
QShortcut(QKeySequence("Shift+Return"), self.search_input).activated.connect(
    lambda: self.navigate_to_match(-1)
)
QShortcut(QKeySequence("Shift+F3"), self).activated.connect(
    lambda: self.navigate_to_match(-1)
)

# Esc: 清空搜索框
QShortcut(QKeySequence("Escape"), self.search_input).activated.connect(
    lambda: self.search_input.clear()
)
```

---

**文档版本**: v1.0
**最后更新**: 2026-01-22
**作者**: Claude (via spec-workflow-executor)
