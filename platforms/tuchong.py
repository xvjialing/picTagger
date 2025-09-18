"""
图虫网平台格式化器
专门针对图虫网的格式化输出
"""

from .base_formatter import BasePlatformFormatter


def optimize_description_length(description, min_length=5, max_length=50):
    """优化描述长度，确保在指定范围内"""
    cleaned = clean_description(description) if description else '精美图片'
    length = len(cleaned)

    if length >= min_length and length <= max_length:
        return cleaned
    elif length < min_length:
        if '风景' in cleaned or '景色' in cleaned:
            return '精美的' + cleaned
        elif '人物' in cleaned:
            return '专业的' + cleaned
        else:
            return '精美的' + cleaned
    else:
        # 智能截取，优先在标点符号处
        punctuation = ['，', '。', '、', '；']
        for i in range(max_length - 1, max_length // 2, -1):
            if i < len(cleaned) and cleaned[i] in punctuation:
                return cleaned[:i]
        return cleaned[:max_length]

def clean_description(description):

    # 定义需要去除的前缀模式
    redundant_prefixes = [
        '图片展示了',
        '图片显示了',
        '图片描述了',
        '这张图片',
        '图片中',
        '图片里',
        '画面中',
        '画面里',
        '照片中',
        '照片里',
        '图像中',
        '图像里',
        '此图',
        '本图',
        '图中',
        '图里'
    ]

    # 去除前缀
    cleaned = description.strip()
    for prefix in redundant_prefixes:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
            # 如果去除前缀后以"是"、"为"、"有"等开头，也去除
            if cleaned.startswith('是'):
                cleaned = cleaned[1:].strip()
            elif cleaned.startswith('为'):
                cleaned = cleaned[1:].strip()
            elif cleaned.startswith('有'):
                cleaned = cleaned[1:].strip()
            break

    return cleaned if cleaned else description


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
                # 优化描述长度，确保在5-50字符范围内
                optimized_description = optimize_description_length(description)
                result.append(f"图片说明：{optimized_description}")
            else:
                result.append("图片说明：精美图片素材")

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
                # 优化描述长度，确保在合适范围内
                optimized_description = optimize_description_length(description)
                result.append(f"Image Description: {optimized_description}")
            else:
                result.append("Image Description: Beautiful image")

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