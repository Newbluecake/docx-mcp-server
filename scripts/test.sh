#!/bin/bash
# 测试脚本 - docx-mcp-server

set -e

echo "=== docx-mcp-server 测试脚本 ==="

# 设置 QT 平台为 offscreen，避免在无头环境中 GUI 测试失败
# 如果用户已设置该变量，则使用用户设置
export QT_QPA_PLATFORM=${QT_QPA_PLATFORM:-offscreen}

# 运行所有测试
echo "运行所有测试 (unit, integration, e2e)..."
uv run pytest "$@"

echo ""
echo "=== 所有测试通过 ==="
