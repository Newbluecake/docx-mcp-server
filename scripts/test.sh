#!/bin/bash
# 测试脚本 - docx-mcp-server

set -e

echo "=== docx-mcp-server 测试脚本 ==="

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "错误: 虚拟环境不存在，请先运行 ./scripts/install.sh"
    exit 1
fi

# 运行单元测试
echo ""
echo "运行单元测试..."
python -m pytest tests/unit/ -v

# 运行 E2E 测试
echo ""
echo "运行 E2E 测试..."
python -m pytest tests/e2e/ -v

echo ""
echo "=== 所有测试通过 ==="
