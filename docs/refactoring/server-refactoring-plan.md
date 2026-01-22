# 重构计划: server.py 模块化拆分

**创建日期**: 2026-01-21
**预估工作量**: 3-4 人日
**风险等级**: 中
**当前状态**: 待审阅

---

## 概要

server.py 文件包含 2,234 行代码和 33 个 MCP 工具定义，违反了单一职责原则。本重构计划将其拆分为功能模块，提升可维护性、可测试性和代码组织性。

**预期收益**:
- 代码行数减少 70%（单文件从 2,234 行降至 ~600 行）
- 模块职责清晰，符合 SOLID 原则
- 测试隔离度提升，便于单元测试
- 新功能开发更快（减少文件冲突）

---

## 当前状态分析

### 代码指标

| 指标 | 当前值 | 目标值 | 说明 |
|------|--------|--------|------|
| 代码行数 | 2,234 | <600 | 主文件仅保留启动逻辑 |
| 工具数量 | 33 | 0 | 全部迁移到功能模块 |
| 圈复杂度 | 中等 | 低 | 拆分后单个函数复杂度降低 |
| 测试覆盖率 | 85%+ | >85% | 保持或提升 |
| 模块耦合度 | 高 | 低 | 通过依赖注入解耦 |

### 识别的问题

| 问题 | 严重程度 | 位置 | 影响 |
|------|----------|------|------|
| 单文件过大 | 🔴 严重 | server.py | 难以维护、查找、测试 |
| 职责混乱 | 🔴 严重 | 全局 | 违反 SRP，修改风险高 |
| 工具分类不清 | 🟠 重要 | 33 个工具 | 难以理解功能边界 |
| 导入混乱 | 🟡 建议 | 顶部 | 依赖关系不清晰 |
| 缺少抽象层 | 🟠 重要 | 工具定义 | 重复代码多 |

### 功能分类分析

通过分析 33 个工具，识别出以下功能域：

| 功能域 | 工具数量 | 工具列表 |
|--------|----------|----------|
| **会话管理** | 4 | `docx_create`, `docx_close`, `docx_save`, `docx_get_context` |
| **内容读取** | 4 | `docx_read_content`, `docx_find_paragraphs`, `docx_list_files`, `docx_extract_template_structure` |
| **段落操作** | 6 | `docx_insert_paragraph`, `docx_insert_heading`, `docx_update_paragraph_text`, `docx_copy_paragraph`, `docx_delete`, `docx_insert_page_break` |
| **文本块操作** | 3 | `docx_insert_run`, `docx_update_run_text`, `docx_set_font` |
| **表格操作** | 9 | `docx_insert_table`, `docx_get_table`, `docx_find_table`, `docx_get_cell`, `docx_insert_paragraph_to_cell`, `docx_insert_table_row`, `docx_insert_table_col`, `docx_fill_table`, `docx_copy_table` |
| **格式化** | 4 | `docx_set_alignment`, `docx_set_properties`, `docx_format_copy`, `docx_set_margins` |
| **高级操作** | 2 | `docx_replace_text`, `docx_insert_image` |
| **系统工具** | 1 | `docx_server_status` |

---

## 重构计划

### 目标架构

```
src/docx_mcp_server/
├── server.py                    # 主入口（~100 行）
├── tools/                       # MCP 工具定义
│   ├── __init__.py             # 工具注册器
│   ├── session_tools.py        # 会话管理工具（4 个）
│   ├── content_tools.py        # 内容读取工具（4 个）
│   ├── paragraph_tools.py      # 段落操作工具（6 个）
│   ├── run_tools.py            # 文本块操作工具（3 个）
│   ├── table_tools.py          # 表格操作工具（9 个）
│   ├── format_tools.py         # 格式化工具（4 个）
│   ├── advanced_tools.py       # 高级操作工具（2 个）
│   └── system_tools.py         # 系统工具（1 个）
├── core/                        # 核心逻辑（已存在）
│   ├── session.py
│   ├── finder.py
│   ├── copier.py
│   ├── replacer.py
│   ├── format_painter.py
│   └── template_parser.py
└── utils/                       # 工具函数
    ├── decorators.py           # 通用装饰器（会话验证等）
    └── validators.py           # 参数验证器
```

