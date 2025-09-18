"""
图虫网平台格式化器
专门针对图虫网的格式化输出
"""

from .base_formatter import BasePlatformFormatter


class TuchongFormatter(BasePlatformFormatter):
    """图虫网格式化器 - 只保留图片分类、图片说明、图片关键字"""

    def format_analysis_result(self, analysis_data, language='zh'):
        """图虫网格式化"""
        # 检查是否有错误
        error_result = self.handle_error(analysis_data, language)
        if error_result:
            return error_result

        result = []
        max_keywords = self.template_config.get('max_keywords', 30)

        if language == 'zh':
            # 图片分类
            image_type = analysis_data.get('image_type', '其他')
            result.append(f"图片分类：{image_type}")

            # 图片说明
            description = (
                analysis_data.get('description') or
                analysis_data.get('detailed_description') or
                analysis_data.get('main_subject', '')
            )
            if description:
                result.append(f"图片说明：{description}")

            # 图片关键字 - 至少5个以上
            keywords = self.extract_keywords(analysis_data, max_keywords)

            if not keywords:
                # 如果没有keywords字段，尝试从其他字段获取
                keywords = analysis_data.get('keywords_en', [])

            if keywords:
                # 确保至少有5个关键词
                if len(keywords) < 5:
                    # 如果关键词不足5个，可以从其他字段补充
                    additional_keywords = []
                    if analysis_data.get('mood'):
                        additional_keywords.append(analysis_data['mood'])
                    if analysis_data.get('color_palette'):
                        additional_keywords.extend(analysis_data['color_palette'][:2])  # 最多取2个颜色
                    keywords = self.ensure_minimum_keywords(keywords, 5, additional_keywords)

                result.append(f"图片关键字：{', '.join(keywords)}")
            else:
                result.append("图片关键字：暂无")

        else:
            # Image Category
            image_type = analysis_data.get('image_type', 'Other')
            result.append(f"Image Category: {image_type}")

            # Image Description
            description = (
                analysis_data.get('description') or
                analysis_data.get('detailed_description') or
                analysis_data.get('main_subject', '')
            )
            if description:
                result.append(f"Image Description: {description}")

            # Image Keywords - at least 5
            keywords = self.extract_keywords(analysis_data, max_keywords)

            if not keywords:
                keywords = analysis_data.get('keywords_cn', [])

            if keywords:
                # Ensure at least 5 keywords
                if len(keywords) < 5:
                    additional_keywords = []
                    if analysis_data.get('mood'):
                        additional_keywords.append(analysis_data['mood'])
                    if analysis_data.get('color_palette'):
                        additional_keywords.extend(analysis_data['color_palette'][:2])
                    keywords = self.ensure_minimum_keywords(
                        keywords, 5,
                        ['photography', 'image', 'material', 'creative', 'design']
                    )

                result.append(f"Image Keywords: {', '.join(keywords)}")
            else:
                result.append("Image Keywords: None")

        return '\n'.join(result)