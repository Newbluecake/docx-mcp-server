---
feature: gui-cwd-switch
version: 1
started_at: 2026-01-21T09:45:00Z
updated_at: 2026-01-21T09:45:00Z
---

# 规范驱动开发上下文: gui-cwd-switch

## 执行参数

```yaml
feature_name: gui-cwd-switch
planning: batch
execution: batch
complexity: standard
skip_requirements: true
no_worktree: true
verbose: false
with_review: false
```

## 当前状态

- **阶段**: Planning (Stage 2-3 进行中)
- **工作区**: 主工作区
- **分支**: master

## Planning 阶段记录

### 阶段 1: 需求分析
- 状态: 已完成（跳过，使用现有文档）
- 文档: docs/dev/gui-cwd-switch/gui-cwd-switch-requirements.md
- 复杂度: standard

### 阶段 2-3: 技术设计与任务拆分
- 状态: 进行中
- 目标文档:
  - docs/dev/gui-cwd-switch/gui-cwd-switch-design.md
  - docs/dev/gui-cwd-switch/gui-cwd-switch-tasks.md

## 技术栈发现

实际项目使用（与 requirements.md 的假设有差异）:
- GUI 框架: PyQt6（非 tkinter）
- 配置管理: QSettings（非 JSON 文件）
- 服务管理: ServerManager 类（已支持 cwd 参数）

## 现有基础设施

1. 工作目录选择: browse_cwd() 方法
2. 目录显示: cwd_input QLineEdit
3. 配置持久化: QSettings
4. 服务生命周期: ServerManager.start_server(host, port, cwd)

## 待实现功能

1. 工作目录切换时触发服务重启
2. 历史目录记录（最多 10 条）
3. 重启进度提示
4. 错误处理和回滚机制
