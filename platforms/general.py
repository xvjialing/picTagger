"""
通用平台格式化器
提供通用的分析结果格式化
"""

from .base_formatter import BasePlatformFormatter


class GeneralFormatter(BasePlatformFormatter):
    """通用格式化器"""

    def format_analysis_result(self, analysis_data, language='zh'):
        """通用格式化"""
        # 检查是否有错误
        error_result = self.handle_error(analysis_data, language)
        if error_result:
            return error_result

        if 'raw_response' in analysis_data:
            prefix = "AI分析结果：" if language == 'zh' else "AI Analysis Result:"
            return f"{prefix}\n{analysis_data['raw_response']}"

        result = []

        if language == 'zh':
            result.append(f"📷 图片类型：{analysis_data.get('image_type', '未知')}")
            result.append(f"🎯 主要内容：{analysis_data.get('main_subject', '未描述')}")
            result.append(f"📝 详细描述：{analysis_data.get('detailed_description', '未描述')}")

            if analysis_data.get('keywords_cn'):
                result.append(f"🏷️ 中文关键词：{', '.join(analysis_data['keywords_cn'])}")

            if analysis_data.get('keywords_en'):
                result.append(f"🏷️ 英文关键词：{', '.join(analysis_data['keywords_en'])}")

            result.append(f"😊 情感色调：{analysis_data.get('mood', '未知')}")

            if analysis_data.get('color_palette'):
                result.append(f"🎨 色彩搭配：{', '.join(analysis_data['color_palette'])}")

            result.append(f"📐 构图方式：{analysis_data.get('composition', '未描述')}")
            result.append(f"💡 光线效果：{analysis_data.get('lighting', '未描述')}")
            result.append(f"💼 商业用途：{analysis_data.get('commercial_use', '未建议')}")
        else:
            result.append(f"📷 Image Type: {analysis_data.get('image_type', 'Unknown')}")
            result.append(f"🎯 Main Subject: {analysis_data.get('main_subject', 'Not described')}")
            result.append(f"📝 Detailed Description: {analysis_data.get('detailed_description', 'Not described')}")

            if analysis_data.get('keywords_en'):
                result.append(f"🏷️ English Keywords: {', '.join(analysis_data['keywords_en'])}")

            if analysis_data.get('keywords_cn'):
                result.append(f"🏷️ Chinese Keywords: {', '.join(analysis_data['keywords_cn'])}")

            result.append(f"😊 Mood: {analysis_data.get('mood', 'Unknown')}")

            if analysis_data.get('color_palette'):
                result.append(f"🎨 Color Palette: {', '.join(analysis_data['color_palette'])}")

            result.append(f"📐 Composition: {analysis_data.get('composition', 'Not described')}")
            result.append(f"💡 Lighting: {analysis_data.get('lighting', 'Not described')}")
            result.append(f"💼 Commercial Use: {analysis_data.get('commercial_use', 'Not suggested')}")

        return '\n'.join(result)