### 设计原则

1. **单一职责**: 每个模块只负责一类工具
2. **依赖注入**: 通过参数传递 `session_manager`，避免全局状态
3. **装饰器模式**: 提取会话验证、日志等横切关注点
4. **向后兼容**: 保持所有工具签名不变

---

## 实施步骤

### 阶段 1: 准备阶段（0.5 人日）

**工作量**: 0.5 人日 | **风险**: 🟢 低

**步骤**:
1. 创建备份分支
   ```bash
   git checkout -b refactor-backup-20260121
   git tag backup/server-refactor-start
   git checkout master
   git checkout -b refactor/server-modularization
   ```

2. 创建目录结构
   ```bash
   mkdir -p src/docx_mcp_server/tools
   touch src/docx_mcp_server/tools/__init__.py
   ```

3. 运行完整测试套件，建立基准
   ```bash
   uv run pytest --cov=src/docx_mcp_server --cov-report=term --cov-report=html
   # 记录当前覆盖率: 85%+
   ```

**验收标准**:
- [ ] 备份分支创建成功
- [ ] 目录结构创建完成
- [ ] 所有测试通过（基准）
- [ ] 覆盖率报告生成

---

### 阶段 2: 提取通用基础设施（1 人日）

**工作量**: 1 人日 | **风险**: 🟡 中

**步骤**:

#### 2.1 创建装饰器模块

创建 `src/docx_mcp_server/utils/decorators.py`:

```python
import logging
from functools import wraps
from typing import Callable

logger = logging.getLogger(__name__)

def require_session(func: Callable) -> Callable:
    """装饰器：验证 session_id 并获取 session 对象"""
    @wraps(func)
    def wrapper(session_id: str, *args, **kwargs):
        from docx_mcp_server.core.session import session_manager

        session = session_manager.get_session(session_id)
        if not session:
            logger.error(f"{func.__name__} failed: Session {session_id} not found")
            raise ValueError(f"Session {session_id} not found")

        # 将 session 作为第一个参数传递
        return func(session, *args, **kwargs)

    return wrapper

def log_tool_call(func: Callable) -> Callable:
    """装饰器：记录工具调用日志"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"{func.__name__} called with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} success")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed: {e}")
            raise

    return wrapper
```

#### 2.2 创建工具注册器

创建 `src/docx_mcp_server/tools/__init__.py`:

```python
"""MCP 工具注册中心"""
from mcp.server.fastmcp import FastMCP

def register_all_tools(mcp: FastMCP):
    """注册所有 MCP 工具到服务器实例"""
    from . import session_tools
    from . import content_tools
    from . import paragraph_tools
    from . import run_tools
    from . import table_tools
    from . import format_tools
    from . import advanced_tools
    from . import system_tools

    # 每个模块的 register_tools() 函数会将工具注册到 mcp
    session_tools.register_tools(mcp)
    content_tools.register_tools(mcp)
    paragraph_tools.register_tools(mcp)
    run_tools.register_tools(mcp)
    table_tools.register_tools(mcp)
    format_tools.register_tools(mcp)
    advanced_tools.register_tools(mcp)
    system_tools.register_tools(mcp)
```

**验收标准**:
- [ ] 装饰器模块创建完成
- [ ] 工具注册器创建完成
- [ ] 单元测试通过

---

### 阶段 3: 迁移工具模块（1.5 人日）

**工作量**: 1.5 人日 | **风险**: 🟠 中高

**迁移顺序**（按依赖关系从低到高）:

#### 3.1 系统工具（最简单，无依赖）

创建 `src/docx_mcp_server/tools/system_tools.py`:

