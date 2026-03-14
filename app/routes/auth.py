from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from datetime import datetime
from werkzeug.security import generate_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.get_by_username(username)
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            
            # 更新最后登录时间
            from flask import current_app
            from datetime import datetime
            db = current_app.db
            update_data = {
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            # 确保 user.id 是整数类型
            user_id = user.id
            try:
                user_id = int(user_id)
            except ValueError:
                pass
            db.update('users', user_id, update_data)
            
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'teacher':
                return redirect(url_for('teacher.dashboard'))
            else:
                return redirect(url_for('student.dashboard'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role', 'student')
        
        if password != confirm_password:
            flash('两次输入的密码不一致', 'error')
            return render_template('auth/register.html')
        
        if User.get_by_username(username):
            flash('用户名已存在', 'error')
            return render_template('auth/register.html')
        
        if User.get_by_email(email):
            flash('邮箱已被注册', 'error')
            return render_template('auth/register.html')
        
        # 创建用户时设置创建时间和更新时间
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 为新用户生成默认头像（人机头像）
        default_avatar = f"https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt={username}%20avatar%20robot%20icon%20minimalist&image_size=square"
        
        from flask import current_app
        db = current_app.db
        
        user_data = {
            'username': username,
            'email': email,
            'password_hash': generate_password_hash(password),
            'role': role,
            'nickname': username,  # 默认昵称设为用户名
            'avatar': default_avatar,  # 默认头像设为人机头像
            'created_at': current_time,
            'updated_at': current_time
        }
        
        user_id = db.insert('users', user_data)
        
        if user_id:
            flash('注册成功，请登录', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('注册失败，请重试', 'error')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已成功退出登录', 'success')
    return redirect(url_for('auth.login'))