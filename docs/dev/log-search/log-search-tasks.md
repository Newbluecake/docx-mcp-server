# 任务拆分文档: Log Search Feature

> **功能标识**: log-search
> **复杂度**: standard
> **任务版本**: v1.0
> **创建时间**: 2026-01-22

---

## 任务总览

| 统计项 | 数值 |
|--------|------|
| 总任务数 | 9 |
| P0 任务 | 6 |
| P1 任务 | 3 |
| 预计总时间 | 10.5 小时 |
| 并行组数 | 3 |

---

## 任务列表

### T-001: 初始化搜索工具栏 UI

**优先级**: P0
**预计时间**: 1h
**依赖**: 无
**复杂度**: Simple

**描述**:
在 `main_window.py` 的 `log_group` 中添加搜索工具栏，包括所有必要的 UI 控件（搜索框、导航按钮、复选框、清空按钮）。

**验收标准**:
- [ ] 搜索工具栏位于 `log_group` 顶部，在 `log_area` 之上
- [ ] 包含以下控件：
  - `search_input` (QLineEdit)
  - `prev_btn` (QPushButton，图标 ↑)
  - `next_btn` (QPushButton，图标 ↓)
  - `match_label` (QLabel，显示 "0 / 0")
  - `case_checkbox` (QCheckBox，"Case Sensitive")
  - `regex_checkbox` (QCheckBox，"Regex")
  - `clear_log_btn` (QPushButton，"Clear Logs")
- [ ] 初始状态：所有按钮禁用（因为搜索框为空）
- [ ] UI 与现有风格一致（字体、间距）
- [ ] 支持多语言（使用 `self.tr()`）

**实现要点**:
```python
def init_search_toolbar(self):
    """在 log_group 中添加搜索工具栏"""
    # 修改 log_layout（在 init_ui() 中）
    # log_layout = QVBoxLayout()

    # Row 1: 搜索 + 导航
    search_row = QHBoxLayout()
    # ...添加控件...

    # Row 2: 选项 + 清空
    options_row = QHBoxLayout()
    # ...添加控件...

    log_layout.addLayout(search_row)
    log_layout.addLayout(options_row)
    log_layout.addWidget(self.log_area)  # 日志区域
```

**测试**:
```python
def test_search_toolbar_exists():
    """测试搜索工具栏是否存在"""
    window = MainWindow()
    assert hasattr(window, 'search_input')
    assert hasattr(window, 'prev_btn')
    assert hasattr(window, 'next_btn')
    # ...其他控件...
```

---

### T-002: 实现搜索引擎（普通模式）

**优先级**: P0
**预计时间**: 1h
**依赖**: 无
**复杂度**: Simple

**描述**:
实现基础的文本搜索功能，支持大小写敏感/不敏感，返回所有匹配位置。

**验收标准**:
- [ ] 实现 `find_matches_plain(text, pattern, case_sensitive)` 函数
- [ ] 返回格式：`[(start_pos, length), ...]`
- [ ] 大小写不敏感时，正确匹配不同大小写的文本
- [ ] 支持重叠匹配（如 "aaa" 搜索 "aa" 应返回 2 个匹配）
- [ ] 空搜索返回空列表
- [ ] 性能：10000 行日志搜索 < 100ms

**实现要点**:
```python
def find_matches_plain(text: str, pattern: str, case_sensitive: bool) -> List[Tuple[int, int]]:
    """普通文本搜索"""
    if not pattern:
        return []

    matches = []
    search_text = text if case_sensitive else text.lower()
    search_pattern = pattern if case_sensitive else pattern.lower()

    start = 0
    while True:
        pos = search_text.find(search_pattern, start)
        if pos == -1:
            break
        matches.append((pos, len(pattern)))
        start = pos + 1  # 允许重叠

    return matches
```

