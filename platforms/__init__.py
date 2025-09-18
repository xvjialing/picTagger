"""
平台模块
支持不同图片供稿平台的格式化输出
"""

from .base_formatter import BasePlatformFormatter
from .general import GeneralFormatter
from .tuchong import TuchongFormatter
from .adobe_stock import AdobeStockFormatter
from .vcg import VCGFormatter

__all__ = [
    'BasePlatformFormatter',
    'GeneralFormatter',
    'TuchongFormatter',
    'AdobeStockFormatter',
    'VCGFormatter'
]