```python
"""系统管理工具"""
import json
import os
import sys
import time
import platform
from mcp.server.fastmcp import FastMCP

SERVER_START_TIME = time.time()
VERSION = "0.1.3"

def register_tools(mcp: FastMCP):
    """注册系统工具"""

    @mcp.tool()
    def docx_server_status() -> str:
        """获取服务器状态和环境信息"""
        from docx_mcp_server.core.session import session_manager

        info = {
            "status": "running",
            "version": VERSION,
            "cwd": os.getcwd(),
            "os_name": os.name,
            "os_system": platform.system(),
            "path_sep": os.sep,
            "python_version": sys.version,
            "start_time": SERVER_START_TIME,
            "uptime_seconds": time.time() - SERVER_START_TIME,
            "active_sessions": len(session_manager.sessions)
        }
        return json.dumps(info, indent=2)
```

#### 3.2 会话管理工具

创建 `src/docx_mcp_server/tools/session_tools.py`:

```python
"""会话管理工具"""
import json
import logging
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

def register_tools(mcp: FastMCP):
    """注册会话管理工具"""

    @mcp.tool()
    def docx_create(file_path: str = None, auto_save: bool = False) -> str:
        """创建新文档会话或加载现有文档"""
        from docx_mcp_server.core.session import session_manager

        logger.info(f"docx_create called: file_path={file_path}, auto_save={auto_save}")
        try:
            session_id = session_manager.create_session(file_path, auto_save=auto_save)
            logger.info(f"docx_create success: session_id={session_id}")
            return session_id
        except Exception as e:
            logger.error(f"docx_create failed: {e}")
            raise

    @mcp.tool()
    def docx_save(session_id: str, file_path: str) -> str:
        """保存文档到磁盘"""
        from docx_mcp_server.core.session import session_manager

        logger.info(f"docx_save called: session_id={session_id}, file_path={file_path}")
        session = session_manager.get_session(session_id)
        if not session:
            logger.error(f"docx_save failed: Session {session_id} not found")
            raise ValueError(f"Session {session_id} not found or expired")

        # 实现保存逻辑（与原代码相同）
        # ...

    # docx_close, docx_get_context 类似实现
```

#### 3.3 其他工具模块

按照相同模式迁移：
- `content_tools.py` - 内容读取工具
- `paragraph_tools.py` - 段落操作工具
- `run_tools.py` - 文本块操作工具
- `table_tools.py` - 表格操作工具
- `format_tools.py` - 格式化工具
- `advanced_tools.py` - 高级操作工具

**每个模块的模板**:

```python
"""[模块名称]工具"""
import logging
from mcp.server.fastmcp import FastMCP
from docx_mcp_server.utils.decorators import require_session, log_tool_call

logger = logging.getLogger(__name__)

def register_tools(mcp: FastMCP):
    """注册[模块名称]工具"""

    @mcp.tool()
    @log_tool_call
    def tool_name(session_id: str, ...) -> str:
        """工具文档字符串（保持原样）"""
        from docx_mcp_server.core.session import session_manager

        session = session_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # 工具实现逻辑（保持原样）
        # ...
```

**验收标准**:
- [ ] 所有 33 个工具迁移完成
- [ ] 每个模块包含 `register_tools()` 函数
- [ ] 工具签名和文档字符串保持不变
- [ ] 单元测试逐模块通过

---

### 阶段 4: 重构主文件（0.5 人日）

**工作量**: 0.5 人日 | **风险**: 🟢 低

**步骤**:

#### 4.1 简化 server.py

将 `src/docx_mcp_server/server.py` 重构为：

```python
"""DOCX MCP Server - 主入口"""
import logging
from mcp.server.fastmcp import FastMCP
from docx_mcp_server.core.session import SessionManager
from docx_mcp_server.tools import register_all_tools

logger = logging.getLogger(__name__)

# 初始化 MCP 服务器
mcp = FastMCP("docx-mcp-server")

# 全局会话管理器
session_manager = SessionManager()

# 注册所有工具
register_all_tools(mcp)

def main():
    """服务器启动入口"""
    import argparse
    parser = argparse.ArgumentParser(description="DOCX MCP Server")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "sse"])
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)

    args, unknown = parser.parse_known_args()

    if args.transport == "sse":
        print(f"Starting SSE server on {args.host}:{args.port}...", flush=True)
        mcp.settings.host = args.host
        mcp.settings.port = args.port

        if args.host not in ("127.0.0.1", "localhost"):
            mcp.settings.transport_security = None

        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
```