**测试**:
```python
def test_find_matches_plain_case_insensitive():
    text = "Error error ERROR"
    matches = find_matches_plain(text, "error", case_sensitive=False)
    assert len(matches) == 3
    assert matches == [(0, 5), (6, 5), (12, 5)]

def test_find_matches_plain_case_sensitive():
    text = "Error error ERROR"
    matches = find_matches_plain(text, "error", case_sensitive=True)
    assert len(matches) == 1
    assert matches == [(6, 5)]
```

---

### T-003: 实现搜索引擎（正则模式）

**优先级**: P0
**预计时间**: 1h
**依赖**: T-002
**复杂度**: Standard

**描述**:
在普通搜索的基础上，添加正则表达式支持，包括正则验证和错误处理。

**验收标准**:
- [ ] 实现 `find_matches_regex(text, pattern, case_sensitive)` 函数
- [ ] 使用 Python `re` 模块
- [ ] 无效正则抛出 `ValueError` 并包含详细错误信息
- [ ] 实现 `validate_regex_safety(pattern)` 检测危险正则（嵌套量词）
- [ ] 性能：简单正则搜索 < 200ms（10000 行）

**实现要点**:
```python
import re

def find_matches_regex(text: str, pattern: str, case_sensitive: bool) -> List[Tuple[int, int]]:
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

def validate_regex_safety(pattern: str) -> Tuple[bool, str]:
    """检测危险正则"""
    dangerous = [r'\([^)]*[+*]\)[+*]', r'\([^)]*[+*]\)\{']
    for dp in dangerous:
        if re.search(dp, pattern):
            return False, "Potentially dangerous regex (nested quantifiers)"
    return True, ""
```

**测试**:
```python
def test_find_matches_regex():
    text = "Date: 2026-01-22, Time: 10:30:45"
    matches = find_matches_regex(text, r"\d{4}-\d{2}-\d{2}", case_sensitive=False)
    assert len(matches) == 1
    assert matches == [(6, 10)]  # "2026-01-22"

def test_validate_regex_safety_dangerous():
    is_safe, msg = validate_regex_safety(r"(a+)+b")
    assert not is_safe
    assert "dangerous" in msg.lower()

def test_find_matches_regex_invalid():
    with pytest.raises(ValueError, match="Invalid regex"):
        find_matches_regex("text", "[(", case_sensitive=False)
```

---

### T-004: 实现高亮管理器

**优先级**: P0
**预计时间**: 1.5h
**依赖**: T-001, T-002
**复杂度**: Standard

**描述**:
使用 PyQt6 的 `QTextEdit.ExtraSelection` API 实现搜索结果高亮，支持普通匹配（黄色）和当前匹配（橙色）的区分。

**验收标准**:
- [ ] 实现 `apply_highlights(matches, current_index)` 方法
- [ ] 使用 `setExtraSelections()` 批量设置高亮
- [ ] 普通匹配背景色：`#FFFF00`（黄色）
- [ ] 当前匹配背景色：`#FFA500`（橙色）
- [ ] 实现 `clear_highlights()` 清除所有高亮
- [ ] 高亮不干扰日志的自动滚动
- [ ] 性能：1000 个匹配的高亮刷新 < 100ms

**实现要点**:
```python
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QTextCharFormat, QColor

def apply_highlights(self):
    """应用搜索高亮"""
    extra_selections = []

    for i, (start, length) in enumerate(self._search_matches):
        selection = QTextEdit.ExtraSelection()

        # 设置光标
        cursor = self.log_area.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(start + length, QTextCursor.MoveMode.KeepAnchor)
        selection.cursor = cursor

        # 设置颜色
        format = QTextCharFormat()
        if i == self._current_match_index:
            format.setBackground(QColor("#FFA500"))  # 橙色
        else:
            format.setBackground(QColor("#FFFF00"))  # 黄色
        selection.format = format

        extra_selections.append(selection)

    self.log_area.setExtraSelections(extra_selections)

def clear_highlights(self):
    """清除所有高亮"""
    self.log_area.setExtraSelections([])
    self._search_matches = []
    self._current_match_index = -1
```

