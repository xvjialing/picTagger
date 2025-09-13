import os
import json
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
from werkzeug.utils import secure_filename
from image_analyzer import ImageAnalyzer
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
        
        return jsonify({
            'success': True,
            'filename': filename,
            'analysis': formatted_result,
            'raw_data': analysis_data,
            'platform': platform,
            'language': language,
            'model': model
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
            
            return jsonify({
                'success': True,
                'filename': filename,
                'analysis': formatted_result,
                'file_index': file_index,
                'total_files': total_files,
                'platform': platform,
                'language': language,
                'model': model
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
            
            # 处理analysis可能是字符串的情况
            if isinstance(analysis, str):
                # 如果analysis是字符串，尝试解析为JSON
                try:
                    import json
                    analysis = json.loads(analysis)
                except:
                    # 如果解析失败，创建默认结构
                    analysis = {
                        'description': analysis[:100] if analysis else '精美图片',
                        'keywords': []
                    }
            
            # 从AI分析结果中提取信息
            description = analysis.get('description', '')
            keywords = analysis.get('keywords', [])
            
            # 如果keywords是字符串，转换为列表
            if isinstance(keywords, str):
                keywords = [k.strip() for k in keywords.split(',') if k.strip()]
            
            # 限制描述长度（5-50字）
            if len(description) > 50:
                description = description[:47] + '...'
            elif len(description) < 5:
                description = description + '，精美图片'
            
            # 限制关键词数量（5-30个）
            if len(keywords) > 30:
                keywords = keywords[:30]
            elif len(keywords) < 5:
                # 补充通用关键词
                default_keywords = ['摄影', '图片', '素材', '创意', '设计']
                keywords.extend(default_keywords[:5-len(keywords)])
            
            keywords_str = ','.join(keywords)
            
            # 直接使用AI识别的图片类型作为分类
            category = analysis.get('image_type', '其他')
            
            # 确保分类在图虫网允许的分类列表中
            tuchong_categories = [
                '城市风光', '自然风光', '野生动物', '静物美食', 
                '动物萌宠', '商务肖像', '生活方式', '室内空间', 
                '生物医疗', '运动健康', '节日假日', '其他'
            ]
            
            if category not in tuchong_categories:
                category = '其他'
            
            excel_row = {
                '图片文件名': filename,
                '是否独家[选项]': '否',  # 默认否
                '图片说明': description,
                '图片关键字': keywords_str,
                '图片分类': category,
                '图片用途[选项]': '商业广告类'  # 设置为商业广告类
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
            df.to_excel(writer, sheet_name='图片信息', index=False)
            
            # 获取工作表并设置列宽
            worksheet = writer.sheets['图片信息']
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