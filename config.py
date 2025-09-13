import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Ollama配置
    OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen2.5vl:7b')
    
    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_FILE_SIZE', 100 * 1024 * 1024))  # 增加到100MB
    
    # 上传配置
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    
    # 图片处理配置
    MAX_IMAGE_SIZE = int(os.getenv('MAX_IMAGE_SIZE', 1536))  # 增加到1536以更好处理大图
    IMAGE_QUALITY = int(os.getenv('IMAGE_QUALITY', 90))     # 提高质量保持细节
    
    # 批量处理配置
    MAX_BATCH_SIZE = int(os.getenv('MAX_BATCH_SIZE', 50))  # 增加到50张
    
    # 支持的文件格式
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'tiff'}

# 支持的模型列表
SUPPORTED_MODELS = {
    'qwen2.5vl:7b': {
        'name': 'Qwen2.5-VL 7B',
        'description': '阿里通义千问视觉语言模型，中文效果优秀',
        'size': '约4.7GB'
    },
    'llava:latest': {
        'name': 'LLaVA Latest',
        'description': '最新版本的LLaVA视觉语言模型',
        'size': '约4.7GB'
    },
    'llava:7b': {
        'name': 'LLaVA 7B',
        'description': '轻量级视觉语言模型，速度快',
        'size': '约4.7GB'
    },
    'llava:13b': {
        'name': 'LLaVA 13B', 
        'description': '更强大的视觉语言模型，精度更高',
        'size': '约7GB'
    },
    'llava:34b': {
        'name': 'LLaVA 34B',
        'description': '最强大的LLaVA模型，精度最高',
        'size': '约20GB'
    },
    'llava-llama3:8b': {
        'name': 'LLaVA Llama3 8B',
        'description': '基于Llama3的LLaVA模型',
        'size': '约5GB'
    },
    'moondream:1.8b': {
        'name': 'Moondream 1.8B',
        'description': '轻量级视觉模型，速度极快',
        'size': '约1.8GB'
    }
}

# 图片供稿平台关键词模板
PLATFORM_TEMPLATES = {
    'shutterstock': {
        'max_keywords': 50,
        'language': 'en',
        'style': 'commercial',
        'prompt_suffix': 'Generate commercial stock photo keywords in English.'
    },
    'tuchong': {
        'max_keywords': 30,
        'language': 'zh',
        'style': 'artistic',
        'prompt_suffix': '生成适合图虫网的中文艺术摄影关键词。',
        'categories': [
            '城市风光', '自然风光', '野生动物', '静物美食', 
            '动物萌宠', '商务肖像', '生活方式', '室内空间', 
            '生物医疗', '运动健康', '节日假日', '其他'
        ]
    },
    'getty': {
        'max_keywords': 40,
        'language': 'en',
        'style': 'editorial',
        'prompt_suffix': 'Generate editorial and news-worthy keywords in English.'
    },
    'adobe_stock': {
        'max_keywords': 45,
        'language': 'en',
        'style': 'versatile',
        'prompt_suffix': 'Generate versatile stock photo keywords for Adobe Stock.'
    }
}