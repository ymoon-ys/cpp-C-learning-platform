import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    PROJECT_ROOT = os.path.dirname(BASE_DIR)
    
    DATABASE_DIR = os.path.join(PROJECT_ROOT, 'database')
    UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'uploads')
    STATIC_FOLDER = os.path.join(PROJECT_ROOT, 'static')
    
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov', 'doc', 'docx', 'ppt', 'pptx'}
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024
    
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    @staticmethod
    def init_app(app):
        pass