**测试**:
```python
def test_apply_highlights():
    """测试高亮应用"""
    window = MainWindow()
    window.log_area.setPlainText("ERROR error ERROR")
    window._search_matches = [(0, 5), (6, 5), (12, 5)]
    window._current_match_index = 1

    window.apply_highlights()

    selections = window.log_area.extraSelections()
    assert len(selections) == 3
    # 验证第 2 个选区是橙色（当前匹配）
    assert selections[1].format.background().color() == QColor("#FFA500")
```

---

### T-005: 实现防抖搜索机制

**优先级**: P0
**预计时间**: 1h
**依赖**: T-001, T-002, T-003, T-004
**复杂度**: Simple

**描述**:
连接搜索框的文本变化信号，使用 `QTimer` 实现 300ms 防抖，避免频繁搜索。

**验收标准**:
- [ ] 搜索框文本变化时，启动防抖定时器（300ms）
- [ ] 定时器触发后执行搜索
- [ ] 如果文本在定时器触发前再次变化，重置定时器
- [ ] 空搜索时清除高亮
- [ ] 正则错误时在搜索框显示红色边框和 Tooltip

**实现要点**:
```python
def __init__(self):
    # ...
    self._search_timer = None
    self.search_input.textChanged.connect(self.on_search_text_changed)
    self.case_checkbox.stateChanged.connect(self.on_search_option_changed)
    self.regex_checkbox.stateChanged.connect(self.on_search_option_changed)

def on_search_text_changed(self, text: str):
    """搜索框文本变化（防抖）"""
    if self._search_timer:
        self._search_timer.stop()

    self._search_timer = QTimer()
    self._search_timer.setSingleShot(True)
    self._search_timer.timeout.connect(self.perform_search)
    self._search_timer.start(300)  # 300ms

def on_search_option_changed(self):
    """搜索选项变化（立即搜索）"""
    self.perform_search()

def perform_search(self):
    """执行搜索"""
    pattern = self.search_input.text()

    if not pattern:
        self.clear_highlights()
        self.match_label.setText("0 / 0")
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
        use_regex = self.regex_checkbox.isChecked()
        case_sensitive = self.case_checkbox.isChecked()

        if use_regex:
            matches = find_matches_regex(text, pattern, case_sensitive)
        else:
            matches = find_matches_plain(text, pattern, case_sensitive)

        # 限制匹配数
        if len(matches) > 1000:
            matches = matches[:1000]

        # 更新状态
        self._search_matches = matches
        self._current_match_index = 0 if matches else -1

        # 应用高亮
        self.apply_highlights()
        self.update_match_label()

        # 清除错误状态
        self.search_input.setStyleSheet("")
        self.search_input.setToolTip("")

    except ValueError as e:
        self.show_search_error(str(e))

def show_search_error(self, message: str):
    """显示搜索错误"""
    self.search_input.setStyleSheet("border: 1px solid red;")
    self.search_input.setToolTip(message)
    self.match_label.setText("Error")
    self.clear_highlights()
```

**测试**:
```python
def test_debounce_search(qtbot):
    """测试防抖机制"""
    window = MainWindow()
    window.log_area.setPlainText("ERROR error ERROR")

    # 快速输入
    window.search_input.setText("e")
    window.search_input.setText("er")
    window.search_input.setText("err")

    # 等待防抖
    qtbot.wait(350)

    # 应该只执行一次搜索
    assert len(window._search_matches) == 3  # "err" 匹配 3 次
```

---

### T-006: 实现结果导航功能

**优先级**: P1
**预计时间**: 1h
**依赖**: T-004, T-005
**复杂度**: Simple

**描述**:
实现"上一个"/"下一个"按钮，支持在搜索结果间跳转，并更新当前匹配的高亮颜色。

