import boto3
import uuid
import os
from datetime import datetime
from botocore.exceptions import ClientError
from werkzeug.security import generate_password_hash, check_password_hash
from app.services.base import StorageService, VideoDBService, UsersService
from app.models import User

# --- 1. S3 STORAGE ---
class S3Storage(StorageService):
    def __init__(self):
        # Safe defaults or Environment Variables
        self.bucket = os.environ.get('AWS_BUCKET_NAME', 'my-snapstream-bucket')
        self.region = os.environ.get('AWS_REGION', 'us-east-1')
        self.s3_client = boto3.client('s3', region_name=self.region)
        print(f"[INFO] S3Storage initialized: bucket={self.bucket}")
    
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
            return None

# --- 2. DYNAMO VIDEO DB ---
class DynamoDBService(VideoDBService):
    def __init__(self):
        table_name = os.environ.get('DYNAMO_TABLE_VIDEO', 'SnapStream-Metadata')
        region = os.environ.get('AWS_REGION', 'us-east-1')
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = self.dynamodb.Table(table_name)
        print(f"[INFO] DynamoDBService initialized: table={table_name}")
    
    def put_video(self, title, description, tags, filename, user_id, thumbnail_filename=None):
        try:
            video_id = str(uuid.uuid4())
            # Handle tags
            if isinstance(tags, str):
                tag_list = [t.strip() for t in tags.split(',') if t.strip()]
            else:
                tag_list = tags if isinstance(tags, list) else []
            
            # Dynamic Date
            upload_date = datetime.now().strftime("%Y-%m-%d")

            item = {
                'video_id': video_id,
                'user_id': user_id,
                'title': title,
                'description': description or '',
                'tags': tag_list,
                'filename': filename,
                'thumbnail': thumbnail_filename,
                'upload_date': upload_date,
                'views': 0, # Safe default
                'likes': 0  # Safe default
            }
            self.table.put_item(Item=item)
            return video_id
        except ClientError as e:
            print(f"[ERROR] DynamoDB put_item failed: {e}")
            return None
    
    def get_all_videos(self):
        try:
            response = self.table.scan()
            items = response.get('Items', [])
            # Sort by upload_date (Newest first)
            items.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
            return items
        except ClientError as e:
            print(f"[ERROR] DynamoDB scan failed: {e}")
            return []

    def get_video(self, video_id):
        # Note: Changed from get_video_by_id to get_video to match base class
        try:
            response = self.table.get_item(Key={'video_id': video_id})
            return response.get('Item')
        except ClientError as e:
            return None
            
    def get_user_videos(self, user_id):
        from boto3.dynamodb.conditions import Attr
        try:
            response = self.table.scan(FilterExpression=Attr('user_id').eq(user_id))
            return response.get('Items', [])
        except ClientError as e:
            return []

# --- 3. DYNAMO USERS ---
class DynamoUsers(UsersService):
    def __init__(self):
        table_name = os.environ.get('DYNAMO_TABLE_USER', 'SnapStream-Users')
        region = os.environ.get('AWS_REGION', 'us-east-1')
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
            'avatar': None
        }

        try:
            self.table.put_item(Item=item)
            # FIXED: Order of arguments matches User class
            return User(user_id, username, email, password_hash), None
        except ClientError as e:
            print(f"[ERROR] Create user failed: {e}")
            return None, "Database error."

    def validate_login(self, email, password):
        user_data = self.get_user_by_email(email)
        if not user_data:
            return None, "Email not found."

        if check_password_hash(user_data['password_hash'], password):
            # FIXED: Order of arguments matches User class
            return User(
                user_data['user_id'], 
                user_data['username'],
                user_data['email'], 
                user_data['password_hash'],
                user_data.get('avatar')
            ), None
        
        return None, "Incorrect password."

    def get_user_by_email(self, email):
        try:
            from boto3.dynamodb.conditions import Attr
            response = self.table.scan(FilterExpression=Attr('email').eq(email))
            items = response.get('Items', [])
            return items[0] if items else None
        except ClientError:
            return None

    def get_user_by_id(self, user_id):
        try:
            response = self.table.get_item(Key={'user_id': user_id})
            data = response.get('Item')
            if data:
                return User(data['user_id'], data['username'], data['email'], data['password_hash'], data.get('avatar'))
            return None
        except ClientError:
            return None

    def update_profile(self, user_id, new_username, avatar_filename=None):
        try:
            update_expr = "SET username = :u"
            expr_values = {':u': new_username}
            
            if avatar_filename == "__DELETE__":
                update_expr += ", avatar = :null"
                expr_values[':null'] = None
            elif avatar_filename:
                update_expr += ", avatar = :a"
                expr_values[':a'] = avatar_filename

            self.table.update_item(
                Key={'user_id': user_id},
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_values
            )
            return True, "Profile updated"
        except ClientError as e:
            return False, str(e)

    def change_password(self, user_id, current_password, new_password):
        user = self.get_user_by_id(user_id)
        if not user or not check_password_hash(user.password_hash, current_password):
            return False, "Incorrect current password"
            
        new_hash = generate_password_hash(new_password)
        try:
            self.table.update_item(
                Key={'user_id': user_id},
                UpdateExpression="SET password_hash = :p",
                ExpressionAttributeValues={':p': new_hash}
            )
            return True, "Password updated"
        except ClientError as e:
            return False, str(e)