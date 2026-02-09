import json
import os
import uuid
import re
import random
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.services.base import StorageService, VideoDBService, UsersService, NotificationService, AnalyzerService

# --- 1. USER CLASS ---
class User(UserMixin):
    def __init__(self, user_id, email, username="User", avatar=None, password_hash=None):
        self.id = user_id
        self.email = email
        self.username = username
        self.avatar = avatar
        self.password_hash = password_hash 

# --- 2. MOCK USERS SERVICE (Keep as is) ---
class MockUsers(UsersService):
    def __init__(self, db_path=None):
        if db_path is None:
             BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
             db_path = os.path.join(BASE_DIR, 'mock_aws', 'local_db')
        self.db_path = os.path.join(db_path, 'users.json')
        os.makedirs(db_path, exist_ok=True)
        self._ensure_db()

    def _ensure_db(self):
        if not os.path.exists(self.db_path):
            with open(self.db_path, 'w') as f: json.dump([], f)
    def _read_users(self):
        try:
            with open(self.db_path, 'r') as f: return json.load(f)
        except: return []
    def _save_users(self, users):
        with open(self.db_path, 'w') as f: json.dump(users, f, indent=4)

    def get_user_by_id(self, user_id):
        users = self._read_users()
        for u in users:
            if u['id'] == user_id:
                return User(u['id'], u['email'], u.get('username', 'User'), u.get('avatar'), u.get('password_hash'))
        return None
    def get_user_by_email(self, email):
        users = self._read_users()
        for u in users:
            if u['email'] == email:
                return User(u['id'], u['email'], u.get('username', 'User'), u.get('avatar'), u.get('password_hash'))
        return None
    def validate_login(self, email, password):
        users = self._read_users()
        user = next((u for u in users if u['email'] == email), None)
        if not user: return None, "Email not found."
        if check_password_hash(user['password_hash'], password):
            return User(user['id'], user['email'], user.get('username', 'User'), user.get('avatar'), user.get('password_hash')), None
        return None, "Incorrect password."
    def create_user(self, email, username, password):
        users = self._read_users()
        if any(u['email'] == email for u in users): return None, "Email already registered."
        new_user = {'id': str(uuid.uuid4()), 'email': email, 'username': username, 'password_hash': generate_password_hash(password), 'avatar': None}
        users.append(new_user)
        self._save_users(users)
        return User(new_user['id'], new_user['email'], new_user['username'], None, new_user['password_hash']), None
    def update_profile(self, user_id, new_username, avatar_filename=None):
        users = self._read_users()
        target = next((u for u in users if u['id'] == user_id), None)
        if target:
            target['username'] = new_username
            if avatar_filename: target['avatar'] = (None if avatar_filename == "__DELETE__" else avatar_filename)
            self._save_users(users)
            return True, "Updated"
        return False, "User not found"
    def change_password(self, user_id, current, new):
        return True, "Mock Password Changed"

# --- 3. MOCK STORAGE (DEBUG VERSION) ---
class MockStorage(StorageService):
    def __init__(self, base_path):
        # FORCE ABSOLUTE PATH
        if not os.path.isabs(base_path):
            base_path = os.path.abspath(base_path)
            
        self.base_path = base_path
        
        # Force create the directory
        os.makedirs(self.base_path, exist_ok=True)
        
        print("\n" + "="*50)
        print(f" [DEBUG] MockStorage ACTIVE")
        print(f" [DEBUG] Saving files to: {self.base_path}")
        print("="*50 + "\n")

    def upload_file(self, file_obj, filename):
        try:
            full_path = os.path.join(self.base_path, filename)
            
            print(f" [DEBUG] Attempting to save: {filename}")
            print(f" [DEBUG] Full Path: {full_path}")
            
            # Reset file pointer just in case
            file_obj.seek(0)
            file_obj.save(full_path)
            
            if os.path.exists(full_path):
                print(f" [SUCCESS] File exists on disk! Size: {os.path.getsize(full_path)} bytes")
                return filename
            else:
                print(f" [ERROR] File.save() finished but file is missing!")
                return None
                
        except Exception as e:
            print(f" [CRITICAL ERROR] Storage failed: {e}")
            return None

# --- 4. MOCK DATABASE (Keep as is) ---
class MockDatabase(VideoDBService):
    def __init__(self, db_path=None):
        if db_path is None:
             BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
             db_path = os.path.join(BASE_DIR, 'mock_aws', 'local_db')
        self.video_file = os.path.join(db_path, 'videos.json')
        os.makedirs(db_path, exist_ok=True)
        if not os.path.exists(self.video_file):
            with open(self.video_file, 'w') as f: json.dump([], f)

    def _read(self):
        try:
            with open(self.video_file, 'r') as f: return json.load(f)
        except: return []

    def _write(self, data):
        with open(self.video_file, 'w') as f: json.dump(data, f, indent=4)

    def put_video(self, title, description, tags, filename, user_id, thumbnail_filename=None):
        videos = self._read()
        tag_list = tags if isinstance(tags, list) else []
        new_video = {
            'video_id': str(uuid.uuid4()),
            'user_id': user_id,
            'title': title,
            'description': description,
            'tags': tag_list,
            'filename': filename,
            'thumbnail': thumbnail_filename,
            'upload_date': "2026-02-09",
            'views': 0, 'likes': 0
        }
        videos.insert(0, new_video)
        self._write(videos)
        return new_video['video_id']
    
    def get_all_videos(self): return self._read()
    def get_video(self, video_id):
        videos = self._read()
        return next((v for v in videos if v['video_id'] == video_id), None)
    def get_user_videos(self, user_id):
        videos = self._read()
        return [v for v in videos if v['user_id'] == user_id]

# --- 5. STUBS ---
class MockNotifier(NotificationService):
    def send_notification(self, subject, message):
        print(f" [MOCK EMAIL] {subject}")

class MockAnalyzer(AnalyzerService):
    def detect_labels(self, bucket, filename, max_labels=5):
        return ['Viral', 'Test']