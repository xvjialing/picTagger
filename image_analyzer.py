import base64
import json
from io import BytesIO
from PIL import Image
import ollama
from config import Config, PLATFORM_TEMPLATES

class ImageAnalyzer:
    def __init__(self):
        self.config = Config()
        self.model = self.config.OLLAMA_MODEL
    
    def compress_image(self, image_path, max_size=(1536, 1536), quality=90):
        """压缩图片以减少模型处理时间和内存占用，针对相机大图片优化"""
        with Image.open(image_path) as img:
            # 获取原始尺寸
            original_size = img.size
            
            # 转换为RGB（如果是RGBA或其他格式）
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 对于非常大的图片，先进行预处理
            if max(original_size) > 6000:  # 超过6000像素的大图
                # 先缩放到合理尺寸
                pre_scale = (3000, 3000)
                img.thumbnail(pre_scale, Image.Resampling.LANCZOS)
            
            # 按比例缩放到目标尺寸
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 保存到内存，提高质量以保持细节
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
            buffer.seek(0)
            
            return buffer.getvalue(), original_size, img.size
    
    def generate_platform_prompt(self, platform='general', language='zh'):
        """根据不同平台和语言生成优化的提示词"""
        
        if language == 'zh':
            # 根据平台调整分类选项
            if platform == 'tuchong' and platform in PLATFORM_TEMPLATES:
                categories = PLATFORM_TEMPLATES[platform].get('categories', [])
                category_options = '、'.join(categories)
                base_prompt = f"""请详细分析这张图片，并按以下JSON格式输出（请用中文回答）：

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
                base_prompt = """请详细分析这张图片，并按以下JSON格式输出（请用中文回答）：

