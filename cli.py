#!/usr/bin/env python3
"""
PicTagger CLI - 命令行版本
用于批量处理图片和自动化工作流
"""

import argparse
import os
import sys
import json
from pathlib import Path
from unified_analyzer import UnifiedImageAnalyzer as ImageAnalyzer
from utils import ImageUtils, ResultExporter, ModelManager, setup_logging

def main():
    parser = argparse.ArgumentParser(description='PicTagger CLI - 智能图片标签生成器')
    
    # 基本参数
    parser.add_argument('input', help='输入图片文件或目录路径')
    parser.add_argument('-p', '--platform', default='general', 
                       choices=['general', 'tuchong', 'shutterstock', 'getty', 'adobe_stock'],
                       help='目标平台 (默认: general)')
    parser.add_argument('-o', '--output', help='输出文件路径')
    parser.add_argument('-f', '--format', default='json', 
                       choices=['json', 'csv', 'txt'],
                       help='输出格式 (默认: json)')
    
    # 高级选项
    parser.add_argument('--recursive', '-r', action='store_true',
                       help='递归处理子目录')
    parser.add_argument('--keywords-only', action='store_true',
                       help='仅输出关键词')
    parser.add_argument('--check-duplicates', action='store_true',
                       help='检查重复文件')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='详细输出')
    
    # 系统管理
    parser.add_argument('--check-model', action='store_true',
                       help='检查模型状态')
    parser.add_argument('--download-model', action='store_true',
                       help='下载推荐模型')
    
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logging()
    
    if args.verbose:
        logger.setLevel('DEBUG')
    
    # 系统管理命令
    if args.check_model:
        status = ModelManager.check_model_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
        return
    
    if args.download_model:
        success = ModelManager.download_recommended_model()
        sys.exit(0 if success else 1)
    
    # 验证输入路径
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"输入路径不存在: {input_path}")
        sys.exit(1)
    
    # 收集图片文件
    image_files = collect_image_files(input_path, args.recursive)
    
    if not image_files:
        logger.error("未找到图片文件")
        sys.exit(1)
    
    logger.info(f"找到 {len(image_files)} 个图片文件")
    
    # 初始化分析器
    analyzer = ImageAnalyzer()
    results = []
    
    # 处理图片
    for i, image_file in enumerate(image_files, 1):
        logger.info(f"处理 ({i}/{len(image_files)}): {image_file.name}")
        
        try:
            # 检查重复文件
            if args.check_duplicates:
                is_dup, dup_name = ImageUtils.is_duplicate(str(image_file), str(image_file.parent))
                if is_dup:
                    logger.warning(f"发现重复文件: {image_file.name} (与 {dup_name} 相同)")
                    continue
            
            # 分析图片
            analysis_data = analyzer.analyze_image(str(image_file), args.platform)
            formatted_result = analyzer.format_for_platform(analysis_data, args.platform)

            # 获取处理耗时
            processing_time = analysis_data.get('image_info', {}).get('processing_time', 0)
            logger.info(f"完成 {image_file.name}，耗时: {processing_time:.2f}秒")

            # 获取图片信息
            image_info = ImageUtils.get_image_info(str(image_file))

            result = {
                'filename': image_file.name,
                'filepath': str(image_file),
                'image_info': image_info,
                'analysis': formatted_result,
                'processing_time': f"{processing_time:.2f}s",
                'raw_data': analysis_data,
                'platform': args.platform
            }
            
            results.append(result)
            
            if args.verbose:
                print(f"\n--- {image_file.name} ---")
                print(formatted_result)
                print("-" * 50)
        
        except Exception as e:
            logger.error(f"处理 {image_file.name} 时出错: {e}")
            results.append({
                'filename': image_file.name,
                'filepath': str(image_file),
                'error': str(e),
                'platform': args.platform
            })
    
    # 输出结果
    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(f"pictagger_results_{timestamp}.{args.format}")
    
    try:
        if args.keywords_only:
            output_file, keyword_count = ResultExporter.export_keywords_only(
                results, args.platform, str(output_path.with_suffix('.txt'))
            )
            logger.info(f"导出 {keyword_count} 个关键词到: {output_file}")
        
        elif args.format == 'json':
            output_file = ResultExporter.export_to_json(results, str(output_path))
            logger.info(f"结果已导出到: {output_file}")
        
        elif args.format == 'csv':
            output_file = ResultExporter.export_to_csv(results, str(output_path))
            logger.info(f"结果已导出到: {output_file}")
        
        else:  # txt
            with open(output_path, 'w', encoding='utf-8') as f:
                for result in results:
                    f.write(f"=== {result['filename']} ===\n")
                    f.write(result.get('analysis', result.get('error', 'No analysis')))
                    f.write("\n\n")
            logger.info(f"结果已导出到: {output_path}")
    
    except Exception as e:
        logger.error(f"导出结果时出错: {e}")
        sys.exit(1)
    
    # 统计信息
    successful = len([r for r in results if 'error' not in r])
    failed = len(results) - successful
    
    logger.info(f"处理完成: 成功 {successful}, 失败 {failed}")

def collect_image_files(path, recursive=False):
    """收集图片文件"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
    image_files = []
    
    if path.is_file():
        if path.suffix.lower() in image_extensions:
            image_files.append(path)
    elif path.is_dir():
        if recursive:
            for file_path in path.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                    image_files.append(file_path)
        else:
            for file_path in path.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                    image_files.append(file_path)
    
    return sorted(image_files)

if __name__ == '__main__':
    from datetime import datetime
    main()