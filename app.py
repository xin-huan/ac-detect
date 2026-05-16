import os
from flask import Flask, send_from_directory
from flask_cors import CORS

# 导入核心业务模块蓝图
from api.face_api import face_bp
from api.voice_api import voice_bp
from api.integrated_analysis_api import integrated_bp
from api.score_api import score_bp

app = Flask(__name__)
CORS(app)  # 开启跨域支持

# 注册API路由（全部模块共用 ac_detect 单一 Conda 环境）
app.register_blueprint(face_bp)
app.register_blueprint(voice_bp)
app.register_blueprint(integrated_bp)
app.register_blueprint(score_bp)

@app.route('/')
def serve_index():
    """加载系统主界面"""
    return send_from_directory('.', 'system.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """静态资源与前端依赖代理服务"""
    return send_from_directory('.', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)