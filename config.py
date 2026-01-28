import os

class Config:
    # 1. SECURITY & SESSION
    SECRET_KEY = 'dev-key-fixed-professional'
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400 * 7  # 7 Days

    # 2. PATHS (Pointing to your EXISTING folders)
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # We map 'MOCK_MEDIA_FOLDER' to 'mock_aws/local_s3'
    # This is the key fix for thumbnails!
    MOCK_MEDIA_FOLDER = os.path.join(BASE_DIR, 'mock_aws', 'local_s3')
    MOCK_DB_FOLDER = os.path.join(BASE_DIR, 'mock_aws', 'local_db')
    
    # Max upload size (2GB)
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024 * 1024
    
    ENV = 'development'
    DEBUG = True