from functools import wraps
from flask import current_app
from flask_caching import Cache

cache = None


def init_cache(app):
    """初始化缓存实例"""
    global cache
    cache = Cache(app)
    return cache


def get_cache():
    """获取缓存实例"""
    global cache
    if cache is None:
        from flask import current_app
        cache = current_app.extensions.get('cache')
    return cache


def cached(timeout=300, key_prefix='view/%s'):
    """
    缓存装饰器
    :param timeout: 缓存超时时间（秒）
    :param key_prefix: 缓存键前缀
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_instance = get_cache()
            if cache_instance is None:
                return f(*args, **kwargs)
            
            cache_key = key_prefix % f.__name__
            rv = cache_instance.get(cache_key)
            if rv is None:
                rv = f(*args, **kwargs)
                cache_instance.set(cache_key, rv, timeout=timeout)
            return rv
        return decorated_function
    return decorator


def clear_cache(key_prefix=None):
    """清除缓存"""
    cache_instance = get_cache()
    if cache_instance is None:
        return
    
    if key_prefix:
        cache_instance.delete(key_prefix)
    else:
        cache_instance.clear()


# 常用缓存键
class CacheKeys:
    USER = 'user:%s'
    USER_LIST = 'user_list'
    COURSE = 'course:%s'
    COURSE_LIST = 'course_list'
    PROBLEM = 'problem:%s'
    PROBLEM_LIST = 'problem_list'
    CATEGORIES = 'categories'
