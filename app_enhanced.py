import os
import json
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
from werkzeug.utils import secure_filename
from unified_analyzer import UnifiedImageAnalyzer as ImageAnalyzer
from config import Config, PLATFORM_TEMPLATES, SUPPORTED_MODELS
import ollama
import pandas as pd
from datetime import datetime
import tempfile
import re

app = Flask(__name__)
app.config.from_object(Config)

# 设置更大的文件上传限制
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 初始化图片分析器
analyzer = ImageAnalyzer()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def safe_filename(filename):
    """
    创建安全的文件名，保留中文字符
    """
    if not filename:
        return 'unknown'
    
    # 保留中文字符、英文字母、数字、点号、下划线、连字符
    # 移除其他可能有安全风险的字符
    safe_chars = re.sub(r'[^\w\u4e00-\u9fff\.\-]', '_', filename)
    
    # 确保文件名不以点开头
    if safe_chars.startswith('.'):
        safe_chars = 'file_' + safe_chars
    
    # 限制文件名长度
    if len(safe_chars) > 200:
        name, ext = os.path.splitext(safe_chars)
        safe_chars = name[:200-len(ext)] + ext
    
    return safe_chars

@app.route('/')
def index():
    return render_template('enhanced_index_with_abort.html', platforms=PLATFORM_TEMPLATES.keys())

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    
    file = request.files['file']
    platform = request.form.get('platform', 'general')
    language = request.form.get('language', 'zh')
    model = request.form.get('model', 'llava:7b')  # 添加模型参数
    
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file and allowed_file(file.filename):
        filename = safe_filename(file.filename or 'unknown')
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # 使用指定模型分析图片
        analysis_data = analyzer.analyze_image(filepath, platform, model, language)
        formatted_result = analyzer.format_for_platform(analysis_data, platform, language)

        # 获取处理耗时
        processing_time = analysis_data.get('image_info', {}).get('processing_time', 0)

        return jsonify({
            'success': True,
            'filename': filename,
            'analysis': formatted_result,
            'raw_data': analysis_data,
            'platform': platform,
            'language': language,
            'model': model,
            'processing_time': f"{processing_time:.2f}s"
        })
    
    return jsonify({'error': '不支持的文件格式'}), 400

@app.route('/batch_upload', methods=['POST'])
def batch_upload():
    """批量上传处理 - 单个文件处理"""
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    
    file = request.files['file']
    platform = request.form.get('platform', 'general')
    language = request.form.get('language', 'zh')
    model = request.form.get('model', 'llava:7b')  # 添加模型参数
    file_index = request.form.get('file_index', '1')
    total_files = request.form.get('total_files', '1')
    
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    try:
        if file and allowed_file(file.filename):
            filename = safe_filename(file.filename or 'unknown')
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # 使用指定模型分析图片
            analysis_data = analyzer.analyze_image(filepath, platform, model, language)
            formatted_result = analyzer.format_for_platform(analysis_data, platform, language)

            # 获取处理耗时
            processing_time = analysis_data.get('image_info', {}).get('processing_time', 0)

            return jsonify({
                'success': True,
                'filename': filename,
                'analysis': formatted_result,
                'file_index': file_index,
                'total_files': total_files,
                'platform': platform,
                'language': language,
                'model': model,
                'processing_time': f"{processing_time:.2f}s"
            })
        else:
            return jsonify({
                'success': False,
                'filename': file.filename or 'unknown',
                'error': '不支持的文件格式',
                'file_index': file_index,
                'total_files': total_files
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'filename': file.filename or 'unknown',
            'error': f'处理失败: {str(e)}',
            'file_index': file_index,
            'total_files': total_files
        })

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/health')
def health_check():
    """检查Ollama服务状态"""
    try:
        models = ollama.list()
        available_model_names = [model['name'] for model in models['models']]
        
        # 检查支持的模型是否可用
        model_status = {}
        for model_key in SUPPORTED_MODELS:
            model_status[model_key] = model_key in available_model_names
        
        llava_available = any('llava' in model for model in available_model_names)
        
        # 检查模型详细信息
        model_info = None
        if llava_available:
            for model in models['models']:
                if 'llava' in model['name']:
                    model_info = {
                        'name': model['name'],
                        'size': model.get('size', 'Unknown'),
                        'modified_at': model.get('modified_at', 'Unknown')
                    }
                    break
        
        return jsonify({
            'ollama_running': True,
            'llava_available': llava_available,
            'model_info': model_info,
            'available_models': available_model_names,
            'model_status': model_status,
            'supported_platforms': list(PLATFORM_TEMPLATES.keys())
        })
    except Exception as e:
        return jsonify({
            'ollama_running': False,
            'error': str(e)
        }), 500

@app.route('/platforms')
def get_platforms():
    """获取支持的平台信息"""
    return jsonify({
        'platforms': PLATFORM_TEMPLATES,
        'default': 'general'
    })

