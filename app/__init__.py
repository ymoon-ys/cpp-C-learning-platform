import os
from flask import Flask, redirect, url_for
from flask_login import LoginManager
from app.config import Config
from app.mysql_database import MySQLDatabase
from app.models import User
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)

def create_app(config_class=Config):
    app = Flask(__name__, static_folder=config_class.STATIC_FOLDER, static_url_path='/static')
    app.config.from_object(config_class)
    
    # 在create_app函数中创建MySQLDatabase实例
    db = MySQLDatabase(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', '123456'),
        database=os.getenv('MYSQL_DATABASE', 'learning_platform')
    )
    app.db = db
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    
    Config.init_app(app)
    
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
    from app.routes.ai_assistant import init_caigpt_database
    init_caigpt_database(db)
    app.register_blueprint(recommendation_bp, url_prefix='/recommendation')
    app.register_blueprint(community_bp, url_prefix='/community')
    
    # 添加重定向规则，将/logout重定向到/auth/logout
    @app.route('/logout')
    def logout_redirect():
        return redirect(url_for('auth.logout'))
    
    # 提供上传文件的静态访问
    from flask import send_from_directory
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    # 初始化默认用户
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
    
    return app
