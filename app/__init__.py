import os
import sys
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

load_dotenv()

login_manager = LoginManager()

cache = Cache()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)

def validate_database_config():
    db_type = os.getenv('DB_TYPE', 'mysql').lower()
    
    if db_type == 'mysql':
        required_vars = ['MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE']
        missing = [var for var in required_vars if not os.getenv(var)]
        
        if missing:
            print(f'\n❌ MySQL 数据库配置缺少必需的环境变量: {", ".join(missing)}')
            print('\n请在 Koyeb 控制台或 .env 文件中设置：')
            for var in missing:
                print(f'  - {var}')
            print('\n示例配置:')
            print('  MYSQL_HOST=your-mysql-host.com')
            print('  MYSQL_USER=your_username')
            print('  MYSQL_PASSWORD=your_secure_password')
            print('  MYSQL_DATABASE=learning_platform\n')
            
            if os.environ.get('FLASK_ENV') == 'production':
                return False
    
    ollama_url = os.getenv('OLLAMA_BASE_URL', '')
    if not ollama_url:
        print('\n⚠️  未配置 OLLAMA_BASE_URL，AI 助手功能将不可用')
        print('   如需使用 AI 功能，请设置 OLLAMA_BASE_URL 环境变量')
        print('   示例: OLLAMA_BASE_URL=https://your-ollama-service.com\n')
    
    return True