@app.route('/models')
def get_models():
    """获取支持的模型信息"""
    try:
        # 检查哪些模型已安装
        installed_models = ollama.list()
        available_model_names = [model['name'] for model in installed_models['models']]
        
        # 为每个支持的模型添加安装状态
        models_with_status = {}
        for model_key, model_info in SUPPORTED_MODELS.items():
            models_with_status[model_key] = {
                **model_info,
                'installed': model_key in available_model_names
            }
        
        return jsonify({
            'models': models_with_status,
            'default': 'llava:7b'
        })
    except Exception as e:
        return jsonify({
            'models': SUPPORTED_MODELS,
            'default': 'llava:7b',
            'error': str(e)
        })

@app.route('/download_model', methods=['POST'])
def download_model():
    """下载指定的模型"""
    data = request.get_json()
    model_name = data.get('model')
    
    if not model_name or model_name not in SUPPORTED_MODELS:
        return jsonify({'error': '不支持的模型'}), 400
    
    try:
        # 检查模型是否已存在
        models = ollama.list()
        available_models = [model['name'] for model in models['models']]
        
        if model_name in available_models:
            return jsonify({
                'success': True,
                'message': '模型已存在',
                'model': model_name
            })
        
        # 开始下载模型
        def download_progress():
            try:
                # 使用ollama pull下载模型
                import subprocess
                process = subprocess.Popen(
                    ['ollama', 'pull', model_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                stdout, stderr = process.communicate()
                
                if process.returncode == 0:
                    return True, "模型下载成功"
                else:
                    return False, f"下载失败: {stderr}"
                    
            except Exception as e:
                return False, f"下载过程出错: {str(e)}"
        
        success, message = download_progress()
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'model': model_name
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'下载失败: {str(e)}'
        }), 500

def clean_description(description):
    """清理描述中的冗余前缀"""
    if not description:
        return '精美图片'

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

    # 确保首字母大写（如果是中文则不变）
    if cleaned and len(cleaned) > 0:
        if cleaned[0].isalpha() and cleaned[0].islower():
            cleaned = cleaned[0].upper() + cleaned[1:]

    return cleaned if cleaned else '精美图片'

def optimize_description_length(description, min_length=5, max_length=50):
    """优化描述长度，确保在指定范围内"""
    if not description:
        return '精美图片素材'

    # 先清理冗余前缀
    cleaned = clean_description(description)

    # 计算字符长度
    length = len(cleaned)

    if length >= min_length and length <= max_length:
        # 长度合适，直接返回
        return cleaned
    elif length < min_length:
        # 太短，需要扩展
        return expand_description(cleaned, min_length)
    else:
        # 太长，需要智能缩短
        return shorten_description(cleaned, max_length)

def expand_description(description, min_length):
    """扩展过短的描述"""
    if len(description) >= min_length:
        return description

    # 添加通用的美化词汇来扩展描述
    enhancement_words = [
        '精美的', '优质的', '高清的', '专业的', '艺术的',
        '美丽的', '壮观的', '清晰的', '生动的', '细腻的'
    ]

    # 根据内容选择合适的修饰词
    if '风景' in description or '景色' in description or '山' in description or '海' in description:
        preferred_words = ['壮观的', '美丽的', '优质的']
    elif '人物' in description or '肖像' in description:
        preferred_words = ['专业的', '精美的', '高清的']
    elif '食物' in description or '美食' in description:
        preferred_words = ['诱人的', '精美的', '美味的']
    else:
        preferred_words = ['精美的', '优质的', '专业的']

    # 尝试添加修饰词
    for word in preferred_words:
        expanded = word + description
        if len(expanded) >= min_length and len(expanded) <= 50:
            return expanded

    # 如果还是太短，添加"摄影作品"后缀
    if len(description) + 4 <= 50:
        return description + '摄影作品'
    elif len(description) + 2 <= 50:
        return description + '作品'

    return description

