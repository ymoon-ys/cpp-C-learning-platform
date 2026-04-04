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

def create_app(config_class=Config):
    app = Flask(__name__, static_folder=config_class.STATIC_FOLDER, static_url_path='/static')
    app.config.from_object(config_class)
    
    app.config['CACHE_TYPE'] = 'SimpleCache'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300
    cache.init_app(app)
    
    limiter.init_app(app)
    
    db_type = os.getenv('DB_TYPE', 'mysql').lower()
    
    if db_type == 'mysql':
        db = MySQLDatabase(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', '123456'),
            database=os.getenv('MYSQL_DATABASE', 'learning_platform'),
            port=int(os.getenv('MYSQL_PORT', '3306'))
        )
        print(f'[OK] Using MySQL database: {os.getenv("MYSQL_DATABASE", "learning_platform")}')
        print(f'Connection: {os.getenv("MYSQL_HOST", "localhost")}:{os.getenv("MYSQL_PORT", "3306")}')
    else:
        db_path = os.path.join(app.config['DATABASE_DIR'], 'learning_platform.db')
        db = SQLiteDatabase(db_path)
        print(f'[OK] Using SQLite database: {db_path}')
    
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
    print(f'[OK] Upload folder ready: {upload_folder}')

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
        print(f'[ERR] Failed to initialize CAIgpt database: {e}')
    
    app.register_blueprint(recommendation_bp, url_prefix='/recommendation')
    app.register_blueprint(community_bp, url_prefix='/community')
    
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
        
        filename = filename.replace('\\', '/')
        if filename.startswith('uploads/'):
            filename = filename[8:]
        
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        if not db.conn:
            print('[ERR] Database connection failed, skipping default user creation')
        else:
            user_count = db.count('users')
            print(f'Current user count: {user_count}')
            if user_count == -1:
                print('[ERR] Failed to count users, skipping default user creation')
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
                        print(f'[OK] Created default user: {user_data["username"]}')
                    else:
                        print(f'[INFO] User {user_data["username"]} already exists, skipping')
                
                if created_count > 0:
                    print(f'[OK] Created {created_count} default users successfully')
                else:
                    print('[OK] All default users already exist')
    except Exception as e:
        print(f'[ERR] Failed to initialize default users: {e}')
    
    return app
