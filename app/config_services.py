import os
# Import Mock Implementations
from app.services.mock_impl import (
    MockUsers, MockStorage, MockDatabase, MockNotifier, MockAnalyzer
)
# Import AWS Implementations
from app.services.aws_impl import (
    S3Storage, DynamoDBService, DynamoUsers, SNSNotifier, RekognitionAnalyzer
)

# Define Paths for Mock Data
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOCK_DIR = os.path.join(BASE_DIR, 'mock_aws')

def get_services():
    """Returns the correct service instances based on FLASK_ENV"""
    
    # --- PRODUCTION (AWS) ---
    if os.environ.get('FLASK_ENV') == 'production':
        print(" [SYSTEM] LOADING AWS SERVICES ☁️")
        
        # Get Config from Env Vars (set by deploy.sh or Elastic Beanstalk)
        s3_bucket = os.environ.get('AWS_BUCKET_NAME')
        users_table = os.environ.get('DYNAMO_TABLE_USER')
        videos_table = os.environ.get('DYNAMO_TABLE_VIDEO')
        region = os.environ.get('AWS_REGION', 'us-east-1')

        # Return tuple of 5 services
        return (
            DynamoUsers(),          # Users
            S3Storage(),            # Storage
            DynamoDBService(),      # Database
            SNSNotifier(),          # Notifier (New)
            RekognitionAnalyzer()   # Analyzer (New)
        )
    
    # --- LOCAL (MOCK) ---
    else:
        print(" [SYSTEM] LOADING MOCK SERVICES 💻")
        
        # Paths for local data
        db_path = os.path.join(MOCK_DIR, 'local_db')
        media_path = os.path.join(MOCK_DIR, 'local_s3')

        return (
            MockUsers(),            # Users
            MockStorage(media_path), # Storage
            MockDatabase(),         # Database
            MockNotifier(),         # Notifier (New)
            MockAnalyzer()          # Analyzer (New)
        )

# Initialize global instances so other files can import them
# UNPACK ALL 5 SERVICES HERE
users_service, storage_service, db_service, notifier_service, analyzer_service = get_services()