def shorten_description(description, max_length):
    """智能缩短过长的描述"""
    if len(description) <= max_length:
        return description

    # 优先去除不必要的修饰词和连接词
    words_to_remove = [
        '非常', '十分', '特别', '极其', '相当', '比较', '较为',
        '显得', '看起来', '看上去', '仿佛', '好像', '似乎',
        '在...下', '在...中', '在...里', '的时候', '的瞬间'
    ]

    shortened = description
    for word in words_to_remove:
        shortened = shortened.replace(word, '')

    # 如果还是太长，智能截取
    if len(shortened) > max_length:
        # 尽量在标点符号处截断
        punctuation = ['，', '。', '、', '；', '：']
        for i in range(max_length - 1, max_length // 2, -1):
            if shortened[i] in punctuation:
                return shortened[:i]

        # 如果没有找到合适的标点，直接截取
        return shortened[:max_length]

    return shortened

@app.route('/export_excel', methods=['POST'])
def export_excel():
    """导出批量处理结果为图虫平台Excel格式"""
    try:
        data = request.get_json()
        results = data.get('results', [])

        if not results:
            return jsonify({'error': '没有数据可导出'}), 400

        # 图虫平台Excel格式
        excel_data = []

        for result in results:
            filename = result.get('filename', '')
            analysis = result.get('analysis', {})

            # 初始化默认值
            description = '精美图片'
            keywords_str = '摄影,图片,素材,创意,设计'
            category = '其他'

            # 处理analysis数据
            if isinstance(analysis, str):
                # 如果analysis是格式化后的字符串，需要解析
                try:
                    # 尝试从格式化字符串中提取信息
                    lines = analysis.split('\n')
                    for line in lines:
                        if '图片说明：' in line:
                            description = line.replace('图片说明：', '').strip()
                        elif '图片关键字：' in line:
                            keywords_str = line.replace('图片关键字：', '').strip()
                        elif '图片分类：' in line:
                            category = line.replace('图片分类：', '').strip()
                except Exception as e:
                    print(f"解析格式化字符串失败: {e}")
            elif isinstance(analysis, dict):
                # 如果analysis是字典，从原始数据中提取
                # 优先使用格式化后的description
                description = (
                    analysis.get('description') or
                    analysis.get('detailed_description') or
                    analysis.get('main_subject', '精美图片')
                )

                # 处理关键词
                keywords = analysis.get('keywords', [])
                if not keywords:
                    keywords = analysis.get('keywords_cn', [])
                if isinstance(keywords, str):
                    keywords = [k.strip() for k in keywords.split(',') if k.strip()]

                if keywords:
                    keywords_str = ','.join(keywords)

                # 处理图片分类
                category = analysis.get('image_type', '其他')

            # 优化描述长度，确保在5-50字符范围内
            description = optimize_description_length(description, 5, 50)

            # 验证和调整关键词
            keywords_list = [k.strip() for k in keywords_str.split(',') if k.strip()]

            # 限制关键词数量（5-30个）
            if len(keywords_list) > 30:
                keywords_list = keywords_list[:30]
            elif len(keywords_list) < 5:
                # 补充通用关键词
                default_keywords = ['摄影', '图片', '素材', '创意', '设计', '艺术', '视觉', '专业', '高质量', '商业']
                keywords_list.extend(default_keywords[:5-len(keywords_list)])

            keywords_str = ','.join(keywords_list)

            # 确保分类在图虫网允许的分类列表中
            tuchong_categories = [
                '城市风光', '自然风光', '野生动物', '静物美食',
                '动物萌宠', '商务肖像', '生活方式', '室内空间',
                '生物医疗', '运动健康', '节日假日', '其他'
            ]

            # 图片分类映射优化
            category_mapping = {
                '风景': '自然风光',
                '景观': '自然风光',
                '风光': '自然风光',
                '自然': '自然风光',
                '山水': '自然风光',
                '建筑': '城市风光',
                '城市': '城市风光',
                '街道': '城市风光',
                '人物': '商务肖像',
                '肖像': '商务肖像',
                '食物': '静物美食',
                '美食': '静物美食',
                '动物': '动物萌宠',
                '宠物': '动物萌宠',
                '生活': '生活方式',
                '室内': '室内空间',
                '医疗': '生物医疗',
                '运动': '运动健康',
                '健康': '运动健康',
                '节日': '节日假日'
            }

            # 先尝试直接匹配
            if category not in tuchong_categories:
                # 尝试映射匹配
                mapped_category = None
                for key, value in category_mapping.items():
                    if key in category:
                        mapped_category = value
                        break

                category = mapped_category if mapped_category else '其他'

            # 使用正确的列名（与模板一致）
            excel_row = {
                '图片文件名': filename,
                '是否独家(选项)': '否',  # 默认否
                '图片说明': description,
                '图片关键字': keywords_str,
                '图片分类': category,
                '图片用途(选项)': '商业广告类'  # 设置为商业广告类
            }

            excel_data.append(excel_row)

        # 创建DataFrame
        df = pd.DataFrame(excel_data)

        # 创建临时文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'图虫平台批量导入_{timestamp}.xlsx'

        # 使用临时目录
        temp_dir = tempfile.gettempdir()
        filepath = os.path.join(temp_dir, filename)

        # 保存Excel文件
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='工作表1', index=False)

            # 获取工作表并设置列宽
            worksheet = writer.sheets['工作表1']
            worksheet.column_dimensions['A'].width = 25  # 图片文件名
            worksheet.column_dimensions['B'].width = 15  # 是否独家
            worksheet.column_dimensions['C'].width = 50  # 图片说明
            worksheet.column_dimensions['D'].width = 60  # 图片关键字
            worksheet.column_dimensions['E'].width = 15  # 图片分类
            worksheet.column_dimensions['F'].width = 20  # 图片用途

        # 返回文件
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        return jsonify({'error': f'导出失败: {str(e)}'}), 500

if __name__ == '__main__':
    print("🚀 PicTagger Enhanced 启动中...")
    print("📋 请确保已安装并启动 Ollama 服务")
    print("🤖 请确保已下载 LLaVA 模型: ollama pull llava:7b")
    print("🌐 访问: http://localhost:5001")
    print("✨ 新功能: 多平台优化 + 批量处理")
    
    app.run(debug=True, host='0.0.0.0', port=5001)