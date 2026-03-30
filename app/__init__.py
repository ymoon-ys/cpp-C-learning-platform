import os
from flask import Flask, redirect, url_for, render_template, request, flash
from flask_login import LoginManager
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.config import Config
from app.mysql_database import MySQLDatabase
from app.sqlite_database import SQLiteDatabase
from app.models import User
from dotenv import load_dotenv
from app.exceptions import BusinessException

# 加载.env文件
load_dotenv()

login_manager = LoginManager()

# 配置缓存
cache = Cache()

# 配置速率限制
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)

def create_app(config_class=Config):
    app = Flask(__name__, static_folder=config_class.STATIC_FOLDER, static_url_path='/static')
    app.config.from_object(config_class)
    
    # 配置缓存
    app.config['CACHE_TYPE'] = 'SimpleCache'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300
    cache.init_app(app)
    
    # 配置速率限制
    limiter.init_app(app)
    
    # 根据环境变量选择数据库类型
    db_type = os.getenv('DB_TYPE', 'mysql').lower()
    
    if db_type == 'mysql':
        # 使用MySQL数据库
        db = MySQLDatabase(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', '123456'),
            database=os.getenv('MYSQL_DATABASE', 'learning_platform'),
            port=int(os.getenv('MYSQL_PORT', '3306'))
        )
        print(f'✅ 使用MySQL数据库: {os.getenv("MYSQL_DATABASE", "learning_platform")}')
        print(f'连接信息: {os.getenv("MYSQL_HOST", "localhost")}:{os.getenv("MYSQL_PORT", "3306")}')
    else:
        # 使用SQLite数据库
        db_path = os.path.join(app.config['DATABASE_DIR'], 'learning_platform.db')
        db = SQLiteDatabase(db_path)
        print(f'✅ 使用SQLite数据库: {db_path}')
    
    app.db = db
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    
    Config.init_app(app)
    
    from app.utils import ensure_url_path
    app.add_template_filter(ensure_url_path, 'ensure_url_path')
    
    @app.errorhandler(BusinessException)
    def handle_business_exception(error):
        """处理业务异常"""
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return {'error': error.message}, error.status_code
        flash(error.message, 'error')
        return redirect(request.referrer or url_for('auth.login'))
    
    @app.errorhandler(404)
    def page_not_found(error):
        """处理404错误"""
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """处理500错误"""
        return render_template('errors/500.html'), 500
    
    @app.after_request
    def add_security_headers(response):
        """添加安全HTTP头"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response
    
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.teacher import teacher_bp
    from app.routes.student import student_bp
    from app.routes.course import course_bp
    from app.routes.ai_assistant import ai_bp
    from app.routes.recommendation import recommendation_bp
    from app.routes.community import community_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(teacher_bp, url_prefix='/teacher')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(course_bp, url_prefix='/course')
    app.register_blueprint(ai_bp, url_prefix='/ai')
    
    # 初始化CAIgpt数据库
    try:
        from app.routes.ai_assistant import init_caigpt_database
        init_caigpt_database(db)
    except Exception as e:
        print(f'❌ 初始化CAIgpt数据库失败: {e}')
    
    app.register_blueprint(recommendation_bp, url_prefix='/recommendation')
    app.register_blueprint(community_bp, url_prefix='/community')
    
    # 添加重定向规则，将/logout重定向到/auth/logout
    @app.route('/logout')
    def logout_redirect():
        return redirect(url_for('auth.logout'))
    
    from flask import send_from_directory
    from werkzeug.utils import secure_filename
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        if '..' in filename:
            return 'Invalid filename', 400
        import os
        
        if filename.startswith('uploads/'):
            filename = filename[8:]
        
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    # 初始化默认用户
    try:
        # 检查数据库连接是否成功
        if not db.conn:
            print('❌ 数据库连接失败，跳过默认用户创建')
        else:
            user_count = db.count('users')
            print(f'当前用户数量: {user_count}')
            if user_count == 0:
                from werkzeug.security import generate_password_hash
                default_users = [
                    {
                        'username': 'admin',
                        'email': 'admin@example.com',
                        'password_hash': generate_password_hash('admin123'),
                        'role': 'admin',
                        'nickname': '管理员'
                    },
                    {
                        'username': 'teacher',
                        'email': 'teacher@example.com',
                        'password_hash': generate_password_hash('teacher123'),
                        'role': 'teacher',
                        'nickname': '教师'
                    },
                    {
                        'username': 'student',
                        'email': 'student@example.com',
                        'password_hash': generate_password_hash('student123'),
                        'role': 'student',
                        'nickname': '学生'
                    }
                ]
                for user_data in default_users:
                    db.insert('users', user_data)
                print('✅ 成功创建默认用户')
            else:
                print('✅ 数据库中已有用户，跳过默认用户创建')
    except Exception as e:
        print(f'❌ 初始化默认用户失败: {e}')
    
    return app
