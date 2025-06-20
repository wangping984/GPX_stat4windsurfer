from flask import Flask, render_template, request, jsonify
import os
import numpy as np
from werkzeug.utils import secure_filename
import gpxo_enhance

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024  # 4MB max file size

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def handle_nan(obj):
    """处理字典中的NaN值，将其转换为None"""
    if isinstance(obj, dict):
        return {k: handle_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [handle_nan(item) for item in obj]
    elif isinstance(obj, float) and np.isnan(obj):
        return None
    return obj

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件被上传'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file and file.filename.endswith('.gpx'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # 分析GPX文件
            track = gpxo_enhance.track_enhance(filepath)
            results = track.results  # 假设这个方法返回分析结果的字典

            # 处理NaN值
            results = handle_nan(results)
            
            # 删除临时文件
            os.remove(filepath)
            
            return jsonify(results)
        except Exception as e:
            return jsonify({'error': f'分析文件时出错: {str(e)}'}), 500
    
    return jsonify({'error': '只支持GPX文件'}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 