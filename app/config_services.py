import os
from app.services.mock_impl import MockUsers, MockStorage, MockDatabase
from app.services.aws_impl import S3Storage, DynamoDBService, DynamoUsers

# Define Paths for Mock Data
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOCK_DIR = os.path.join(BASE_DIR, 'mock_aws')

def get_services():
    """Returns the correct service instances based on FLASK_ENV"""
    
    # If we are on EC2 (Production), use Real AWS
    if os.environ.get('FLASK_ENV') == 'production':
        print(" [SYSTEM] LOADING AWS SERVICES ☁️")
        
        # Get Config from Env Vars (set by deploy.sh)
        s3_bucket = os.environ.get('S3_BUCKET_NAME')
        users_table = os.environ.get('DYNAMO_USERS_TABLE')
        videos_table = os.environ.get('DYNAMO_VIDEOS_TABLE')
        region = os.environ.get('AWS_REGION', 'us-east-1')

        return (
            DynamoUsers(users_table, region),
            S3Storage(s3_bucket, region),
            DynamoDBService(videos_table, region)
        )
    
    # Otherwise (Local), use Mock Files
    else:
        print(" [SYSTEM] LOADING MOCK SERVICES 💻")
        return (
            MockUsers(os.path.join(MOCK_DIR, 'local_db')),
            MockStorage(os.path.join(MOCK_DIR, 'local_s3')),
            MockDatabase(os.path.join(MOCK_DIR, 'local_db'))
        )

# Initialize global instances so other files can import them
users_service, storage_service, db_service = get_services()