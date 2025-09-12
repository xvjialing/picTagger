# PicTagger Makefile

.PHONY: install start stop clean test help setup-dev

# 默认目标
help:
	@echo "PicTagger - 智能图片标签生成器"
	@echo "================================"
	@echo "可用命令:"
	@echo "  make install     - 安装所有依赖和模型"
	@echo "  make start       - 启动Web服务"
	@echo "  make start-cli   - 启动CLI版本"
	@echo "  make stop        - 停止所有服务"
	@echo "  make clean       - 清理临时文件"
	@echo "  make test        - 运行测试"
	@echo "  make setup-dev   - 设置开发环境"
	@echo "  make backup      - 备份结果数据"
	@echo "  make update      - 更新模型和依赖"

# 安装
install:
	@echo "🚀 开始安装 PicTagger..."
	@chmod +x install.sh
	@./install.sh

# 启动Web服务
start:
	@echo "🌐 启动Web服务..."
	@chmod +x start.sh
	@./start.sh

# 启动CLI版本
start-cli:
	@echo "💻 CLI版本使用方法:"
	@echo "python cli.py <图片路径> [选项]"
	@echo "例如: python cli.py ./test_images -p tuchong -f csv"

# 停止服务
stop:
	@echo "🛑 停止服务..."
	@pkill -f "python.*app" || true
	@pkill -f "ollama serve" || true
	@echo "✅ 服务已停止"

# 清理
clean:
	@echo "🧹 清理临时文件..."
	@rm -rf uploads/*
	@rm -rf __pycache__/
	@rm -rf *.pyc
	@rm -rf .pytest_cache/
	@rm -rf pictagger.log
	@echo "✅ 清理完成"

# 测试
test:
	@echo "🧪 运行测试..."
	@python -m pytest tests/ -v || echo "请先创建测试文件"

# 开发环境设置
setup-dev:
	@echo "🔧 设置开发环境..."
	@python -m venv venv
	@source venv/bin/activate && pip install -r requirements.txt
	@source venv/bin/activate && pip install pytest black flake8
	@echo "✅ 开发环境设置完成"

# 备份数据
backup:
	@echo "💾 备份结果数据..."
	@mkdir -p backups
	@tar -czf backups/pictagger_backup_$(shell date +%Y%m%d_%H%M%S).tar.gz uploads/ *.json *.csv *.txt || true
	@echo "✅ 备份完成"

# 更新
update:
	@echo "🔄 更新模型和依赖..."
	@ollama pull llava:7b
	@pip install -r requirements.txt --upgrade
	@echo "✅ 更新完成"

# 检查系统状态
status:
	@echo "📊 系统状态检查..."
	@echo "Ollama服务: $(shell pgrep -f ollama > /dev/null && echo '✅ 运行中' || echo '❌ 未运行')"
	@echo "Python环境: $(shell python --version 2>/dev/null || echo '❌ 未找到')"
	@echo "可用模型: $(shell ollama list 2>/dev/null | grep llava | wc -l | tr -d ' ') 个"
	@echo "上传文件: $(shell ls uploads/ 2>/dev/null | wc -l | tr -d ' ') 个"

# 快速演示
demo:
	@echo "🎬 运行演示..."
	@mkdir -p demo_images
	@echo "请将测试图片放入 demo_images/ 目录"
	@echo "然后运行: python cli.py demo_images -p tuchong -v"