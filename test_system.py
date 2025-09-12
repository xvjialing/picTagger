#!/usr/bin/env python3
"""
PicTagger 系统测试脚本
用于验证系统各组件是否正常工作
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from PIL import Image, ImageDraw
import subprocess

def create_test_image(filename, size=(800, 600), text="Test Image"):
    """创建测试图片"""
    img = Image.new('RGB', size, color='lightblue')
    draw = ImageDraw.Draw(img)
    
    # 添加文字
    text_bbox = draw.textbbox((0, 0), text)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    x = (size[0] - text_width) // 2
    y = (size[1] - text_height) // 2
    
    draw.text((x, y), text, fill='darkblue')
    
    # 添加一些图形
    draw.rectangle([50, 50, 150, 150], fill='red', outline='darkred', width=3)
    draw.ellipse([size[0]-150, 50, size[0]-50, 150], fill='green', outline='darkgreen', width=3)
    
    img.save(filename)
    return filename

def test_ollama_connection():
    """测试Ollama连接"""
    print("🔍 测试Ollama连接...")
    try:
        import ollama
        models = ollama.list()
        print(f"✅ Ollama连接成功，找到 {len(models['models'])} 个模型")
        
        # 检查LLaVA模型
        llava_models = [m for m in models['models'] if 'llava' in m['name']]
        if llava_models:
            print(f"✅ 找到LLaVA模型: {[m['name'] for m in llava_models]}")
            return True
        else:
            print("❌ 未找到LLaVA模型")
            return False
    except Exception as e:
        print(f"❌ Ollama连接失败: {e}")
        return False

def test_image_analyzer():
    """测试图片分析器"""
    print("🔍 测试图片分析器...")
    try:
        from image_analyzer import ImageAnalyzer
        
        # 创建测试图片
        test_dir = Path("test_images")
        test_dir.mkdir(exist_ok=True)
        
        test_image = create_test_image(
            test_dir / "test_landscape.jpg", 
            size=(1024, 768), 
            text="Beautiful Landscape"
        )
        
        analyzer = ImageAnalyzer()
        
        # 测试不同平台
        platforms = ['general', 'tuchong', 'shutterstock']
        
        for platform in platforms:
            print(f"  测试平台: {platform}")
            result = analyzer.analyze_image(str(test_image), platform)
            
            if 'error' in result:
                print(f"    ❌ 分析失败: {result['error']}")
                return False
            else:
                print(f"    ✅ 分析成功")
        
        print("✅ 图片分析器测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 图片分析器测试失败: {e}")
        return False

def test_web_server():
    """测试Web服务器"""
    print("🔍 测试Web服务器...")
    
    # 启动服务器
    print("  启动服务器...")
    server_process = None
    
    try:
        server_process = subprocess.Popen([
            sys.executable, 'app_enhanced.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 等待服务器启动
        time.sleep(5)
        
        # 测试健康检查
        response = requests.get('http://localhost:5000/health', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 健康检查通过: {data}")
            
            # 测试主页
            response = requests.get('http://localhost:5000/', timeout=10)
            if response.status_code == 200:
                print("  ✅ 主页访问正常")
                return True
            else:
                print(f"  ❌ 主页访问失败: {response.status_code}")
                return False
        else:
            print(f"  ❌ 健康检查失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Web服务器测试失败: {e}")
        return False
    
    finally:
        if server_process:
            server_process.terminate()
            server_process.wait()

def test_cli():
    """测试CLI功能"""
    print("🔍 测试CLI功能...")
    
    try:
        # 创建测试图片
        test_dir = Path("test_images")
        test_dir.mkdir(exist_ok=True)
        
        test_images = []
        for i in range(3):
            img_path = create_test_image(
                test_dir / f"test_cli_{i}.jpg",
                size=(800, 600),
                text=f"CLI Test {i+1}"
            )
            test_images.append(img_path)
        
        # 测试CLI命令
        cmd = [
            sys.executable, 'cli.py',
            str(test_dir),
            '-p', 'general',
            '-f', 'json',
            '-o', 'test_results.json',
            '--verbose'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("  ✅ CLI执行成功")
            
            # 检查输出文件
            if Path('test_results.json').exists():
                with open('test_results.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"  ✅ 结果文件生成成功，处理了 {data['total_images']} 张图片")
                return True
            else:
                print("  ❌ 结果文件未生成")
                return False
        else:
            print(f"  ❌ CLI执行失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ CLI测试失败: {e}")
        return False

def test_utils():
    """测试工具函数"""
    print("🔍 测试工具函数...")
    
    try:
        from utils import ImageUtils, ResultExporter, ModelManager
        
        # 测试图片工具
        test_dir = Path("test_images")
        test_dir.mkdir(exist_ok=True)
        
        test_image = create_test_image(test_dir / "utils_test.jpg")
        
        # 测试图片信息获取
        info = ImageUtils.get_image_info(test_image)
        if 'error' not in info:
            print("  ✅ 图片信息获取成功")
        else:
            print(f"  ❌ 图片信息获取失败: {info['error']}")
            return False
        
        # 测试模型管理
        status = ModelManager.check_model_status()
        print(f"  ✅ 模型状态检查: {status['ollama_running']}")
        
        print("✅ 工具函数测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 工具函数测试失败: {e}")
        return False

def cleanup_test_files():
    """清理测试文件"""
    print("🧹 清理测试文件...")
    
    cleanup_paths = [
        "test_images",
        "test_results.json",
        "test_results.csv",
        "keywords.txt"
    ]
    
    for path in cleanup_paths:
        path_obj = Path(path)
        if path_obj.exists():
            if path_obj.is_dir():
                import shutil
                shutil.rmtree(path_obj)
            else:
                path_obj.unlink()
    
    print("✅ 清理完成")

def main():
    """主测试函数"""
    print("🚀 PicTagger 系统测试")
    print("=" * 50)
    
    tests = [
        ("Ollama连接", test_ollama_connection),
        ("工具函数", test_utils),
        ("图片分析器", test_image_analyzer),
        ("CLI功能", test_cli),
        # ("Web服务器", test_web_server),  # 可选，因为会启动服务器
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 运行测试: {test_name}")
        print("-" * 30)
        
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            results[test_name] = False
    
    # 输出测试结果
    print("\n📊 测试结果汇总")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统运行正常")
        cleanup_test_files()
        return 0
    else:
        print("⚠️  部分测试失败，请检查系统配置")
        return 1

if __name__ == '__main__':
    sys.exit(main())