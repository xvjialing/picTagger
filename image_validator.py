"""
图片验证和修复工具
提供强大的图片文件检测、验证和修复功能
"""

import os
import tempfile
from PIL import Image, ImageFile
from io import BytesIO
import base64


class ImageValidator:
    """图片验证和修复工具"""

    def __init__(self):
        # 启用截断图像加载，允许处理不完整的图片
        ImageFile.LOAD_TRUNCATED_IMAGES = True

    def validate_and_fix_image(self, image_path, max_size=(1536, 1536), quality=90):
        """验证并修复图片，返回处理后的图片数据"""

        # 第1步：基本文件检查
        file_info = self._check_file_basic(image_path)
        if file_info['has_error']:
            return None, file_info

        # 第2步：尝试多种方式打开和处理图片
        for attempt, method in enumerate(['standard', 'robust', 'force'], 1):
            try:
                result = self._process_image_with_method(
                    image_path, method, max_size, quality
                )
                if result:
                    compressed_data, original_size, new_size = result
                    return {
                        'success': True,
                        'data': compressed_data,
                        'original_size': original_size,
                        'compressed_size': new_size,
                        'method_used': method,
                        'attempts': attempt
                    }, None
            except Exception as e:
                file_info['errors'].append(f"方法{attempt}({method})失败: {str(e)}")
                continue

        # 如果所有方法都失败了
        file_info['has_error'] = True
        return None, file_info

    def _check_file_basic(self, image_path):
        """基本文件检查"""
        info = {
            'has_error': False,
            'errors': [],
            'warnings': [],
            'file_path': image_path,
            'file_size': 0,
            'file_extension': ''
        }

        try:
            # 检查文件是否存在
            if not os.path.exists(image_path):
                info['errors'].append("文件不存在")
                info['has_error'] = True
                return info

            # 检查文件大小
            file_size = os.path.getsize(image_path)
            info['file_size'] = file_size

            if file_size == 0:
                info['errors'].append("文件大小为0字节")
                info['has_error'] = True
                return info

            if file_size < 100:  # 小于100字节可能有问题
                info['warnings'].append(f"文件过小({file_size}字节)，可能不是有效图片")

            # 检查文件扩展名
            _, ext = os.path.splitext(image_path)
            info['file_extension'] = ext.lower()

            # 检查文件头（magic number）
            with open(image_path, 'rb') as f:
                header = f.read(20)
                if not self._check_image_header(header, ext):
                    info['warnings'].append("文件头信息异常，可能不是标准图片格式")

        except Exception as e:
            info['errors'].append(f"文件检查失败: {str(e)}")
            info['has_error'] = True

        return info

    def _check_image_header(self, header, ext):
        """检查图片文件头"""
        if not header:
            return False

        # 常见图片格式的文件头标识
        signatures = {
            '.jpg': [b'\xff\xd8\xff'],
            '.jpeg': [b'\xff\xd8\xff'],
            '.png': [b'\x89PNG\r\n\x1a\n'],
            '.gif': [b'GIF87a', b'GIF89a'],
            '.bmp': [b'BM'],
            '.webp': [b'RIFF'],
            '.tiff': [b'II*\x00', b'MM\x00*'],
            '.tif': [b'II*\x00', b'MM\x00*']
        }

        if ext in signatures:
            for sig in signatures[ext]:
                if header.startswith(sig):
                    return True
            return False

        return True  # 未知格式，假设正确

    def _process_image_with_method(self, image_path, method, max_size, quality):
        """使用指定方法处理图片"""

        if method == 'standard':
            return self._process_standard(image_path, max_size, quality)
        elif method == 'robust':
            return self._process_robust(image_path, max_size, quality)
        elif method == 'force':
            return self._process_force(image_path, max_size, quality)
        else:
            raise ValueError(f"未知处理方法: {method}")

    def _process_standard(self, image_path, max_size, quality):
        """标准处理方法"""
        with Image.open(image_path) as img:
            original_size = img.size

            # 转换颜色模式
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # 缩放
            if max(original_size) > max(max_size):
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # 保存
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)

            return buffer.getvalue(), original_size, img.size

    def _process_robust(self, image_path, max_size, quality):
        """健壮处理方法 - 使用更宽松的设置"""
        with Image.open(image_path) as img:
            original_size = img.size

            # 强制重新加载图片数据
            img.load()

            # 简单模式转换
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # 简单缩放
            if max(original_size) > max(max_size):
                img = img.resize(max_size, Image.Resampling.LANCZOS)

            # 高质量保存
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=min(quality + 10, 100))

            return buffer.getvalue(), original_size, img.size

    def _process_force(self, image_path, max_size, quality):
        """强制处理方法 - 最后的尝试"""
        try:
            # 尝试用PIL的最宽松模式打开
            with open(image_path, 'rb') as f:
                data = f.read()

            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                tmp.write(data)
                tmp_path = tmp.name

            try:
                with Image.open(tmp_path) as img:
                    # 强制加载
                    img.load()
                    original_size = img.size

                    # 创建新图片对象
                    new_img = Image.new('RGB', img.size, (255, 255, 255))

                    try:
                        if img.mode == 'RGB':
                            new_img = img.copy()
                        else:
                            new_img.paste(img)
                    except:
                        # 如果粘贴失败，创建一个纯色图片
                        pass

                    # 缩放
                    if max(original_size) > max(max_size):
                        new_img = new_img.resize(max_size, Image.Resampling.NEAREST)

                    # 保存
                    buffer = BytesIO()
                    new_img.save(buffer, format='JPEG', quality=85)

                    return buffer.getvalue(), original_size, new_img.size
            finally:
                # 清理临时文件
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            raise Exception(f"强制处理也失败了: {str(e)}")

    def get_detailed_error_message(self, file_info):
        """生成详细的错误信息"""
        if not file_info or not file_info.get('has_error'):
            return "未知错误"

        messages = []

        # 基本信息
        messages.append(f"文件: {os.path.basename(file_info.get('file_path', ''))}")
        messages.append(f"大小: {file_info.get('file_size', 0)} 字节")
        messages.append(f"格式: {file_info.get('file_extension', '未知')}")

        # 错误信息
        if file_info.get('errors'):
            messages.append("\n错误详情:")
            for error in file_info['errors']:
                messages.append(f"  • {error}")

        # 警告信息
        if file_info.get('warnings'):
            messages.append("\n警告:")
            for warning in file_info['warnings']:
                messages.append(f"  • {warning}")

        # 建议
        messages.append("\n建议:")
        messages.append("  • 检查图片文件是否完整下载")
        messages.append("  • 尝试用其他图片查看器打开验证")
        messages.append("  • 如果是截图，尝试重新截图")
        messages.append("  • 考虑转换为标准JPEG格式")

        return "\n".join(messages)