from typing import Optional, List
from flask import current_app
from app.models import User
from app.exceptions import NotFoundError, ConflictError


def _get_cache():
    """获取缓存实例"""
    return current_app.extensions.get('cache')


class UserService:
    """用户服务类"""

    @staticmethod
    def get_user_by_id(user_id: int, use_cache: bool = True) -> Optional[User]:
        """根据ID获取用户"""
        cache = _get_cache()
        cache_key = f'user:{user_id}'
        
        if use_cache and cache:
            cached_user = cache.get(cache_key)
            if cached_user:
                return cached_user
        
        user = User.get_by_id(user_id)
        
        if use_cache and cache and user:
            cache.set(cache_key, user, timeout=300)
        
        if not user:
            raise NotFoundError(f"用户ID {user_id} 不存在")
        return user

    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return User.get_by_username(username)

    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return User.get_by_email(email)

    @staticmethod
    def get_all_users(use_cache: bool = True) -> List[User]:
        """获取所有用户"""
        cache = _get_cache()
        cache_key = 'user_list'
        
        if use_cache and cache:
            cached_users = cache.get(cache_key)
            if cached_users:
                return cached_users
        
        users = User.get_all()
        
        if use_cache and cache:
            cache.set(cache_key, users, timeout=600)
        
        return users

    @staticmethod
    def clear_user_cache(user_id: int = None):
        """清除用户缓存"""
        cache = _get_cache()
        if not cache:
            return
        
        if user_id:
            cache.delete(f'user:{user_id}')
        cache.delete('user_list')

    @staticmethod
    def create_user(
        username: str,
        email: str,
        password: str,
        role: str = "student",
        nickname: Optional[str] = None,
        avatar: Optional[str] = None
    ) -> User:
        """创建新用户"""
        if User.get_by_username(username):
            raise ConflictError(f"用户名 {username} 已存在")
        
        if User.get_by_email(email):
            raise ConflictError(f"邮箱 {email} 已被注册")

        user = User(
            username=username,
            email=email,
            role=role,
            nickname=nickname or username,
            avatar=avatar
        )
        user.set_password(password)
        return user.save()

    @staticmethod
    def update_user(
        user_id: int,
        username: Optional[str] = None,
        email: Optional[str] = None,
        nickname: Optional[str] = None,
        avatar: Optional[str] = None
    ) -> User:
        """更新用户信息"""
        user = UserService.get_user_by_id(user_id)
        
        if username and username != user.username:
            if User.get_by_username(username):
                raise ConflictError(f"用户名 {username} 已存在")
            user.username = username
        
        if email and email != user.email:
            if User.get_by_email(email):
                raise ConflictError(f"邮箱 {email} 已被注册")
            user.email = email
        
        if nickname is not None:
            user.nickname = nickname
        
        if avatar is not None:
            user.avatar = avatar
        
        return user.save()

    @staticmethod
    def update_user_password(user_id: int, new_password: str) -> User:
        """更新用户密码"""
        user = UserService.get_user_by_id(user_id)
        user.set_password(new_password)
        return user.save()

    @staticmethod
    def delete_user(user_id: int) -> bool:
        """删除用户"""
        from flask import current_app
        db = current_app.db
        return db.delete('users', user_id)
