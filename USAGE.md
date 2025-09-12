# PicTagger 使用指南

## 快速开始

### 1. 安装系统

```bash
# 方法一：使用安装脚本（推荐）
chmod +x install.sh
./install.sh

# 方法二：使用Makefile
make install

# 方法三：手动安装
brew install ollama
ollama serve
ollama pull llava:7b
pip install -r requirements.txt
```

### 2. 启动服务

```bash
# Web界面版本
make start
# 或者
./start.sh
# 或者
python app_enhanced.py

# 访问 http://localhost:5000
```

### 3. 使用CLI版本

```bash
# 分析单张图片
python cli.py image.jpg -p tuchong

# 批量处理目录
python cli.py ./photos -p shutterstock -f csv -o results.csv

# 递归处理子目录
python cli.py ./photos -r -p general --keywords-only
```

## 详细功能说明

### Web界面功能

#### 平台选择
- **通用格式**: 适合所有平台的通用描述
- **图虫网**: 针对国内摄影社区优化
- **Shutterstock**: 商业图库格式
- **Getty Images**: 新闻编辑图片格式
- **Adobe Stock**: Adobe图库格式

#### 上传模式
- **单张上传**: 逐张分析，适合精细处理
- **批量处理**: 一次处理多张图片，提高效率

#### 操作步骤
1. 选择目标平台
2. 选择上传模式
3. 拖拽或点击上传图片
4. 等待AI分析完成
5. 查看结果并复制使用

### CLI功能详解

#### 基本用法
```bash
python cli.py <输入路径> [选项]
```

#### 常用选项
- `-p, --platform`: 目标平台 (general/tuchong/shutterstock/getty/adobe_stock)
- `-o, --output`: 输出文件路径
- `-f, --format`: 输出格式 (json/csv/txt)
- `-r, --recursive`: 递归处理子目录
- `--keywords-only`: 仅输出关键词
- `--check-duplicates`: 检查重复文件
- `-v, --verbose`: 详细输出

#### 实用示例

```bash
# 为图虫网准备图片描述
python cli.py ./landscape_photos -p tuchong -f txt -o tuchong_descriptions.txt

# 批量生成Shutterstock关键词
python cli.py ./stock_photos -p shutterstock --keywords-only -o stock_keywords.txt

# 检查并处理重复图片
python cli.py ./all_photos -r --check-duplicates -v

# 生成CSV报告
python cli.py ./photos -p general -f csv -o analysis_report.csv
```

### 系统管理

#### 使用Makefile
```bash
make help          # 查看所有命令
make install       # 安装系统
make start         # 启动Web服务
make stop          # 停止服务
make clean         # 清理临时文件
make test          # 运行测试
make status        # 检查系统状态
make backup        # 备份数据
make update        # 更新模型和依赖
```

#### 检查系统状态
```bash
# 检查模型状态
python cli.py --check-model

# 下载推荐模型
python cli.py --download-model

# 运行系统测试
python test_system.py
```

## 平台特定指南

### 图虫网供稿

**特点**: 注重艺术性和情感表达

**关键词策略**:
- 中文关键词优先
- 强调情感和氛围
- 包含摄影技法描述

**示例输出**:
```
标题建议：夕阳下的宁静湖面
描述：温暖的夕阳光线洒在平静的湖面上，远山如黛，营造出宁静致远的意境
关键词：夕阳 湖面 宁静 意境 风景摄影 暖色调 倒影 远山 黄昏 自然
情感标签：宁静
色彩风格：暖色调, 橙色, 金色
```

### Shutterstock供稿

**特点**: 商业化程度高，关键词精准

**关键词策略**:
- 英文关键词为主
- 突出商业用途
- 包含技术参数

**示例输出**:
```
Title: Sunset reflection on calm lake water
Description: Beautiful golden hour lighting creates perfect reflections on tranquil lake surface with mountain silhouettes
Keywords: sunset, lake, reflection, golden hour, landscape, nature, tranquil, mountains, water, evening
Category: Nature
Commercial Use: Yes
```

### Getty Images供稿

**特点**: 新闻和编辑用途，注重真实性

**关键词策略**:
- 描述性关键词
- 地理位置信息
- 时事相关性

### Adobe Stock供稿

**特点**: 创意和设计导向

**关键词策略**:
- 设计元素描述
- 情绪和概念关键词
- 用途场景说明

## 高级技巧

### 批量处理工作流

1. **整理图片结构**
```
photos/
├── landscapes/
├── portraits/
├── products/
└── abstract/
```

2. **分类处理**
```bash
# 风景照片 - 图虫网
python cli.py photos/landscapes -p tuchong -f csv -o landscapes_tuchong.csv

# 产品照片 - Shutterstock
python cli.py photos/products -p shutterstock -f json -o products_stock.json

# 人像照片 - Adobe Stock
python cli.py photos/portraits -p adobe_stock --keywords-only -o portraits_keywords.txt
```

3. **结果整合**
```bash
# 合并所有关键词
cat *_keywords.txt | sort | uniq > all_keywords.txt

# 生成统计报告
python -c "
import json
import glob

total_images = 0
for file in glob.glob('*.json'):
    with open(file) as f:
        data = json.load(f)
        total_images += data['total_images']

print(f'总计处理图片: {total_images} 张')
"
```

### 性能优化

#### 系统配置
- **内存**: 建议16GB+，24GB更佳
- **存储**: SSD推荐，加快图片读取
- **网络**: 稳定网络连接用于模型下载

#### 处理优化
- 图片自动压缩到1024px以内
- 批量处理时建议每次不超过50张
- 大文件建议预先压缩

#### 模型选择
- **LLaVA 7B**: 平衡性能和质量（推荐）
- **LLaVA 13B**: 更高质量，需要更多内存
- **LLaVA 34B**: 最高质量，需要32GB+内存

## 故障排除

### 常见问题

#### 1. Ollama连接失败
```bash
# 检查Ollama是否运行
pgrep ollama

# 手动启动Ollama
ollama serve

# 检查端口占用
lsof -i :11434
```

#### 2. 模型下载失败
```bash
# 检查网络连接
ping ollama.ai

# 手动下载模型
ollama pull llava:7b

# 查看已安装模型
ollama list
```

#### 3. 内存不足
- 关闭其他应用程序
- 重启Ollama服务
- 考虑使用更小的模型

#### 4. 图片处理失败
- 检查图片格式是否支持
- 确认文件没有损坏
- 检查文件权限

### 日志查看
```bash
# 查看应用日志
tail -f pictagger.log

# 查看Ollama日志
ollama logs

# 系统资源监控
top -p $(pgrep ollama)
```

## 最佳实践

### 图片准备
1. **格式选择**: JPG/PNG为主，避免过大的TIFF
2. **尺寸控制**: 长边不超过2048px
3. **质量平衡**: 保持清晰度的同时控制文件大小

### 关键词优化
1. **数量控制**: 每张图片15-30个关键词
2. **相关性**: 确保关键词与图片内容高度相关
3. **层次性**: 从具体到抽象，从主要到次要

### 工作流程
1. **预处理**: 图片筛选和基础编辑
2. **批量分析**: 使用CLI进行批量处理
3. **结果审核**: 检查和调整AI生成的描述
4. **平台适配**: 根据不同平台调整格式
5. **上传发布**: 使用生成的描述和关键词

### 质量控制
1. **人工审核**: AI结果需要人工检查
2. **A/B测试**: 对比不同描述的效果
3. **持续优化**: 根据平台反馈调整策略