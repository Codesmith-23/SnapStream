import os
from datetime import timedelta

class Config:
    # ========================================================
    # 1. SMART SECRET KEY (Handles Both Local & AWS)
    # ========================================================
    # AWS: We will set 'SECRET_KEY' in the AWS Console settings.
    # Local: Since that variable is missing, it falls back to os.urandom(24).
    # This gives you the "restart = logout" behavior locally, but stability on AWS.
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)

    # ========================================================
    # 2. SESSION SETTINGS
    # ========================================================
    PERMANENT_SESSION_LIFETIME = timedelta(days=7) # Users stay logged in for 7 days
    SESSION_COOKIE_SECURE = False # Set to True later when you have HTTPS on AWS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # ========================================================
    # 3. STORAGE & DATABASE PATHS
    # ========================================================
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # These paths are only used if you are using the Mock/Local implementation
    MOCK_MEDIA_FOLDER = os.path.join(BASE_DIR, 'mock_aws', 'local_s3')
    MOCK_DB_FOLDER = os.path.join(BASE_DIR, 'mock_aws', 'local_db')
    
    # AWS Configuration (Will be read from Environment Variables on Server)
    AWS_BUCKET_NAME = os.environ.get('AWS_BUCKET_NAME')
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
    DYNAMO_TABLE_VIDEO = os.environ.get('DYNAMO_TABLE_VIDEO')
    DYNAMO_TABLE_USER = os.environ.get('DYNAMO_TABLE_USER')

    # Upload Limits
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024 * 1024 # 2GB Limit
    
    # Debug Mode: True locally, False on AWS (controlled by env var)
    DEBUG = os.environ.get('FLASK_DEBUG', 'True') == 'True'
    ENV = 'development'