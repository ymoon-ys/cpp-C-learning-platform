from functools import wraps
from flask import current_app


def get_cache():
    return current_app.extensions.get('cache')


def cached(timeout=300, key_prefix='view/%s'):
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
    cache_instance = get_cache()
    if cache_instance is None:
        return

    if key_prefix:
        cache_instance.delete(key_prefix)
    else:
        cache_instance.clear()


class CacheKeys:
    USER = 'user:%s'
    USER_LIST = 'user_list'
    COURSE = 'course:%s'
    COURSE_LIST = 'course_list'
    PROBLEM = 'problem:%s'
    PROBLEM_LIST = 'problem_list'
    CATEGORIES = 'categories'