**代码行数对比**:
- 重构前: 2,234 行
- 重构后: ~100 行（减少 95%）

**验收标准**:
- [ ] server.py 简化完成
- [ ] 代码行数 <150 行
- [ ] 所有工具正常注册
- [ ] 服务器启动成功

---

### 阶段 5: 测试验证（0.5 人日）

**工作量**: 0.5 人日 | **风险**: 🟢 低

**步骤**:

1. **运行完整测试套件**
   ```bash
   uv run pytest --cov=src/docx_mcp_server --cov-report=term --cov-report=html
   ```

2. **验证覆盖率**
   - 目标: ≥85%（与重构前持平或提升）
   - 检查新模块是否被测试覆盖

3. **E2E 测试**
   ```bash
   uv run pytest tests/e2e/ -v
   ```

4. **手动测试**
   - 启动服务器: `uv run mcp-server-docx`
    - 测试关键工具: `docx_create`, `docx_insert_paragraph`, `docx_save`

5. **性能对比**
   - 启动时间: 应无明显变化
   - 工具调用延迟: 应无明显变化

**验收标准**:
- [ ] 所有单元测试通过（100%）
- [ ] 所有集成测试通过（100%）
- [ ] 所有 E2E 测试通过（100%）
- [ ] 覆盖率 ≥85%
- [ ] 性能无劣化

---

## 依赖关系处理

### 模块依赖图

```
server.py
    ↓
tools/__init__.py (register_all_tools)
    ↓
tools/[各功能模块].py
    ↓
core/session.py (session_manager)
    ↓
core/[其他核心模块].py
```

### 导入策略

1. **避免循环导入**:
   - `session_manager` 在 `core/session.py` 中定义
   - 工具模块通过 `from docx_mcp_server.core.session import session_manager` 导入

2. **延迟导入**:
   - 在函数内部导入 `session_manager`，避免模块加载时的循环依赖

3. **全局状态管理**:
   - `session_manager` 保持全局单例
   - 通过 `core/session.py` 统一管理

---

## 风险评估与缓解

### 技术风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 测试失败 | 中 | 高 | 逐模块迁移，每步验证测试 |
| 循环导入 | 低 | 中 | 使用延迟导入，依赖注入 |
| 性能劣化 | 低 | 中 | 性能基准测试，对比验证 |
| 向后兼容性破坏 | 低 | 高 | 保持所有工具签名不变 |

### 项目风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 工作量估算不准 | 中 | 中 | 增加 20% Buffer（3-4 人日） |
| 并行开发冲突 | 低 | 中 | 在独立分支进行，完成后合并 |

### 回滚触发条件

- 🔴 测试覆盖率下降超过 5%
- 🔴 任何 E2E 测试失败
- 🔴 性能劣化超过 10%
- 🔴 发现严重 bug 且无法快速修复

---

## 回滚计划

### 快速回滚（<5 分钟）

```bash
# 回到重构前状态
git checkout master
git reset --hard backup/server-refactor-start

# 或切换到备份分支
git checkout refactor-backup-20260121
```

### 部分回滚（保留部分改进）

```bash
# 仅回滚特定模块
git checkout master -- src/docx_mcp_server/tools/[problem_module].py
git commit -m "revert: rollback [problem_module] due to [reason]"
```

---

## 成功指标

### 代码质量指标

- [ ] 单文件代码行数 <600 行（主文件 <150 行）
- [ ] 模块数量: 8 个工具模块 + 1 个主文件
- [ ] 平均函数复杂度 <10
- [ ] 测试覆盖率 ≥85%

### 功能指标

- [ ] 所有 33 个工具正常工作
- [ ] 向后兼容性 100%（所有现有调用无需修改）
- [ ] 性能无劣化（启动时间、工具调用延迟）

### 可维护性指标

