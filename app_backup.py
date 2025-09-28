from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
import json
import time
import os
from datetime import datetime
import random
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO

# 导入classroom蓝图和数据库
from classroom.routes import classroom_bp
from classroom.models import db, init_db

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# 应用配置
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# 初始化数据库
init_db(app)

# 注册classroom蓝图
app.register_blueprint(classroom_bp, url_prefix="/classroom")

# 原有作业系统路由
@app.route('/')
def index():
    """作业系统主页"""
    return render_template('homework_index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """文件上传处理"""
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file:
        # 生成唯一文件名
        timestamp = str(int(time.time()))
        filename = f"presentation_{timestamp}.pptx"
        filepath = os.path.join('uploads', filename)
        
        # 确保uploads目录存在
        os.makedirs('uploads', exist_ok=True)
        
        # 保存文件
        file.save(filepath)
        
        return jsonify({
            'success': True, 
            'filename': filename,
            'message': '文件上传成功'
        })

@app.route('/process', methods=['POST'])
def process_presentation():
    """处理演示文稿"""
    data = request.get_json()
    filename = data.get('filename')
    
    if not filename:
        return jsonify({'error': '文件名不能为空'}), 400
    
    filepath = os.path.join('uploads', filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': '文件不存在'}), 404
    
    try:
        # 这里可以添加PPT处理逻辑
        # 目前只是模拟处理
        slides_data = []
        for i in range(5):  # 模拟5张幻灯片
            slides_data.append({
                'slide_number': i + 1,
                'content': f'这是第{i+1}张幻灯片的内容',
                'image_path': f'slide_{i}.png'
            })
        
        return jsonify({
            'success': True,
            'slides': slides_data,
            'message': '处理完成'
        })
    
    except Exception as e:
        return jsonify({'error': f'处理失败: {str(e)}'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """下载文件"""
    filepath = os.path.join('uploads', filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': '文件不存在'}), 404
    
    return send_file(filepath, as_attachment=True)

# 数据库连接配置（如果需要）
def get_database_url():
    """获取数据库连接URL"""
    # 从环境变量获取数据库URL
    return os.environ.get('DATABASE_URL', 'sqlite:///homework.db')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)