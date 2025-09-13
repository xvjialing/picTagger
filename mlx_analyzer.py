"""
MLX优化的图片分析器
针对Apple Silicon芯片优化，提供更快的推理速度
"""

import os
import json
import base64
from io import BytesIO
from PIL import Image

try:
    import mlx.core as mx
    from mlx_vlm import load, generate
    from mlx_vlm.utils import load_config
    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False
    print("⚠️ MLX库未安装，将使用Ollama作为后备方案")

from config import PLATFORM_TEMPLATES

class MLXImageAnalyzer:
    def __init__(self, model_name="mlx-community/llava-1.5-7b-4bit"):
        """初始化MLX图片分析器"""
        self.model_name = model_name
        self.model = None
        self.processor = None
        self.config = None
        self.mlx_available = MLX_AVAILABLE
        
        if self.mlx_available:
            self._load_model()
        else:
            print("🔄 MLX不可用，请先安装: pip install mlx-lm mlx-vlm")
    
    def _load_model(self):
        """加载MLX优化的模型"""
        try:
            print(f"🚀 正在加载MLX模型: {self.model_name}")
            self.model, self.processor = load(self.model_name)
            self.config = load_config(self.model_name)
            print(f"✅ MLX模型加载成功: {self.model_name}")
        except Exception as e:
            print(f"❌ MLX模型加载失败: {str(e)}")
            self.model = None
            self.processor = None
    
    def compress_image(self, image_path, max_size=(1536, 1536), quality=90):
        """压缩图片以优化处理速度"""
        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                original_size = img.size
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                buffer = BytesIO()
                img.save(buffer, format='JPEG', quality=quality, optimize=True)
                compressed_data = buffer.getvalue()
                
                return compressed_data, original_size, img.size
        except Exception as e:
            print(f"图片压缩失败: {str(e)}")
            with open(image_path, 'rb') as f:
                data = f.read()
                return data, (0, 0), (0, 0)
    
    def generate_platform_prompt(self, platform='general', language='zh'):
        """生成平台特定的分析提示词"""
        if language == 'zh':
            if platform == 'tuchong' and platform in PLATFORM_TEMPLATES:
                categories = PLATFORM_TEMPLATES[platform].get('categories', [])
                category_options = '、'.join(categories)
                return f"""请详细分析这张图片，并按以下JSON格式输出（请用中文回答）：

{{
    "image_type": "图片分类，必须从以下选项中选择一个：{category_options}。如果识别不出具体分类，请选择'其他'",
    "description": "图片说明，简洁明了地描述图片的主要内容和特点",
    "keywords": ["关键词1", "关键词2", "关键词3", "关键词4", "关键词5", "关键词6", "关键词7", "..."]
}}

重要要求：
1. image_type字段必须严格从给定的12个分类选项中选择，不能使用其他分类
2. 如果无法确定具体分类，请选择"其他"
3. keywords字段必须包含至少5个以上的关键词，用于描述图片内容、风格、色彩、情感等
4. 所有内容都用中文输出
5. 请根据图片内容仔细选择最合适的分类"""
            else:
                return """请详细分析这张图片，并按以下JSON格式输出（请用中文回答）：

{
    "image_type": "图片类型（风景/人物/动物/建筑/美食/产品/抽象/其他）",
    "main_subject": "主要内容简述",
    "detailed_description": "详细描述构图、色彩、光线、氛围等",
    "keywords_cn": ["中文关键词1", "中文关键词2", "..."],
    "keywords_en": ["English keyword1", "English keyword2", "..."],
    "mood": "情感基调（积极/中性/消极/神秘/温暖/平静等）",
    "color_palette": ["主要颜色1", "主要颜色2", "..."],
    "composition": "构图描述（三分法/对称/引导线等）",
    "lighting": "光线描述（自然光/人工光/逆光/侧光等）",
    "commercial_use": "商业用途建议",
    "target_audience": "目标受众",
    "seasonal": "季节性（如适用）",
    "location_type": "场景类型（室内/室外/工作室等）"
}

重要：请确保所有描述性文字都使用中文，关键词部分提供中英文两个版本。"""
        else:
            if platform == 'tuchong' and platform in PLATFORM_TEMPLATES:
                categories = PLATFORM_TEMPLATES[platform].get('categories', [])
                category_options = ', '.join(categories)
                return f"""Please analyze this image in detail and output in the following JSON format:

{{
    "image_type": "Image category, must choose one from: {category_options}. If cannot identify specific category, choose 'Other'",
    "description": "Image description, concisely describe the main content and characteristics of the image",
    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6", "keyword7", "..."]
}}

Important requirements:
1. The image_type field must strictly choose from the given 12 category options, no other categories allowed
2. If unable to determine specific category, choose "Other"
3. The keywords field must contain at least 5 or more keywords describing image content, style, colors, emotions, etc.
4. All content should be in Chinese
5. Please carefully select the most appropriate category based on the image content"""
            else:
                return """Please analyze this image in detail and output in the following JSON format (please answer in English):

{
    "image_type": "Image type (landscape/portrait/animal/architecture/food/product/abstract/other)",
    "main_subject": "Brief description of main content",
    "detailed_description": "Detailed description of composition, colors, lighting, atmosphere, etc.",
    "keywords_cn": ["Chinese keyword1", "Chinese keyword2", "..."],
    "keywords_en": ["English keyword1", "English keyword2", "..."],
    "mood": "Emotional tone (positive/neutral/negative/mysterious/warm/calm, etc.)",
    "color_palette": ["Main color1", "Main color2", "..."],
    "composition": "Composition description (rule of thirds/symmetry/leading lines, etc.)",
    "lighting": "Lighting description (natural light/artificial light/backlight/side light, etc.)",
    "commercial_use": "Commercial use suggestions",
    "target_audience": "Target audience",
    "seasonal": "Seasonality (if applicable)",
    "location_type": "Scene type (indoor/outdoor/studio, etc.)"
}

Important: Please ensure all descriptive text is in English, and provide both Chinese and English versions for keywords."""
    
    def analyze_image(self, image_path, platform='general', model=None, language='zh'):
        """使用MLX优化模型分析图片"""
        if not self.mlx_available or self.model is None:
            return {
                'error': "MLX模型未加载，请检查MLX安装或使用Ollama",
                'image_info': {'platform': platform, 'engine': 'MLX_UNAVAILABLE'}
            }
        
        try:
            print(f"🔍 开始MLX图片分析: {os.path.basename(image_path)}")
            
            # 压缩图片
            compressed_image, original_size, compressed_size = self.compress_image(image_path)
            image = Image.open(BytesIO(compressed_image))
            
            # 生成提示词
            prompt = self.generate_platform_prompt(platform, language)
            
            print("🤖 正在使用MLX进行推理...")
            
            # 使用MLX进行推理
            response = generate(
                model=self.model,
                processor=self.processor,
                image=image,
                prompt=prompt,
                max_tokens=1000,
                temperature=0.7,
                verbose=False
            )
            
            print("✅ MLX推理完成")
            
            # 解析JSON响应
            try:
                response_text = response.strip()
                if '```json' in response_text:
                    json_start = response_text.find('```json') + 7
                    json_end = response_text.find('```', json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif '{' in response_text:
                    json_start = response_text.find('{')
                    json_end = response_text.rfind('}') + 1
                    response_text = response_text[json_start:json_end]
                
                analysis_result = json.loads(response_text)
                
                return {
                    'success': True,
                    'analysis': analysis_result,
                    'image_info': {
                        'original_size': original_size,
                        'compressed_size': compressed_size,
                        'platform': platform,
                        'model': self.model_name,
                        'engine': 'MLX'
                    }
                }
                
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {str(e)}")
                return {
                    'success': True,
                    'analysis': {
                        'raw_response': response,
                        'image_type': '其他',
                        'main_subject': '图片分析',
                        'detailed_description': response[:200] + '...' if len(response) > 200 else response,
                        'keywords_cn': ['图片', '分析'],
                        'keywords_en': ['image', 'analysis']
                    },
                    'image_info': {
                        'original_size': original_size,
                        'compressed_size': compressed_size,
                        'platform': platform,
                        'model': self.model_name,
                        'engine': 'MLX',
                        'note': 'JSON解析失败，返回原始响应'
                    }
                }
                
        except Exception as e:
            print(f"MLX分析失败: {str(e)}")
            return {
                'error': f"分析失败: {str(e)}",
                'image_info': {
                    'platform': platform,
                    'model': self.model_name,
                    'engine': 'MLX'
                }
            }
    
    def get_available_models(self):
        """获取可用的MLX模型列表"""
        return [
            "mlx-community/llava-1.5-7b-4bit",
            "mlx-community/llava-1.5-13b-4bit", 
            "mlx-community/llava-1.6-mistral-7b-4bit",
            "mlx-community/llava-1.6-vicuna-7b-4bit",
            "mlx-community/qwen2-vl-7b-instruct-4bit"
        ]