- [ ] 新增工具时只需修改 1 个文件（对应功能模块）
- [ ] 模块职责清晰，符合 SRP
- [ ] 依赖关系明确，无循环依赖

---

## 后续优化建议

### 短期（1-2 周）

1. **添加类型提示**: 为所有工具函数添加完整类型提示
2. **统一错误处理**: 创建自定义异常类，统一错误消息格式
3. **性能监控**: 添加工具调用耗时统计

### 中期（1-2 月）

1. **工具分组**: 在 MCP 客户端中按功能域分组显示工具
2. **参数验证**: 使用 Pydantic 进行参数验证
3. **文档生成**: 自动生成工具 API 文档

### 长期（3-6 月）

1. **插件系统**: 支持第三方工具扩展
2. **工具组合**: 支持工具链式调用
3. **性能优化**: 批量操作优化，减少 I/O

---

## 执行 Checkpoint

- [ ] **CP0**: 计划审阅通过，获得用户确认
- [ ] **CP1**: 备份创建完成，可安全回滚
- [ ] **CP2**: 基础设施创建完成（装饰器、注册器）
- [ ] **CP3**: 第一个模块迁移完成并测试通过
- [ ] **CP4**: 所有模块迁移完成
- [ ] **CP5**: 主文件重构完成
- [ ] **CP6**: 所有测试通过，覆盖率达标
- [ ] **CP7**: 性能验证通过，无劣化
- [ ] **CP8**: 代码审查通过，合并到主分支

---

## 附录

### A. 工具分类详细清单

#### 会话管理工具（4 个）
1. `docx_create` - 创建会话
2. `docx_close` - 关闭会话
3. `docx_save` - 保存文档
4. `docx_get_context` - 获取会话上下文

#### 内容读取工具（4 个）
1. `docx_read_content` - 读取文档内容
2. `docx_find_paragraphs` - 查找段落
3. `docx_list_files` - 列出文件
4. `docx_extract_template_structure` - 提取模板结构

#### 段落操作工具（6 个）
1. `docx_insert_paragraph` - 添加段落
2. `docx_insert_heading` - 添加标题
3. `docx_update_paragraph_text` - 更新段落文本
4. `docx_copy_paragraph` - 复制段落
5. `docx_delete` - 删除元素
6. `docx_insert_page_break` - 添加分页符

#### 文本块操作工具（3 个）
1. `docx_insert_run` - 添加文本块
2. `docx_update_run_text` - 更新文本块
3. `docx_set_font` - 设置字体

#### 表格操作工具（9 个）
1. `docx_insert_table` - 创建表格
2. `docx_get_table` - 获取表格
3. `docx_find_table` - 查找表格
4. `docx_get_cell` - 获取单元格
5. `docx_insert_paragraph_to_cell` - 单元格添加段落
6. `docx_insert_table_row` - 添加行
7. `docx_insert_table_col` - 添加列
8. `docx_fill_table` - 批量填充表格
9. `docx_copy_table` - 复制表格

#### 格式化工具（4 个）
1. `docx_set_alignment` - 设置对齐
2. `docx_set_properties` - 设置属性
3. `docx_format_copy` - 复制格式
4. `docx_set_margins` - 设置边距

#### 高级操作工具（2 个）
1. `docx_replace_text` - 替换文本
2. `docx_insert_image` - 插入图片

#### 系统工具（1 个）
1. `docx_server_status` - 服务器状态

### B. 测试文件映射

| 工具模块 | 对应测试文件 |
|---------|-------------|
| session_tools.py | test_server_lifecycle.py, test_session.py |
| content_tools.py | test_server_content.py, test_template_extraction.py |
| paragraph_tools.py | test_server_content.py, test_copy_paragraph.py |
| run_tools.py | test_server_formatting.py, test_update_text.py |
| table_tools.py | test_server_tables.py, test_tables_navigation.py |
| format_tools.py | test_server_formatting.py, test_format_painter_*.py |
| advanced_tools.py | test_replacer_image.py |
| system_tools.py | test_server_status.py |

---

**最后更新**: 2026-01-21
**审阅者**: [待填写]
**批准状态**: 待审阅
