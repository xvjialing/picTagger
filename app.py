import os
import base64
from io import BytesIO
from flask import Flask, render_template, request, jsonify, send_from_directory
from PIL import Image
import ollama
from werkzeug.utils import secure_filename
import json

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 支持的图片格式
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'tiff'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def compress_image(image_path, max_size=(1024, 1024), quality=85):
    """压缩图片以减少模型处理时间"""
    with Image.open(image_path) as img:
        # 转换为RGB（如果是RGBA或其他格式）
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 按比例缩放
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # 保存到内存
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        buffer.seek(0)
        
        return buffer.getvalue()

def analyze_image_with_llava(image_path):
    """使用LLaVA模型分析图片"""
    try:
        # 压缩图片
        compressed_image = compress_image(image_path)
        
        # 转换为base64
        image_b64 = base64.b64encode(compressed_image).decode('utf-8')
        
        # 构建提示词
        prompt = """请详细分析这张图片，并按以下格式输出：

图片类型：[风景/人物/动物/建筑/食物/产品/抽象/其他]
主要内容：[简洁描述图片的主要内容]
详细描述：[详细描述图片的构图、色彩、氛围等]
关键词：[用逗号分隔的关键词，适合图片供稿平台使用]
情感色调：[积极/中性/消极]
适用场景：[商业用途建议]

请用中文回答，关键词要包含中英文对照。"""

        # 调用Ollama API
        response = ollama.chat(
            model='llava:7b',
            messages=[{
                'role': 'user',
                'content': prompt,
                'images': [image_b64]
            }]
        )
        
        return response['message']['content']
        
    except Exception as e:
        return f"分析失败: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # 分析图片
        analysis = analyze_image_with_llava(filepath)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'analysis': analysis
        })
    
    return jsonify({'error': '不支持的文件格式'}), 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/health')
def health_check():
    """检查Ollama服务状态"""
    try:
        models = ollama.list()
        llava_available = any('llava' in model['name'] for model in models['models'])
        return jsonify({
            'ollama_running': True,
            'llava_available': llava_available,
            'models': [model['name'] for model in models['models']]
        })
    except Exception as e:
        return jsonify({
            'ollama_running': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 PicTagger 启动中...")
    print("📋 请确保已安装并启动 Ollama 服务")
    print("🤖 请确保已下载 LLaVA 模型: ollama pull llava:7b")
    print("🌐 访问: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)