import os
import json
from datetime import datetime
from PIL import Image
import hashlib

class ImageUtils:
    """图片处理工具类"""
    
    @staticmethod
    def get_image_info(image_path):
        """获取图片基本信息"""
        try:
            with Image.open(image_path) as img:
                return {
                    'filename': os.path.basename(image_path),
                    'size': img.size,
                    'mode': img.mode,
                    'format': img.format,
                    'file_size': os.path.getsize(image_path),
                    'created_time': datetime.fromtimestamp(os.path.getctime(image_path)).isoformat()
                }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def calculate_file_hash(file_path):
        """计算文件MD5哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    @staticmethod
    def is_duplicate(file_path, upload_dir):
        """检查是否为重复文件"""
        current_hash = ImageUtils.calculate_file_hash(file_path)
        
        for filename in os.listdir(upload_dir):
            if filename != os.path.basename(file_path):
                existing_path = os.path.join(upload_dir, filename)
                if os.path.isfile(existing_path):
                    existing_hash = ImageUtils.calculate_file_hash(existing_path)
                    if current_hash == existing_hash:
                        return True, filename
        return False, None

class ResultExporter:
    """结果导出工具类"""
    
    @staticmethod
    def export_to_json(results, filename='analysis_results.json'):
        """导出结果为JSON格式"""
        export_data = {
            'export_time': datetime.now().isoformat(),
            'total_images': len(results),
            'results': results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return filename
    
    @staticmethod
    def export_to_csv(results, filename='analysis_results.csv'):
        """导出结果为CSV格式"""
        import csv
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 写入表头
            writer.writerow([
                '文件名', '图片类型', '主要内容', '中文关键词', 
                '英文关键词', '情感色调', '商业用途'
            ])
            
            # 写入数据
            for result in results:
                if 'raw_data' in result and not result['raw_data'].get('error'):
                    data = result['raw_data']
                    writer.writerow([
                        result.get('filename', ''),
                        data.get('image_type', ''),
                        data.get('main_subject', ''),
                        ', '.join(data.get('keywords_cn', [])),
                        ', '.join(data.get('keywords_en', [])),
                        data.get('mood', ''),
                        data.get('commercial_use', '')
                    ])
        
        return filename
    
    @staticmethod
    def export_keywords_only(results, platform='general', filename='keywords.txt'):
        """仅导出关键词"""
        keywords_set = set()
        
        for result in results:
            if 'raw_data' in result and not result['raw_data'].get('error'):
                data = result['raw_data']
                
                # 根据平台选择关键词语言
                if platform in ['tuchong', 'general']:
                    keywords_set.update(data.get('keywords_cn', []))
                else:
                    keywords_set.update(data.get('keywords_en', []))
        
        with open(filename, 'w', encoding='utf-8') as f:
            for keyword in sorted(keywords_set):
                f.write(f"{keyword}\n")
        
        return filename, len(keywords_set)

class ConfigManager:
    """配置管理工具"""
    
    @staticmethod
    def load_user_config(config_file='user_config.json'):
        """加载用户配置"""
        default_config = {
            'default_platform': 'general',
            'image_quality': 85,
            'max_image_size': 1024,
            'auto_backup': True,
            'preferred_language': 'zh',
            'batch_size_limit': 20
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception:
                pass
        
        return default_config
    
    @staticmethod
    def save_user_config(config, config_file='user_config.json'):
        """保存用户配置"""
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

class ModelManager:
    """模型管理工具"""
    
    @staticmethod
    def check_model_status():
        """检查模型状态"""
        try:
            import ollama
            models = ollama.list()
            
            available_models = []
            for model in models['models']:
                if 'llava' in model['name'].lower():
                    available_models.append({
                        'name': model['name'],
                        'size': model.get('size', 0),
                        'modified_at': model.get('modified_at', ''),
                        'family': model.get('details', {}).get('family', 'unknown')
                    })
            
            return {
                'ollama_running': True,
                'available_models': available_models,
                'recommended_model': 'llava:7b'
            }
        except Exception as e:
            return {
                'ollama_running': False,
                'error': str(e),
                'available_models': [],
                'recommended_model': 'llava:7b'
            }
    
    @staticmethod
    def download_recommended_model():
        """下载推荐模型"""
        try:
            import ollama
            print("📥 开始下载 LLaVA 7B 模型...")
            ollama.pull('llava:7b')
            print("✅ 模型下载完成")
            return True
        except Exception as e:
            print(f"❌ 模型下载失败: {e}")
            return False

def setup_logging():
    """设置日志"""
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('pictagger.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger('PicTagger')