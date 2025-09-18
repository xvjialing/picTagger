"""
平台格式化基础类
定义所有平台格式化器的通用接口
"""

from abc import ABC, abstractmethod


class BasePlatformFormatter(ABC):
    """平台格式化器基础抽象类"""

    def __init__(self, template_config=None):
        self.template_config = template_config or {}

    @abstractmethod
    def format_analysis_result(self, analysis_data, language='zh'):
        """将AI分析结果格式化为平台特定的输出格式"""
        pass

    def handle_error(self, analysis_data, language='zh'):
        """处理分析失败的情况"""
        if 'error' in analysis_data:
            error_text = "分析失败：" if language == 'zh' else "Analysis failed: "
            return f"{error_text}{analysis_data.get('error', '未知错误')}"
        return None

    def extract_keywords(self, analysis_data, max_keywords=None):
        """从分析结果中提取关键词"""
        keywords = analysis_data.get('keywords', [])

        # 如果没有keywords字段，尝试其他字段
        if not keywords:
            keywords = analysis_data.get('keywords_cn', [])
        if not keywords:
            keywords = analysis_data.get('keywords_en', [])

        # 处理字符串格式的关键词
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(',') if k.strip()]

        # 限制关键词数量
        if max_keywords and len(keywords) > max_keywords:
            keywords = keywords[:max_keywords]

        return keywords

    def ensure_minimum_keywords(self, keywords, min_count=5, additional_keywords=None):
        """确保关键词数量不少于最小值"""
        if additional_keywords is None:
            additional_keywords = ['摄影', '图片', '素材', '创意', '设计']

        if len(keywords) < min_count:
            needed = min_count - len(keywords)
            keywords.extend(additional_keywords[:needed])

        return keywords