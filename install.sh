#!/bin/bash

echo "🚀 PicTagger 安装脚本"
echo "========================"

# 检查是否为macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ 此脚本仅支持macOS系统"
    exit 1
fi

# 检查是否为Apple Silicon
if [[ $(uname -m) != "arm64" ]]; then
    echo "⚠️  警告: 检测到非Apple Silicon处理器，性能可能不佳"
fi

echo "📋 检查系统要求..."

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，请先安装Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python版本: $PYTHON_VERSION"

# 检查Homebrew
if ! command -v brew &> /dev/null; then
    echo "❌ 未找到Homebrew，请先安装: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

echo "✅ Homebrew已安装"

# 安装Ollama
echo "📦 安装Ollama..."
if ! command -v ollama &> /dev/null; then
    brew install ollama
    echo "✅ Ollama安装完成"
else
    echo "✅ Ollama已存在"
fi

# 启动Ollama服务
echo "🔄 启动Ollama服务..."
brew services start ollama
sleep 3

# 检查Ollama是否运行
if ! pgrep -f ollama > /dev/null; then
    echo "🔄 手动启动Ollama..."
    ollama serve &
    sleep 5
fi

# 下载LLaVA模型
echo "🤖 下载LLaVA模型 (约4GB，请耐心等待)..."
ollama pull llava:7b

if [ $? -eq 0 ]; then
    echo "✅ LLaVA模型下载完成"
else
    echo "❌ 模型下载失败，请检查网络连接"
    exit 1
fi

# 安装Python依赖
echo "📦 安装Python依赖..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Python依赖安装完成"
else
    echo "❌ 依赖安装失败"
    exit 1
fi

# 创建必要目录
mkdir -p uploads
mkdir -p templates

echo ""
echo "🎉 安装完成！"
echo "========================"
echo "启动命令: python3 app.py"
echo "访问地址: http://localhost:5000"
echo ""
echo "💡 提示:"
echo "- 首次运行可能需要几分钟加载模型"
echo "- 建议图片大小控制在5MB以内"
echo "- 支持格式: JPG, PNG, WebP, BMP, TIFF"
echo ""