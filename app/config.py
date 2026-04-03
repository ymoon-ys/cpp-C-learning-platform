import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    BAIDU_OCR_API_KEY = os.environ.get('BAIDU_OCR_API_KEY', '')
    BAIDU_OCR_SECRET_KEY = os.environ.get('BAIDU_OCR_SECRET_KEY', '')
    BAIDU_OCR_TOKEN_EXPIRE_MARGIN = 86400

    OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'qwen3-coder:30b')
    OLLAMA_TIMEOUT = int(os.environ.get('OLLAMA_TIMEOUT', '180'))

    AI_MAX_HISTORY = int(os.environ.get('AI_MAX_HISTORY', '20'))
    AI_STREAM_ENABLED = os.environ.get('AI_STREAM_ENABLED', 'true').lower() == 'true'
    AI_RATE_LIMIT = os.environ.get('AI_RATE_LIMIT', '20 per minute')

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    PROJECT_ROOT = os.path.dirname(BASE_DIR)

    UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'uploads')
    STATIC_FOLDER = os.path.join(PROJECT_ROOT, 'static')

    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov', 'doc', 'docx', 'ppt', 'pptx'}
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024

    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = False

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}