#!/bin/bash
# 安装脚本 - docx-mcp-server

set -e

echo "=== docx-mcp-server 安装脚本 ==="

# 检查 Python 版本
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "检测到 Python 版本: $PYTHON_VERSION"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
else
    echo "虚拟环境已存在"
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 升级 pip
echo "升级 pip..."
pip install --upgrade pip

# 安装依赖
echo "安装项目依赖..."
pip install -e .

# 创建必要的目录
echo "创建目录结构..."
mkdir -p logs
mkdir -p output

echo ""
echo "=== 安装完成 ==="
echo ""
echo "使用方法:"
echo "  1. 激活虚拟环境: source venv/bin/activate"
echo "  2. 运行服务器: mcp-server-docx"
echo "  3. 运行测试: ./scripts/test.sh"
echo ""
