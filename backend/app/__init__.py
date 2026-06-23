import os
import logging
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_login import LoginManager
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.getenv('LOG_FILE', 'logs/app.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), 'frontend')

# 初始化Flask应用
app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

# 配置
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL', 'sqlite:///data/learning_manager.db')

# 启用CORS
CORS(app)

# 初始化登录管理
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# 用户加载回调
@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return User.get_by_id(int(user_id))

# 确保数据目录存在
os.makedirs('data', exist_ok=True)
os.makedirs('logs', exist_ok=True)
os.makedirs('static/images', exist_ok=True)

# 注册蓝图
from app.api import auth, plans, content, users, notifications, images, learners, exams
app.register_blueprint(auth.bp)
app.register_blueprint(plans.bp)
app.register_blueprint(content.bp)
app.register_blueprint(users.bp)
app.register_blueprint(notifications.bp)
app.register_blueprint(images.bp)
app.register_blueprint(learners.bp)
app.register_blueprint(exams.bp)

# 前端静态文件路由
@app.route('/')
def index():
    """提供前端主页"""
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:filename>')
def frontend_files(filename):
    """提供前端静态文件"""
    # 排除API路由
    if filename.startswith('api/'):
        return {'error': 'Not found'}, 404
    file_path = os.path.join(FRONTEND_DIR, filename)
    if os.path.exists(file_path):
        return send_from_directory(FRONTEND_DIR, filename)
    # 如果文件不存在，返回index.html（支持前端路由）
    return send_from_directory(FRONTEND_DIR, 'index.html')

# 注册错误处理
@app.errorhandler(404)
def not_found(error):
    return {'error': 'Not found'}, 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f'Server error: {error}')
    return {'error': 'Internal server error'}, 500

# 初始化数据库
from app.models.database import init_db
init_db()

# 启动定时任务
from app.services.scheduler import start_scheduler
start_scheduler()

logger.info('学习管家应用启动成功')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('FLASK_PORT', 5000)))