**验收标准**:
- [ ] 点击"下一个"按钮，跳转到下一个匹配
- [ ] 点击"上一个"按钮，跳转到上一个匹配
- [ ] 当前匹配使用橙色高亮，其他匹配使用黄色
- [ ] 到达最后一个匹配时，循环到第一个
- [ ] 到达第一个匹配时，循环到最后一个
- [ ] 自动滚动日志区域，使当前匹配可见
- [ ] 更新匹配计数显示（如 "3 / 5"）

**实现要点**:
```python
def navigate_to_match(self, direction: int):
    """导航到上一个/下一个匹配

    Args:
        direction: -1 (上一个) 或 1 (下一个)
    """
    if not self._search_matches:
        return

    # 更新索引（循环）
    self._current_match_index += direction
    if self._current_match_index >= len(self._search_matches):
        self._current_match_index = 0
    elif self._current_match_index < 0:
        self._current_match_index = len(self._search_matches) - 1

    # 重新应用高亮（更新当前匹配颜色）
    self.apply_highlights()

    # 滚动到当前匹配
    start, length = self._search_matches[self._current_match_index]
    cursor = self.log_area.textCursor()
    cursor.setPosition(start)
    cursor.setPosition(start + length, QTextCursor.MoveMode.KeepAnchor)
    self.log_area.setTextCursor(cursor)  # 触发滚动

    # 更新匹配数显示
    self.update_match_label()

def update_match_label(self):
    """更新匹配计数显示"""
    if not self._search_matches:
        self.match_label.setText("0 / 0")
    else:
        current = self._current_match_index + 1
        total = len(self._search_matches)
        if total > 1000:
            self.match_label.setText(f"{current} / 1000+")
        else:
            self.match_label.setText(f"{current} / {total}")
```

**测试**:
```python
def test_navigate_to_match():
    """测试结果导航"""
    window = MainWindow()
    window.log_area.setPlainText("INFO ERROR INFO ERROR INFO")
    window._search_matches = [(5, 5), (16, 5)]  # 2 个 "ERROR"
    window._current_match_index = 0

    # 下一个
    window.navigate_to_match(1)
    assert window._current_match_index == 1
    assert window.match_label.text() == "2 / 2"

    # 循环到第一个
    window.navigate_to_match(1)
    assert window._current_match_index == 0
    assert window.match_label.text() == "1 / 2"

    # 上一个（循环到最后）
    window.navigate_to_match(-1)
    assert window._current_match_index == 1
```

---

### T-007: 实现清空日志功能

**优先级**: P1
**预计时间**: 0.5h
**依赖**: T-001
**复杂度**: Simple

**描述**:
实现"清空日志"按钮，清除日志内容和所有高亮，大量日志时显示确认对话框。

**验收标准**:
- [ ] 点击"清空日志"按钮，清除 `log_area` 所有内容
- [ ] 清除所有搜索高亮状态
- [ ] 重置匹配计数显示为 "0 / 0"
- [ ] 如果日志行数 > 100，显示确认对话框
- [ ] 确认对话框包含"确定"和"取消"按钮

**实现要点**:
```python
def clear_log_area(self):
    """清空日志内容"""
    # 检查行数
    line_count = self.log_area.document().blockCount()

    if line_count > 100:
        # 显示确认对话框
        reply = QMessageBox.question(
            self,
            self.tr("Confirm Clear"),
            self.tr(f"Are you sure you want to clear {line_count} lines of logs?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

    # 清空日志
    self.log_area.clear()

    # 清除搜索状态
    self.clear_highlights()
    self.match_label.setText("0 / 0")
```

**测试**:
```python
def test_clear_log_area_with_confirmation(qtbot, monkeypatch):
    """测试清空日志（需要确认）"""
    window = MainWindow()
    window.log_area.setPlainText("\n".join([f"Line {i}" for i in range(150)]))

    # Mock 确认对话框
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.StandardButton.Yes)

    window.clear_log_area()

    assert window.log_area.toPlainText() == ""
    assert window.match_label.text() == "0 / 0"
```

---

