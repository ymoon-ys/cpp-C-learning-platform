import os
import sys
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', '')

    BAIDU_OCR_API_KEY = os.environ.get('BAIDU_OCR_API_KEY', '')
    BAIDU_OCR_SECRET_KEY = os.environ.get('BAIDU_OCR_SECRET_KEY', '')
    BAIDU_OCR_TOKEN_EXPIRE_MARGIN = 86400

    OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', '')
    OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'qwen3-coder:30b')
    OLLAMA_TIMEOUT = int(os.environ.get('OLLAMA_TIMEOUT', '180'))

    QWEN_API_KEY = os.environ.get('QWEN_API_KEY', '')
    QWEN_BASE_URL = os.environ.get('QWEN_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
    QWEN_MODEL = os.environ.get('QWEN_MODEL', 'qwen-turbo')
    QWEN_TIMEOUT = int(os.environ.get('QWEN_TIMEOUT', '120'))

    MINIMAX_API_KEY = os.environ.get('MINIMAX_API_KEY', '')
    MINIMAX_BASE_URL = os.environ.get('MINIMAX_BASE_URL', 'https://api.minimaxi.chat/v1')
    MINIMAX_MODEL = os.environ.get('MINIMAX_MODEL', 'MiniMax-M2.7')
    MINIMAX_TIMEOUT = int(os.environ.get('MINIMAX_TIMEOUT', '120'))

    AI_PROVIDER = os.environ.get('AI_PROVIDER', 'minimax')
    AI_FALLBACK_ENABLED = os.environ.get('AI_FALLBACK_ENABLED', 'true').lower() == 'true'
    AI_FALLBACK_ORDER = os.environ.get('AI_FALLBACK_ORDER', 'minimax,ollama,qwen')

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
    def validate_required_env():
        required_vars = ['SECRET_KEY']
        missing = []

        for var in required_vars:
            value = os.environ.get(var, '')
            if not value:
                missing.append(var)

        if missing:
            print(f'\n❌ 缺少必需的环境变量: {", ".join(missing)}')
            print('\n请在 Koyeb 控制台或 .env 文件中设置以下环境变量：')
            for var in missing:
                print(f'  - {var}')
            print('\n📖 详细配置说明请参考: DEPLOYMENT_GUIDE.md\n')
            return False
        return True

    @staticmethod
    def init_app(app):
        if not Config.validate_required_env():
            if os.environ.get('FLASK_ENV') == 'production':
                print('⚠️  生产环境缺少必需配置，应用无法启动！')
                sys.exit(1)
            else:
                print('⚠️  开发模式：使用不安全的默认配置（仅用于开发测试）')


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'


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
