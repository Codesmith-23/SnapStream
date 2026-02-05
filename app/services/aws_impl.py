import boto3
import uuid
import json
from datetime import datetime
from botocore.exceptions import ClientError
from werkzeug.security import generate_password_hash, check_password_hash
from app.services.base import StorageService, VideoDBService
from app.models import User

# --- 1. S3 STORAGE ---
class S3Storage(StorageService):
    def __init__(self, bucket_name, region='us-east-1'):
        self.s3_client = boto3.client('s3', region_name=region)
        self.bucket = bucket_name
        self.region = region
        print(f"[INFO] S3Storage initialized: bucket={bucket_name}")
    
    def upload_file(self, file_obj, filename):
        try:
            content_type = file_obj.content_type or 'application/octet-stream'
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket,
                filename,
                ExtraArgs={'ContentType': content_type}
            )
            return filename
        except ClientError as e:
            print(f"[ERROR] S3 upload failed: {e}")
            raise Exception(f"S3 upload failed: {str(e)}")

# --- 2. DYNAMO VIDEO DB ---
class DynamoDBService(VideoDBService):
    def __init__(self, table_name, region='us-east-1'):
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = self.dynamodb.Table(table_name)
        print(f"[INFO] DynamoDBService initialized: table={table_name}")
    
    def put_video(self, title, description, tags, filename, user_id, thumbnail_filename=None):
        try:
            video_id = str(uuid.uuid4())
            if isinstance(tags, str):
                tag_list = [t.strip() for t in tags.split(',') if t.strip()]
            else:
                tag_list = tags if isinstance(tags, list) else []
            
            item = {
                'video_id': video_id,
                'user_id': user_id,
                'title': title,
                'description': description or '',
                'tags': tag_list,
                'filename': filename,
                'thumbnail': thumbnail_filename or 'placeholder.jpg',
                'created_at': datetime.utcnow().isoformat(),
                'views': 0,
                'liked': False
            }
            self.table.put_item(Item=item)
            return item
        except ClientError as e:
            print(f"[ERROR] DynamoDB put_item failed: {e}")
            raise Exception(f"Database write failed: {str(e)}")
    
    def get_all_videos(self):
        try:
            response = self.table.scan()
            items = response.get('Items', [])
            items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            return items
        except ClientError as e:
            print(f"[ERROR] DynamoDB scan failed: {e}")
            return []

    def get_video_by_id(self, video_id):
        try:
            response = self.table.get_item(Key={'video_id': video_id})
            return response.get('Item')
        except ClientError as e:
            return None

# --- 3. DYNAMO USERS (LOGIN/SIGNUP) ---
class DynamoUsers:
    def __init__(self, table_name, region='us-east-1'):
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = self.dynamodb.Table(table_name)
        print(f"[INFO] DynamoUsers initialized: table={table_name}")

    def create_user(self, email, username, password):
        if self.get_user_by_email(email):
            return None, "Email already registered."

        user_id = str(uuid.uuid4())
        password_hash = generate_password_hash(password)
        
        item = {
            'user_id': user_id,
            'email': email,
            'username': username,
            'password_hash': password_hash,
            'created_at': datetime.utcnow().isoformat()
        }

        try:
            self.table.put_item(Item=item)
            return User(user_id, email, username), None
        except ClientError as e:
            print(f"[ERROR] Create user failed: {e}")
            return None, "Database error during signup."

    def validate_login(self, email, password):
        user_data = self.get_user_by_email(email)
        if not user_data:
            return None, "Email not found."

        if check_password_hash(user_data['password_hash'], password):
            return User(
                user_data['user_id'], 
                user_data['email'], 
                user_data.get('username', 'User')
            ), None
        
        return None, "Incorrect password."

    def get_user_by_email(self, email):
        try:
            response = self.table.get_item(Key={'email': email})
            return response.get('Item')
        except ClientError as e:
            return None