### T-008: 实现键盘快捷键

**优先级**: P1
**预计时间**: 1h
**依赖**: T-001, T-005, T-006
**复杂度**: Simple

**描述**:
添加键盘快捷键支持，包括聚焦搜索框、导航结果、清空搜索。

**验收标准**:
- [ ] `Ctrl+F` (macOS: `Cmd+F`)：聚焦搜索框
- [ ] `Enter` / `F3`：下一个结果
- [ ] `Shift+Enter` / `Shift+F3`：上一个结果
- [ ] `Esc`：清空搜索框（仅当搜索框有焦点时）
- [ ] 快捷键在整个窗口范围内有效（除了 `Esc`）

**实现要点**:
```python
from PyQt6.QtGui import QShortcut, QKeySequence

def __init__(self):
    # ...
    self.setup_shortcuts()

def setup_shortcuts(self):
    """设置键盘快捷键"""
    # Ctrl+F: 聚焦搜索框
    QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(
        self.search_input.setFocus
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
        self.search_input.clear
    )
```

**测试**:
```python
def test_shortcut_ctrl_f(qtbot):
    """测试 Ctrl+F 快捷键"""
    window = MainWindow()

    # 模拟按键
    qtbot.keyClick(window, Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier)

    # 验证搜索框获得焦点
    assert window.search_input.hasFocus()

def test_shortcut_f3_navigation(qtbot):
    """测试 F3 导航快捷键"""
    window = MainWindow()
    window.log_area.setPlainText("ERROR ERROR ERROR")
    window._search_matches = [(0, 5), (6, 5), (12, 5)]
    window._current_match_index = 0

    # 按 F3
    qtbot.keyClick(window, Qt.Key.Key_F3)

    # 验证跳转到下一个
    assert window._current_match_index == 1
```

---

### T-009: 实现设置持久化

**优先级**: P1
**预计时间**: 0.5h
**依赖**: T-001, T-005
**复杂度**: Simple

**描述**:
使用 `QSettings` 保存和恢复搜索选项（大小写敏感、正则表达式）。

**验收标准**:
- [ ] 关闭 GUI 时，保存 `case_checkbox` 和 `regex_checkbox` 状态
- [ ] 启动 GUI 时，恢复上次的选项状态
- [ ] 使用现有的 `QSettings("DocxMCP", "Launcher")`
- [ ] 键名：`search/case_sensitive`, `search/use_regex`

**实现要点**:
```python
def save_search_settings(self):
    """保存搜索选项"""
    self.settings.setValue("search/case_sensitive", self.case_checkbox.isChecked())
    self.settings.setValue("search/use_regex", self.regex_checkbox.isChecked())

def load_search_settings(self):
    """加载搜索选项"""
    case_sensitive = self.settings.value("search/case_sensitive", False, type=bool)
    use_regex = self.settings.value("search/use_regex", False, type=bool)

    self.case_checkbox.setChecked(case_sensitive)
    self.regex_checkbox.setChecked(use_regex)

def closeEvent(self, event):
    """窗口关闭事件（已有）"""
    self.save_search_settings()
    # ...现有的保存逻辑...
    super().closeEvent(event)

def load_settings(self):
    """加载所有设置（已有）"""
    # ...现有的加载逻辑...
    self.load_search_settings()
```

**测试**:
```python
def test_settings_persistence(tmp_path):
    """测试设置持久化"""
    # 第一个窗口：设置选项
    window1 = MainWindow()
    window1.settings = QSettings(str(tmp_path / "test.ini"), QSettings.Format.IniFormat)
    window1.case_checkbox.setChecked(True)
    window1.regex_checkbox.setChecked(True)
    window1.save_search_settings()
    window1.close()

    # 第二个窗口：验证恢复
    window2 = MainWindow()
    window2.settings = QSettings(str(tmp_path / "test.ini"), QSettings.Format.IniFormat)
    window2.load_search_settings()

    assert window2.case_checkbox.isChecked() is True
    assert window2.regex_checkbox.isChecked() is True
```

