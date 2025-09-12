# PicTagger - 智能图片标签生成器

基于本地AI模型的图片识别和描述生成工具，专为图片供稿平台优化。

## 特性

- 🖼️ 智能图片识别和分类
- 📝 自动生成图片描述和关键词
- 🏷️ 适配国内外图片供稿平台（图虫、Shutterstock等）
- 💻 完全本地运行，保护隐私
- 🚀 针对Apple Silicon (M4) 优化

## 系统要求

- macOS (Apple Silicon推荐)
- 16GB+ 内存 (24GB更佳)
- Python 3.8+
- Ollama

## 快速开始

### 1. 安装依赖

```bash
# 安装Ollama
brew install ollama

# 启动Ollama服务
ollama serve

# 下载LLaVA模型 (约4GB)
ollama pull llava:7b

# 安装Python依赖
pip install -r requirements.txt
```

### 2. 运行应用

```bash
python app.py
```

访问 http://localhost:5000 开始使用。

## 支持的图片格式

- JPEG/JPG
- PNG
- WebP
- BMP
- TIFF

## 模型说明

使用LLaVA-1.6 7B模型，专门针对视觉理解任务优化：
- 模型大小: ~4GB
- 内存占用: ~6-8GB
- 推理速度: 2-5秒/张 (M4)

## 许可证

MIT License