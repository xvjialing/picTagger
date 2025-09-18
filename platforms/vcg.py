"""
视觉中国平台格式化器
专门针对视觉中国的格式化输出
"""

from .base_formatter import BasePlatformFormatter


class VCGFormatter(BasePlatformFormatter):
    """视觉中国格式化器"""

    def format_analysis_result(self, analysis_data, language='zh'):
        """视觉中国格式化"""
        # 检查是否有错误
        error_result = self.handle_error(analysis_data, language)
        if error_result:
            return error_result

        result = []
        max_keywords = self.template_config.get('max_keywords', 50)

        if language == 'zh':
            result.append("📸 视觉中国供稿格式")
            result.append("=" * 35)
            
            # 图片标题
            title = analysis_data.get('main_subject', '')
            if title:
                result.append(f"图片标题：{title}")

            # 图片描述
            description = (
                analysis_data.get('description') or
                analysis_data.get('detailed_description', '')
            )
            if description:
                result.append(f"图片描述：{description}")

            # 图片分类
            image_type = analysis_data.get('image_type', '其他')
            result.append(f"图片分类：{image_type}")

            # 关键词 - 视觉中国支持较多关键词
            keywords = self.extract_keywords(analysis_data, max_keywords)
            
            if not keywords:
                keywords = analysis_data.get('keywords_cn', [])
            
            if keywords:
                # 确保至少有10个关键词（视觉中国要求较高）
                if len(keywords) < 10:
                    additional_keywords = []
                    if analysis_data.get('mood'):
                        additional_keywords.append(analysis_data['mood'])
                    if analysis_data.get('color_palette'):
                        additional_keywords.extend(analysis_data['color_palette'])
                    if analysis_data.get('composition'):
                        additional_keywords.append(analysis_data['composition'])
                    if analysis_data.get('lighting'):
                        additional_keywords.append(analysis_data['lighting'])
                    
                    # 补充通用关键词
                    default_keywords = ['摄影', '图片', '素材', '创意', '设计', '商业', '艺术', '视觉', '专业', '高质量']
                    keywords = self.ensure_minimum_keywords(keywords, 10, additional_keywords + default_keywords)

                result.append(f"关键词：{', '.join(keywords)}")

            # 商业用途建议
            commercial_use = analysis_data.get('commercial_use', '')
            if commercial_use:
                result.append(f"商业用途：{commercial_use}")

            # 情感色调
            mood = analysis_data.get('mood', '')
            if mood:
                result.append(f"情感色调：{mood}")

        else:
            result.append("📸 Visual China Group Format")
            result.append("=" * 35)
            
            # Image Title
            title = analysis_data.get('main_subject', '')
            if title:
                result.append(f"Image Title: {title}")

            # Image Description
            description = (
                analysis_data.get('description') or
                analysis_data.get('detailed_description', '')
            )
            if description:
                result.append(f"Image Description: {description}")

            # Image Category
            image_type = analysis_data.get('image_type', 'Other')
            result.append(f"Image Category: {image_type}")

            # Keywords
            keywords = self.extract_keywords(analysis_data, max_keywords)
            
            if not keywords:
                keywords = analysis_data.get('keywords_en', [])
            
            if keywords:
                # Ensure at least 10 keywords
                if len(keywords) < 10:
                    additional_keywords = []
                    if analysis_data.get('mood'):
                        additional_keywords.append(analysis_data['mood'])
                    if analysis_data.get('color_palette'):
                        additional_keywords.extend(analysis_data['color_palette'])
                    
                    default_keywords = ['photography', 'image', 'material', 'creative', 'design', 'commercial', 'art', 'visual', 'professional', 'high-quality']
                    keywords = self.ensure_minimum_keywords(keywords, 10, additional_keywords + default_keywords)

                result.append(f"Keywords: {', '.join(keywords)}")

            # Commercial Use
            commercial_use = analysis_data.get('commercial_use', '')
            if commercial_use:
                result.append(f"Commercial Use: {commercial_use}")

            # Mood
            mood = analysis_data.get('mood', '')
            if mood:
                result.append(f"Mood: {mood}")

        return '\n'.join(result)