---

## 并行执行计划

### 组 1: 基础设施（并行）

| 任务 | 预计时间 | 说明 |
|------|---------|------|
| T-001 | 1h | UI 布局 |
| T-002 | 1h | 搜索引擎（普通） |

**总耗时**: 1h（并行）

### 组 2: 核心功能（顺序）

| 任务 | 预计时间 | 依赖 |
|------|---------|------|
| T-003 | 1h | T-002 |
| T-004 | 1.5h | T-001, T-002 |
| T-005 | 1h | T-001, T-002, T-003, T-004 |

**总耗时**: 3.5h（顺序执行）

### 组 3: 增强功能（并行）

| 任务 | 预计时间 | 依赖 |
|------|---------|------|
| T-006 | 1h | T-004, T-005 |
| T-007 | 0.5h | T-001 |
| T-008 | 1h | T-001, T-005, T-006 |
| T-009 | 0.5h | T-001, T-005 |

**说明**: T-006 完成后，T-008 可以开始。T-007 和 T-009 与其他任务独立。

**总耗时**: 1h（并行，T-008 依赖 T-006）

---

## 整体时间线

```
时间线:
0h ─────┬─── T-001 (1h) ─────┬─── T-004 (1.5h) ───┬─── T-005 (1h) ───┬─── T-006 (1h) ───┬─── T-008 (1h) ───> 完成
        └─── T-002 (1h) ───┬─── T-003 (1h) ──────┘                    │
                           └─── T-007 (0.5h) ──────────────────────────┤
                                T-009 (0.5h) ──────────────────────────┘

总耗时（关键路径）: 1h + 1.5h + 1h + 1h + 1h = 5.5h
```

**注意**: 上述是理想并行情况。实际单人开发建议按组顺序执行，总耗时 ~10.5h。

---

## 任务依赖图

```
T-001 (UI)
  ├─→ T-004 (高亮)
  ├─→ T-005 (防抖搜索)
  ├─→ T-007 (清空日志)
  └─→ T-009 (设置持久化)

T-002 (搜索引擎-普通)
  ├─→ T-003 (搜索引擎-正则)
  ├─→ T-004 (高亮)
  └─→ T-005 (防抖搜索)

T-003 (正则)
  └─→ T-005 (防抖搜索)

T-004 (高亮)
  ├─→ T-005 (防抖搜索)
  └─→ T-006 (结果导航)

T-005 (防抖搜索)
  ├─→ T-006 (结果导航)
  ├─→ T-008 (快捷键)
  └─→ T-009 (设置持久化)

T-006 (结果导航)
  └─→ T-008 (快捷键)
```

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 大量日志导致高亮卡顿 | 高 | T-004 中限制匹配数（1000）+ 批量高亮 |
| 正则表达式 DoS | 中 | T-003 中实现安全验证 + 超时机制（可选） |
| UI 布局在不同平台不一致 | 低 | T-001 测试 Windows/macOS/Linux |
| 高亮颜色与主题冲突 | 低 | 使用固定颜色（黄色/橙色）兼容性好 |

---

## 验收清单

完成所有任务后，验证以下功能：

- [ ] F-001: 搜索栏 UI 完整且美观
- [ ] F-002: 实时搜索高亮工作正常
- [ ] F-003: 大小写敏感开关生效
- [ ] F-004: 正则表达式搜索工作正常
- [ ] F-005: 结果导航（上/下一个）正常
- [ ] F-006: 匹配计数显示正确（"X / Y"）
- [ ] F-007: 清空日志功能正常（含确认对话框）
- [ ] F-008: 性能测试通过（15000 行日志 < 500ms）
- [ ] F-009: 键盘快捷键全部工作
- [ ] F-010: 设置持久化正常

---

**文档版本**: v1.0
**最后更新**: 2026-01-22
**作者**: Claude (via spec-workflow-executor)
