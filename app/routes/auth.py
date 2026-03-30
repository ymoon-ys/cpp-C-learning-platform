from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.services.auth_service import AuthService
from app.forms.forms import LoginForm, RegisterForm
from app import limiter

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("100 per minute")
def login():
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = AuthService.authenticate(form.username.data, form.password.data)
            login_user(user, remember=True)
            return redirect(AuthService.get_login_redirect_url(user))
        except Exception as e:
            flash(str(e), 'error')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{form[field].label.text}: {error}", 'error')
    
    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            default_avatar = f"https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt={form.username.data}%20avatar%20robot%20icon%20minimalist&image_size=square"
            
            AuthService.register(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data,
                confirm_password=form.confirm_password.data,
                role=form.role.data,
                avatar=default_avatar
            )
            flash('注册成功，请登录', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash(str(e), 'error')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{form[field].label.text}: {error}", 'error')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已成功退出登录', 'success')
    return redirect(url_for('auth.login'))