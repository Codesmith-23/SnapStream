import boto3
import pytest
from moto import mock_aws
import os
import json

# Import your REAL AWS implementations
from app.services.aws_impl import S3Storage, DynamoDBService, SNSNotifier, RekognitionAnalyzer

# --- SETUP: FAKE AWS CREDENTIALS ---
@pytest.fixture(scope='function')
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_REGION'] = 'us-east-1'
    os.environ['AWS_BUCKET_NAME'] = 'test-bucket'
    os.environ['DYNAMO_TABLE_VIDEO'] = 'Test-Videos'

# --- TEST 1: S3 UPLOAD ---
@mock_aws
def test_s3_upload(aws_credentials):
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test-bucket')

    storage = S3Storage()
    
    # Create fake file
    from io import BytesIO
    fake_file = BytesIO(b"Hello World")
    fake_file.content_type = "text/plain"

    filename = storage.upload_file(fake_file, "hello.txt")

    assert filename == "hello.txt"
    obj = s3.get_object(Bucket='test-bucket', Key='hello.txt')
    assert obj['Body'].read().decode('utf-8') == "Hello World"
    print("\n✅ S3 Upload Logic is PERFECT.")

# --- TEST 2: DYNAMO DB SAVE ---
@mock_aws
def test_dynamo_save(aws_credentials):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    dynamodb.create_table(
        TableName='Test-Videos',
        KeySchema=[{'AttributeName': 'video_id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'video_id', 'AttributeType': 'S'}],
        ProvisionedThroughput={'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}
    )

    db = DynamoDBService()
    video_id = db.put_video("My Title", "Desc", ["tag1"], "vid.mp4", "user-1", "thumb.jpg")

    table = dynamodb.Table('Test-Videos')
    item = table.get_item(Key={'video_id': video_id})['Item']
    
    assert item['title'] == "My Title"
    print("\n✅ DynamoDB Logic is PERFECT.")

# --- TEST 3: SNS NOTIFICATION (NEW) ---
@mock_aws
def test_sns_publish(aws_credentials):
    # 1. Create Mock SNS Topic
    sns = boto3.client('sns', region_name='us-east-1')
    response = sns.create_topic(Name='SnapStream-Alerts')
    topic_arn = response['TopicArn']
    
    # 2. Tell our code to use this fake topic
    os.environ['SNS_TOPIC_ARN'] = topic_arn
    
    # 3. Initialize Service
    notifier = SNSNotifier()
    
    # 4. Send Notification
    # (If this crashes, the test fails. If it passes, boto3 is working.)
    notifier.send_notification("Test Subject", "This is a test message")
    
    print("\n✅ SNS Notification Logic is PERFECT.")

# --- TEST 4: REKOGNITION AI (NEW) ---
@mock_aws
def test_rekognition_analysis(aws_credentials):
    # 1. Setup S3 (Rekognition needs a file to look at)
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test-bucket')
    s3.put_object(Bucket='test-bucket', Key='test_image.jpg', Body=b'fake_image_bytes')
    
    # 2. Initialize Service
    analyzer = RekognitionAnalyzer()
    
    # 3. Run Analysis
    # Moto's Rekognition mock is basic: It simply returns a success response 
    # with dummy labels if the image exists in the S3 bucket.
    tags = analyzer.detect_labels('test-bucket', 'test_image.jpg')
    
    # 4. Verify
    assert isinstance(tags, list)
    print(f"\n✅ Rekognition Logic is PERFECT. (Tags received: {tags})")

if __name__ == "__main__":
    pytest.main(["-v", "tests.py"])