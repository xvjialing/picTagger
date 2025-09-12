#!/bin/bash

echo "🚀 启动 PicTagger Enhanced"
echo "=========================="

# 检查Ollama是否运行
if ! pgrep -f ollama > /dev/null; then
    echo "🔄 启动 Ollama 服务..."
    ollama serve &
    sleep 3
fi

# 检查LLaVA模型是否存在
if ! ollama list | grep -q "llava"; then
    echo "⚠️  未找到 LLaVA 模型"
    echo "📥 正在下载 LLaVA 模型 (约4GB)..."
    ollama pull llava:7b
fi

# 检查Python依赖
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

echo "🔧 激活虚拟环境..."
source venv/bin/activate

echo "📦 安装/更新依赖..."
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 创建必要目录
mkdir -p uploads
mkdir -p templates

echo "🌐 启动 Web 服务..."
echo "访问地址: http://localhost:5000"
echo "按 Ctrl+C 停止服务"
echo ""

python app_enhanced.py