"""
Adobe Stock平台格式化器
"""

from .base_formatter import BasePlatformFormatter


class AdobeStockFormatter(BasePlatformFormatter):
    """Adobe Stock格式化器"""

    def format_analysis_result(self, analysis_data, language='zh'):
        """Adobe Stock格式化"""
        # 检查是否有错误
        error_result = self.handle_error(analysis_data, language)
        if error_result:
            return error_result

        result = []
        max_keywords = self.template_config.get('max_keywords', 45)

        if language == 'zh':
            result.append("🎨 Adobe Stock供稿格式")
            result.append("=" * 35)
            result.append(f"标题：{analysis_data.get('main_subject', '')}")
            result.append(f"描述：{analysis_data.get('detailed_description', '')}")

            keywords = analysis_data.get('keywords_en', [])
            if keywords:
                keywords = self.extract_keywords({'keywords_en': keywords}, max_keywords)
                result.append(f"关键词：{', '.join(keywords)}")

            result.append(f"类别：{analysis_data.get('image_type', '')}")
            result.append(f"情感：{analysis_data.get('mood', '')}")
        else:
            result.append("🎨 Adobe Stock Format")
            result.append("=" * 35)
            result.append(f"Title: {analysis_data.get('main_subject', '')}")
            result.append(f"Description: {analysis_data.get('detailed_description', '')}")

            keywords = analysis_data.get('keywords_en', [])
            if keywords:
                keywords = self.extract_keywords({'keywords_en': keywords}, max_keywords)
                result.append(f"Keywords: {', '.join(keywords)}")

            result.append(f"Category: {analysis_data.get('image_type', '')}")
            result.append(f"Mood: {analysis_data.get('mood', '')}")

        return '\n'.join(result)