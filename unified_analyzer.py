"""
统一图片分析器
整合不同的AI模型和平台格式化器
"""

import time
import os
from models import OllamaImageAnalyzer, MLXImageAnalyzer
from platforms import (
    GeneralFormatter, TuchongFormatter,
    AdobeStockFormatter, VCGFormatter
)
from config import PLATFORM_TEMPLATES
from image_validator import ImageValidator


class UnifiedImageAnalyzer:
    """统一图片分析器，整合模型和平台"""

    def __init__(self):
        # 初始化不同的AI模型分析器
        self.ollama_analyzer = OllamaImageAnalyzer()
        self.mlx_analyzer = MLXImageAnalyzer()

        # 初始化图片验证器
        self.image_validator = ImageValidator()

        # 初始化平台格式化器
        self.formatters = {
            'general': GeneralFormatter(PLATFORM_TEMPLATES.get('general', {})),
            'tuchong': TuchongFormatter(PLATFORM_TEMPLATES.get('tuchong', {})),
            'adobe_stock': AdobeStockFormatter(PLATFORM_TEMPLATES.get('adobe_stock', {})),
            'vcg': VCGFormatter(PLATFORM_TEMPLATES.get('vcg', {}))
        }

    def analyze_image(self, image_path, platform='general', model=None, language='zh', engine='ollama'):
        """统一的图片分析接口，包含图片验证和耗时统计"""
        start_time = time.time()
        image_name = os.path.basename(image_path) if image_path else "Unknown"

        print(f"🔍 开始分析图片: {image_name}")

        # 第一步：验证和修复图片
        try:
            validation_result, error_info = self.image_validator.validate_and_fix_image(image_path)

            if validation_result and validation_result.get('success'):
                print(f"✅ 图片验证通过，使用方法: {validation_result.get('method_used', 'unknown')}")

                # 如果图片被修复了，需要创建临时文件
                if validation_result.get('data'):
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                        tmp.write(validation_result['data'])
                        processed_image_path = tmp.name
                        print(f"📝 图片已处理并保存为临时文件")
                else:
                    processed_image_path = image_path
            else:
                # 验证失败，返回详细错误信息
                error_msg = self.image_validator.get_detailed_error_message(error_info)
                return {
                    'error': f"图片格式错误：{error_msg}",
                    'error_type': 'image_validation_failed',
                    'suggestions': [
                        "重新保存为标准JPEG格式",
                        "使用其他图片编辑软件转换格式",
                        "检查文件是否完整下载",
                        "尝试重新截图或重新获取图片"
                    ]
                }

        except Exception as e:
            return {
                'error': f"图片验证过程出错：{str(e)}",
                'error_type': 'validation_process_error',
                'suggestions': [
                    "检查图片文件权限",
                    "确保图片文件未损坏",
                    "尝试复制图片到其他位置"
                ]
            }

        # 根据引擎选择分析器
        if engine.lower() == 'mlx':
            analyzer = self.mlx_analyzer
            # 检查MLX是否可用
            availability = analyzer.check_model_availability()
            if not availability.get('available', False):
                # 如果MLX不可用，回退到Ollama
                print("MLX不可用，自动切换到Ollama")
                analyzer = self.ollama_analyzer
        else:
            analyzer = self.ollama_analyzer

        try:
            # 执行分析
            analysis_result = analyzer.analyze_image(processed_image_path, platform, model, language)

            # 如果使用了临时文件，清理它
            if 'processed_image_path' in locals() and processed_image_path != image_path:
                try:
                    os.unlink(processed_image_path)
                except:
                    pass

        except Exception as e:
            # 清理临时文件
            if 'processed_image_path' in locals() and processed_image_path != image_path:
                try:
                    os.unlink(processed_image_path)
                except:
                    pass
            raise e

        # 计算耗时
        end_time = time.time()
        processing_time = end_time - start_time

        # 添加耗时信息到结果中
        if 'image_info' not in analysis_result:
            analysis_result['image_info'] = {}

        analysis_result['image_info']['processing_time'] = processing_time
        analysis_result['image_info']['image_name'] = image_name

        # 如果图片被处理过，添加处理信息
        if validation_result and validation_result.get('success'):
            analysis_result['image_info']['image_processed'] = True
            analysis_result['image_info']['original_size'] = validation_result.get('original_size')
            analysis_result['image_info']['compressed_size'] = validation_result.get('compressed_size')
            analysis_result['image_info']['processing_method'] = validation_result.get('method_used')

        # 打印耗时信息
        print(f"✅ 图片 {image_name} 分析完成，耗时: {processing_time:.2f}秒")

        return analysis_result

    def format_for_platform(self, analysis_data, platform='general', language='zh'):
        """根据平台格式化输出"""
        formatter = self.formatters.get(platform, self.formatters['general'])
        return formatter.format_analysis_result(analysis_data, language)

    def get_available_engines(self):
        """获取可用的AI引擎"""
        engines = {}

        # 检查Ollama
        ollama_status = self.ollama_analyzer.check_model_availability()
        engines['ollama'] = ollama_status

        # 检查MLX
        mlx_status = self.mlx_analyzer.check_model_availability()
        engines['mlx'] = mlx_status

        return engines

    def get_supported_platforms(self):
        """获取支持的平台列表"""
        return list(self.formatters.keys())


# 向后兼容的别名
ImageAnalyzer = UnifiedImageAnalyzer