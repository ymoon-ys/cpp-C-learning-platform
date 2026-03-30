from typing import Optional
from datetime import datetime
from flask import current_app
from app.models import User
from app.exceptions import AuthenticationError, ValidationError
from app.services.user_service import UserService


class AuthService:
    """认证服务类"""

    @staticmethod
    def authenticate(username: str, password: str) -> Optional[User]:
        """
        验证用户凭据
        返回用户对象或抛出 AuthenticationError
        """
        if not username or not password:
            raise ValidationError("用户名和密码不能为空")

        user = UserService.get_user_by_username(username)
        
        if not user:
            raise AuthenticationError("用户名或密码错误")
        
        if not user.check_password(password):
            raise AuthenticationError("用户名或密码错误")
        
        AuthService.update_last_login(user.id)
        return user

    @staticmethod
    def update_last_login(user_id: int) -> None:
        """更新用户最后登录时间"""
        db = current_app.db
        update_data = {
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            user_id_int = user_id
        db.update('users', user_id_int, update_data)

    @staticmethod
    def register(
        username: str,
        email: str,
        password: str,
        confirm_password: str,
        role: str = "student",
        avatar: Optional[str] = None
    ) -> User:
        """
        用户注册
        验证输入并创建新用户
        """
        if not username or not email or not password:
            raise ValidationError("用户名、邮箱和密码不能为空")

        if password != confirm_password:
            raise ValidationError("两次输入的密码不一致")

        if len(password) < 6:
            raise ValidationError("密码长度至少为6位")

        return UserService.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            avatar=avatar
        )

    @staticmethod
    def get_login_redirect_url(user: User) -> str:
        """根据用户角色获取登录后跳转的URL"""
        from flask import url_for
        
        if user.role == 'admin':
            return url_for('admin.dashboard')
        elif user.role == 'teacher':
            return url_for('teacher.dashboard')
        else:
            return url_for('student.dashboard')
