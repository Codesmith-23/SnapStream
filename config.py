import os
from datetime import timedelta

class Config:
    # ========================================================
    # 1. SECURITY SETTINGS
    # ========================================================
    # If there is no SECRET_KEY in the environment (Local), use 'dev-key'.
    # This prevents the "No Secret Key" error and keeps you logged in after restarts.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-for-snapstream-local-12345'

    # Session Settings
    PERMANENT_SESSION_LIFETIME = timedelta(days=7) 
    SESSION_COOKIE_SECURE = False # False for Local/HTTP
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # ========================================================
    # 2. STORAGE & DATABASE PATHS
    # ========================================================
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Mock Paths
    MOCK_MEDIA_FOLDER = os.path.join(BASE_DIR, 'mock_aws', 'local_s3')
    MOCK_DB_FOLDER = os.path.join(BASE_DIR, 'mock_aws', 'local_db')
    
    # AWS Configuration
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
    AWS_BUCKET_NAME = os.environ.get('AWS_BUCKET_NAME')
    
    # DynamoDB Tables
    DYNAMO_TABLE_VIDEO = os.environ.get('DYNAMO_TABLE_VIDEO')
    DYNAMO_TABLE_USER = os.environ.get('DYNAMO_TABLE_USER')

    # Notification Config (SNS)
    SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')

    # ========================================================
    # 3. AI CONFIGURATION
    # ========================================================
    REKOGNITION_MIN_CONFIDENCE = 75 

    # ========================================================
    # 4. UPLOAD LIMITS
    # ========================================================
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024 * 1024 # 2GB
    
    DEBUG = os.environ.get('FLASK_DEBUG', 'True') == 'True'
    ENV = 'development'