def create_app(config_class=Config):
    app = Flask(__name__, static_folder=config_class.STATIC_FOLDER, static_url_path='/static')
    app.config.from_object(config_class)
    
    app.config['CACHE_TYPE'] = 'SimpleCache'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300
    cache.init_app(app)
    
    limiter.init_app(app)
    
    if not validate_database_config():
        if os.environ.get('FLASK_ENV') == 'production':
            print('❌ 生产环境数据库配置不完整，应用无法启动！')
            sys.exit(1)
        else:
            print('⚠️  开发模式继续运行，但数据库可能无法连接')
    
    db_type = os.getenv('DB_TYPE', 'mysql').lower()
    
    if db_type == 'mysql':
        db = MySQLDatabase(
            host=os.getenv('MYSQL_HOST'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DATABASE'),
            port=int(os.getenv('MYSQL_PORT', '3306'))
        )
        
        if db.conn:
            print(f'[✓] MySQL 数据库连接成功')
            print(f'    主机: {os.getenv("MYSQL_HOST")}:{os.getenv("MYSQL_PORT", "3306")}')
            print(f'    数据库: {os.getenv("MYSQL_DATABASE")}')
        else:
            print(f'[✗] MySQL 数据库连接失败！请检查配置')
    else:
        db_path = os.path.join(app.config.get('DATABASE_DIR', '.'), 'learning_platform.db')
        db = SQLiteDatabase(db_path)
        print(f'[✓] 使用 SQLite 数据库: {db_path}')
    
    app.db = db
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please login first'
    
    Config.init_app(app)

    upload_folder = app.config.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads'))
    app.config['UPLOAD_FOLDER'] = upload_folder
    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(os.path.join(upload_folder, 'avatars'), exist_ok=True)
    os.makedirs(os.path.join(upload_folder, 'community'), exist_ok=True)
    print(f'[✓] 上传目录已准备: {upload_folder}')

    from app.utils import ensure_url_path, from_json
    app.add_template_filter(ensure_url_path, 'ensure_url_path')
    app.add_template_filter(from_json, 'from_json')
    
    @app.errorhandler(BusinessException)
    def handle_business_exception(error):
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return {'error': error.message}, error.status_code
        flash(error.message, 'error')
        return redirect(request.referrer or url_for('auth.login'))
    
    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template('errors/500.html'), 500
    
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        is_https = request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https'
        if is_https:
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
    
    try:
        from app.routes.ai_assistant import init_caigpt_database
        init_caigpt_database(db)
    except Exception as e:
        print(f'[!] CAIgpt 数据库初始化失败: {e}')
    
    app.register_blueprint(recommendation_bp, url_prefix='/recommendation')
    app.register_blueprint(community_bp, url_prefix='/community')
    
    @app.route('/logout')
    def logout_redirect():
        return redirect(url_for('auth.logout'))
    
    from flask import send_from_directory, abort, Response
    from werkzeug.utils import secure_filename
    import base64
    import io
    
    DEFAULT_IMAGES = {
        'covers': {
            'data': b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x01\x90\x00\x00\x00\xe1\x08\x06\x00\x00\x00\x18\x19\xd6\x9e\x00\x00\x00\tsRGB\x00\xae\xce\x1c\xe9\x00\x00\x00>IDATx\x9c\xed\xc1\x01\x0d\x00\x00\x00\x82\x80\x89\xfe\xaf\xf8\xcf\xff\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x00\x01\xb7w\xfc\x0f\x00\x00\x00\x00IEND\xaeB`\x82',
            'mime': 'image/png'
        },
        'avatars': {
            'data': b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00d\x00\x00\x00d\x08\x02\x00\x00\x00\x1e\x19z\x8f\x00\x00\x00\tsRGB\x00\xae\xce\x1c\xe9\x00\x00\x00IDATx\x9c\xed\xc1\x01\x0d\x00\x00\x00\x82\x80\x89\xfe\xaf\xf8\xcf\xff\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x00\x01\xb7w\xfc\x0f\x00\x00\x00\x00IEND\xaeB`\x82',
            'mime': 'image/png'
        },
        'default': {
            'data': b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\xc8\x00\x00\x00\x96\x08\x02\x00\x00\x00\x1e\x19z\x8f\x00\x00\x00\tsRGB\x00\xae\xce\x1c\xe9\x00\x00\x00IDATx\x9c\xed\xc1\x01\x0d\x00\x00\x00\x82\x80\x89\xfe\xaf\xf8\xcf\xff\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x00\x01\xb7w\xfc\x0f\x00\x00\x00\x00IEND\xaeB`\x82',
            'mime': 'image/png'
        }
    }
    
    @app.route('/uploads/<path:filename>')
    @limiter.exempt
    def uploaded_file(filename):
        if '..' in filename or filename.startswith('/'):
            return 'Invalid filename', 400
        
        import os
        import logging
        logger = logging.getLogger(__name__)
        
        filename = filename.replace('\\', '/')
        if filename.startswith('uploads/'):
            filename = filename[8:]
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            logger.warning(f'[UPLOAD] 文件不存在: {file_path}')
            
            folder = filename.split('/')[0] if '/' in filename else ''
            
            if folder in DEFAULT_IMAGES:
                default_img = DEFAULT_IMAGES[folder]
                logger.info(f'[UPLOAD] 返回 {folder} 默认图片')
                return Response(default_img['data'], mimetype=default_img['mime'])
            else:
                default_img = DEFAULT_IMAGES['default']
                logger.info(f'[UPLOAD] 返回通用默认图片')
                return Response(default_img['data'], mimetype=default_img['mime'])
        
        try:
            return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
        except Exception as e:
            logger.error(f'[UPLOAD] 文件访问失败: {file_path}, 错误: {str(e)}')
            abort(500, description='文件访问失败')
    
    try:
        if not db.conn:
            print('[!] 数据库连接失败，跳过默认用户创建')
        else:
            user_count = db.count('users')
            print(f'当前用户数: {user_count}')
            if user_count == -1:
                print('[!] 无法统计用户数，跳过默认用户创建')
            else:
                from werkzeug.security import generate_password_hash
                default_users = [
                    {
                        'username': 'admin',
                        'email': 'admin@example.com',
                        'password': 'admin123',
                        'role': 'admin',
                        'nickname': 'Admin'
                    },
                    {
                        'username': 'teacher',
                        'email': 'teacher@example.com',
                        'password': 'teacher123',
                        'role': 'teacher',
                        'nickname': 'Teacher'
                    },
                    {
                        'username': 'student',
                        'email': 'student@example.com',
                        'password': 'student123',
                        'role': 'student',
                        'nickname': 'Student'
                    }
                ]
                
                created_count = 0
                for user_data in default_users:
                    existing_users = db.find_by_field('users', 'username', user_data['username'])
                    if not existing_users:
                        user_data_to_insert = {
                            'username': user_data['username'],
                            'email': user_data['email'],
                            'password_hash': generate_password_hash(user_data['password']),
                            'role': user_data['role'],
                            'nickname': user_data['nickname']
                        }
                        db.insert('users', user_data_to_insert)
                        created_count += 1
                        print(f'[✓] 创建默认用户: {user_data["username"]}')
                    else:
                        print(f'[i] 用户 {user_data["username"]} 已存在，跳过')
                
                if created_count > 0:
                    print(f'[✓] 成功创建 {created_count} 个默认用户')
                else:
                    print('[✓] 所有默认用户已存在')
    except Exception as e:
        print(f'[!] 默认用户初始化失败: {e}')
    
    print('\n' + '='*50)
    print('🚀 应用初始化完成!')
    print('='*50 + '\n')
    
    return app