{
    "image_type": "图片类型（风景/人物/动物/建筑/食物/产品/抽象/其他）",
    "main_subject": "主要内容的简洁描述",
    "detailed_description": "详细描述图片的构图、色彩、光线、氛围等",
    "keywords_cn": ["中文关键词1", "中文关键词2", "..."],
    "keywords_en": ["English keyword1", "English keyword2", "..."],
    "mood": "情感色调（积极/中性/消极/神秘/温暖/冷静等）",
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
            # 根据平台调整分类选项
            if platform == 'tuchong' and platform in PLATFORM_TEMPLATES:
                categories = PLATFORM_TEMPLATES[platform].get('categories', [])
                category_options = ', '.join(categories)
                base_prompt = f"""Please analyze this image in detail and output in the following JSON format:

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
                base_prompt = """Please analyze this image in detail and output in the following JSON format (please answer in English):

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

        if platform in PLATFORM_TEMPLATES:
            template = PLATFORM_TEMPLATES[platform]
            if language == 'zh':
                platform_prompt = f"{base_prompt}\n\n特别要求：{template['prompt_suffix']}"
                platform_prompt += f"\n关键词数量限制：{template['max_keywords']}个"
            else:
                platform_prompt = f"{base_prompt}\n\nSpecial requirements: {template['prompt_suffix']}"
                platform_prompt += f"\nKeyword limit: {template['max_keywords']} keywords"
            return platform_prompt
        
        return base_prompt
    
    def check_and_download_model(self, model_name):
        """检查模型是否存在，如果不存在则尝试下载"""
        try:
            # 检查模型是否已安装
            models = ollama.list()
            available_models = [model['name'] for model in models['models']]
            
            if model_name not in available_models:
                print(f"模型 {model_name} 未找到，正在下载...")
                # 尝试下载模型
                import subprocess
                result = subprocess.run(
                    ['ollama', 'pull', model_name],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5分钟超时
                )
                
                if result.returncode == 0:
                    print(f"模型 {model_name} 下载成功")
                    return True
                else:
                    print(f"模型 {model_name} 下载失败: {result.stderr}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"检查/下载模型时出错: {str(e)}")
            return False

    def analyze_image(self, image_path, platform='general', model=None, language='zh'):
        """使用指定模型分析图片"""
        # 如果没有指定模型，使用默认模型
        if model is None:
            model = self.model
        
        # 检查并下载模型（如果需要）
        if not self.check_and_download_model(model):
            return {
                'error': f"模型 {model} 不可用，请检查Ollama服务或手动下载模型",
                'image_info': {
                    'platform': platform
                }
            }
        
        try:
            # 压缩图片
            compressed_image, original_size, compressed_size = self.compress_image(image_path)
            
            # 转换为base64
            image_b64 = base64.b64encode(compressed_image).decode('utf-8')
            
            # 生成平台和语言特定的提示词
            prompt = self.generate_platform_prompt(platform, language)
            
            # 调用Ollama API
            response = ollama.chat(
                model=model,
                messages=[{
                    'role': 'user',
                    'content': prompt,
                    'images': [image_b64]
                }],
                options={
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'num_predict': 1000
                }
            )
            
            # 尝试解析JSON响应
            content = response['message']['content']
            
            # 提取JSON部分
            try:
                # 查找JSON开始和结束位置
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    analysis_data = json.loads(json_str)
                else:
                    # 如果没有找到JSON，返回原始文本
                    analysis_data = {"raw_response": content}
                
            except json.JSONDecodeError:
                # JSON解析失败，返回原始响应
                analysis_data = {"raw_response": content}
            
            # 添加图片元信息
            analysis_data['image_info'] = {
                'original_size': original_size,
                'compressed_size': compressed_size,
                'platform': platform
            }
            
            return analysis_data
            
        except Exception as e:
            return {
                'error': f"分析失败: {str(e)}",
                'image_info': {
                    'platform': platform
                }
            }
    
    def format_for_platform(self, analysis_data, platform='general', language='zh'):
        """根据平台要求格式化输出"""
        if 'error' in analysis_data:
            error_text = "分析失败：" if language == 'zh' else "Analysis failed: "
            return f"{error_text}{analysis_data.get('error', '未知错误')}"
        
        if platform not in PLATFORM_TEMPLATES:
            return self._format_general(analysis_data, language)
        
        template = PLATFORM_TEMPLATES[platform]
        
        if platform == 'tuchong':
            return self._format_tuchong(analysis_data, template, language)
        elif platform == 'shutterstock':
            return self._format_shutterstock(analysis_data, template, language)
        elif platform == 'getty':
            return self._format_getty(analysis_data, template, language)
        elif platform == 'adobe_stock':
            return self._format_adobe_stock(analysis_data, template, language)
        else:
            return self._format_general(analysis_data, language)
    
    def _format_general(self, data, language='zh'):
        """通用格式化"""
        if 'raw_response' in data:
            prefix = "AI分析结果：" if language == 'zh' else "AI Analysis Result:"
            return f"{prefix}\n{data['raw_response']}"
        
        result = []
        
        if language == 'zh':
            result.append(f"📷 图片类型：{data.get('image_type', '未知')}")
            result.append(f"🎯 主要内容：{data.get('main_subject', '未描述')}")
            result.append(f"📝 详细描述：{data.get('detailed_description', '未描述')}")
            
            if data.get('keywords_cn'):
                result.append(f"🏷️ 中文关键词：{', '.join(data['keywords_cn'])}")
            
            if data.get('keywords_en'):
                result.append(f"🏷️ 英文关键词：{', '.join(data['keywords_en'])}")
            
            result.append(f"😊 情感色调：{data.get('mood', '未知')}")
            result.append(f"🎨 色彩搭配：{', '.join(data.get('color_palette', []))}")
            result.append(f"📐 构图方式：{data.get('composition', '未描述')}")
            result.append(f"💡 光线效果：{data.get('lighting', '未描述')}")
            result.append(f"💼 商业用途：{data.get('commercial_use', '未建议')}")
        else:
            result.append(f"📷 Image Type: {data.get('image_type', 'Unknown')}")
            result.append(f"🎯 Main Subject: {data.get('main_subject', 'Not described')}")
            result.append(f"📝 Detailed Description: {data.get('detailed_description', 'Not described')}")
            
            if data.get('keywords_en'):
                result.append(f"🏷️ English Keywords: {', '.join(data['keywords_en'])}")
            
            if data.get('keywords_cn'):
                result.append(f"🏷️ Chinese Keywords: {', '.join(data['keywords_cn'])}")
            
            result.append(f"😊 Mood: {data.get('mood', 'Unknown')}")
            result.append(f"🎨 Color Palette: {', '.join(data.get('color_palette', []))}")
            result.append(f"📐 Composition: {data.get('composition', 'Not described')}")
            result.append(f"💡 Lighting: {data.get('lighting', 'Not described')}")
            result.append(f"💼 Commercial Use: {data.get('commercial_use', 'Not suggested')}")
        
        return '\n'.join(result)
    
    def _format_tuchong(self, data, template, language='zh'):
        """图虫网格式化 - 只保留图片分类、图片说明、图片关键字"""
        result = []
        if language == 'zh':
            # 图片分类
            image_type = data.get('image_type', '其他')
            result.append(f"图片分类：{image_type}")
            
            # 图片说明
            description = data.get('description', data.get('detailed_description', data.get('main_subject', '')))
            if description:
                result.append(f"图片说明：{description}")
            
            # 图片关键字 - 至少5个以上
            keywords = data.get('keywords', data.get('keywords_cn', []))
            if not keywords:
                # 如果没有keywords字段，尝试从其他字段获取
                keywords = data.get('keywords_en', [])
            
            if keywords:
                # 确保至少有5个关键词
                if len(keywords) < 5:
                    # 如果关键词不足5个，可以从其他字段补充
                    additional_keywords = []
                    if data.get('mood'):
                        additional_keywords.append(data['mood'])
                    if data.get('color_palette'):
                        additional_keywords.extend(data['color_palette'][:2])  # 最多取2个颜色
                    keywords.extend(additional_keywords)
                
                # 限制关键词数量不超过模板限制
                keywords = keywords[:template['max_keywords']]
                result.append(f"图片关键字：{', '.join(keywords)}")
            else:
                result.append("图片关键字：暂无")
                
        else:
            # Image Category
            image_type = data.get('image_type', 'Other')
            result.append(f"Image Category: {image_type}")
            
            # Image Description
            description = data.get('description', data.get('detailed_description', data.get('main_subject', '')))
            if description:
                result.append(f"Image Description: {description}")
            
            # Image Keywords - at least 5
            keywords = data.get('keywords', data.get('keywords_en', []))
            if not keywords:
                keywords = data.get('keywords_cn', [])
            
            if keywords:
                # Ensure at least 5 keywords
                if len(keywords) < 5:
                    additional_keywords = []
                    if data.get('mood'):
                        additional_keywords.append(data['mood'])
                    if data.get('color_palette'):
                        additional_keywords.extend(data['color_palette'][:2])
                    keywords.extend(additional_keywords)
                
                keywords = keywords[:template['max_keywords']]
                result.append(f"Image Keywords: {', '.join(keywords)}")
            else:
                result.append("Image Keywords: None")
        
        return '\n'.join(result)
    
    def _format_shutterstock(self, data, template, language='zh'):
        """Shutterstock格式化"""
        result = []
        if language == 'zh':
            result.append("📸 Shutterstock供稿格式")
            result.append("=" * 35)
            result.append(f"标题：{data.get('main_subject', '专业库存照片')}")
            result.append(f"描述：{data.get('detailed_description', '')}")
            
            keywords = data.get('keywords_en', [])
            if keywords:
                keywords = keywords[:template['max_keywords']]
                result.append(f"关键词：{', '.join(keywords)}")
            
            result.append(f"类别：{data.get('image_type', '通用')}")
            result.append(f"商业用途：{data.get('commercial_use', '是')}")
        else:
            result.append("📸 Shutterstock Format")
            result.append("=" * 35)
            result.append(f"Title: {data.get('main_subject', 'Professional Stock Photo')}")
            result.append(f"Description: {data.get('detailed_description', '')}")
            
            keywords = data.get('keywords_en', [])
            if keywords:
                keywords = keywords[:template['max_keywords']]
                result.append(f"Keywords: {', '.join(keywords)}")
            
            result.append(f"Category: {data.get('image_type', 'General')}")
            result.append(f"Commercial Use: {data.get('commercial_use', 'Yes')}")
        
        return '\n'.join(result)
    
    def _format_getty(self, data, template, language='zh'):
        """Getty Images格式化"""
        result = []
        if language == 'zh':
            result.append("🏛️ Getty Images供稿格式")
            result.append("=" * 35)
            result.append(f"标题：{data.get('main_subject', '')}")
            result.append(f"说明：{data.get('detailed_description', '')}")
            
            keywords = data.get('keywords_en', [])
            if keywords:
                keywords = keywords[:template['max_keywords']]
                result.append(f"关键词：{', '.join(keywords)}")
            
            result.append(f"编辑用途：{data.get('target_audience', '大众')}")
        else:
            result.append("🏛️ Getty Images Format")
            result.append("=" * 35)
            result.append(f"Headline: {data.get('main_subject', '')}")
            result.append(f"Caption: {data.get('detailed_description', '')}")
            
            keywords = data.get('keywords_en', [])
            if keywords:
                keywords = keywords[:template['max_keywords']]
                result.append(f"Keywords: {', '.join(keywords)}")
            
            result.append(f"Editorial Use: {data.get('target_audience', 'General Public')}")
        
        return '\n'.join(result)
    
    def _format_adobe_stock(self, data, template, language='zh'):
        """Adobe Stock格式化"""
        result = []
        if language == 'zh':
            result.append("🎨 Adobe Stock供稿格式")
            result.append("=" * 35)
            result.append(f"标题：{data.get('main_subject', '')}")
            result.append(f"描述：{data.get('detailed_description', '')}")
            
            keywords = data.get('keywords_en', [])
            if keywords:
                keywords = keywords[:template['max_keywords']]
                result.append(f"关键词：{', '.join(keywords)}")
            
            result.append(f"类别：{data.get('image_type', '')}")
            result.append(f"情感：{data.get('mood', '')}")
        else:
            result.append("🎨 Adobe Stock Format")
            result.append("=" * 35)
            result.append(f"Title: {data.get('main_subject', '')}")
            result.append(f"Description: {data.get('detailed_description', '')}")
            
            keywords = data.get('keywords_en', [])
            if keywords:
                keywords = keywords[:template['max_keywords']]
                result.append(f"Keywords: {', '.join(keywords)}")
            
            result.append(f"Category: {data.get('image_type', '')}")
            result.append(f"Mood: {data.get('mood', '')}")
        
        return '\n'.join(result)