import boto3
import uuid
import os
from datetime import datetime
from botocore.exceptions import ClientError
from werkzeug.security import generate_password_hash, check_password_hash
from app.services.base import StorageService, VideoDBService, UsersService, NotificationService, AnalyzerService
from app.models import User
from config import Config  # <--- NEW IMPORT

# --- 1. S3 STORAGE ---
class S3Storage:
    def __init__(self):
        # We save files to the 'static/uploads' folder on the server
        self.upload_folder = os.path.join(os.getcwd(), 'app', 'static', 'uploads')
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)

    def upload_file(self, file_obj, filename):
        """Saves file to local disk instead of S3"""
        filename = secure_filename(filename)
        file_path = os.path.join(self.upload_folder, filename)
        
        # Save the file
        file_obj.save(file_path)
        return filename

    def generate_presigned_url(self, object_name, expiration=3600):
        """Returns the local web path for the image"""
        # Returns: /static/uploads/filename.jpg
        return f"/static/uploads/{object_name}"
    
# --- 2. DYNAMO VIDEO DB ---
class DynamoDBService(VideoDBService):
    def __init__(self):
        table_name = os.environ.get('DYNAMO_TABLE_VIDEO')
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
                'views': 0,
                'likes': 0
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
            items.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
            return items
        except ClientError as e:
            print(f"[ERROR] DynamoDB scan failed: {e}")
            return []

    def get_video(self, video_id):
        try:
            response = self.table.get_item(Key={'video_id': video_id})
            return response.get('Item')
        except ClientError:
            return None
            
    def get_user_videos(self, user_id):
        from boto3.dynamodb.conditions import Attr
        try:
            response = self.table.scan(FilterExpression=Attr('user_id').eq(user_id))
            return response.get('Items', [])
        except ClientError:
            return []

# --- 3. DYNAMO USERS ---
class DynamoUsers(UsersService):
    def __init__(self):
        table_name = os.environ.get('DYNAMO_TABLE_USER')
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
            return User(user_id, username, email, password_hash), None
        except ClientError as e:
            print(f"[ERROR] Create user failed: {e}")
            return None, "Database error."

    def validate_login(self, email, password):
        user_data = self.get_user_by_email(email)
        if not user_data:
            return None, "Email not found."

        if check_password_hash(user_data['password_hash'], password):
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

# --- 4. SNS NOTIFIER (NEW) ---
class SNSNotifier(NotificationService):
    def __init__(self):
        self.sns = boto3.client('sns', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        # Get ARN from Config
        self.topic_arn = getattr(Config, 'SNS_TOPIC_ARN', None)
        print(f"[INFO] SNSNotifier initialized for Topic: {self.topic_arn}")

    def send_notification(self, subject, message):
        if not self.topic_arn:
            print("[WARN] No SNS_TOPIC_ARN set. Skipping notification.")
            return

        try:
            self.sns.publish(
                TopicArn=self.topic_arn,
                Subject=subject,
                Message=message
            )
            print(f"[INFO] SNS Notification sent: {subject}")
        except ClientError as e:
            print(f"[ERROR] Failed to send SNS: {e}")

# --- 5. REKOGNITION ANALYZER (NEW) ---
class RekognitionAnalyzer(AnalyzerService):
    def __init__(self):
        self.region = os.environ.get('AWS_REGION', 'us-east-1')
        self.client = boto3.client('rekognition', region_name=self.region)
        print(f"[INFO] Rekognition Connected in {self.region}")

    def detect_labels(self, bucket, filename, max_labels=5):
        try:
            # Use Config for confidence level
            min_confidence = getattr(Config, 'REKOGNITION_MIN_CONFIDENCE', 75)
            
            response = self.client.detect_labels(
                Image={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': filename
                    }
                },
                MaxLabels=max_labels,
                MinConfidence=min_confidence
            )
            
            tags = [label['Name'] for label in response['Labels']]
            return tags
            
        except ClientError as e:
            print(f"[ERROR] Rekognition Failed: {e}")
            return []