import json
import os
import uuid
import re
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# 1. USER CLASS (Updated with avatar)
class User(UserMixin):
    def __init__(self, user_id, email, username="User", avatar=None):
        self.id = user_id
        self.email = email
        self.username = username
        self.avatar = avatar  # New field

# 2. MOCK USERS SERVICE
class MockUsers:
    def __init__(self, db_path):
        self.db_path = os.path.join(db_path, 'users.json')
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
                return User(u['id'], u['email'], u.get('username', 'User'), u.get('avatar'))
        return None

    def get_user_by_email(self, email):
        users = self._read_users()
        for u in users:
            if u['email'] == email:
                return User(u['id'], u['email'], u.get('username', 'User'), u.get('avatar'))
        return None

    def validate_login(self, email, password):
        users = self._read_users()
        
        # 1. Check if email exists
        user = next((u for u in users if u['email'] == email), None)
        
        if not user:
            # This handles "Pussy23" (missing @) AND valid emails that just aren't registered
            return None, "Email not found or incorrect."
            
        # 2. Check Password
        if check_password_hash(user['password_hash'], password):
            return User(user['id'], user['email'], user.get('username', 'User'), user.get('avatar')), None
        
        return None, "Incorrect password."

    def create_user(self, email, username, password):
        users = self._read_users()
        # Uniqueness Check
        if any(u['email'] == email for u in users):
            return None, "Email already registered."
        if any(u.get('username', '').lower() == username.lower() for u in users):
            return None, "Username already taken."

        # Password Strength Check
        if len(password) < 8: return None, "Password must be at least 8 characters."
        if not re.search(r"[a-z]", password): return None, "Password must contain a lowercase letter."
        if not re.search(r"[A-Z]", password): return None, "Password must contain an uppercase letter."
        if not re.search(r"[0-9]", password): return None, "Password must contain a number."
        if not re.search(r"[^A-Za-z0-9]", password): return None, "Password must contain a special symbol."

        new_user = {
            'id': str(uuid.uuid4()),
            'email': email,
            'username': username,
            'password_hash': generate_password_hash(password),
            'avatar': None
        }
        users.append(new_user)
        self._save_users(users)
        return User(new_user['id'], new_user['email'], new_user['username']), None

    # NEW: Update Profile Method
    def update_profile(self, user_id, new_username, new_avatar_filename=None):
        users = self._read_users()
        target_user = None
        for u in users:
            if u['id'] == user_id:
                target_user = u
                break
        
        if not target_user:
            return False, "User not found."

        # Uniqueness Check (Skip if username hasn't changed)
        if new_username.lower() != target_user['username'].lower():
            if any(u.get('username', '').lower() == new_username.lower() for u in users):
                return False, "Username already taken."

        # Update fields
        target_user['username'] = new_username
        if new_avatar_filename:
            target_user['avatar'] = new_avatar_filename
        
        self._save_users(users)
        return True, "Profile updated successfully."

    # NEW: Change Password Method
    def change_password(self, user_id, old_password, new_password):
        users = self._read_users()
        target_user = None
        for u in users:
            if u['id'] == user_id:
                target_user = u
                break
        
        if not target_user:
            return False, "User not found."

        # Verify Old Password
        if not check_password_hash(target_user['password_hash'], old_password):
            return False, "Incorrect current password."

        # Validate New Password Strength
        if len(new_password) < 8: return False, "Password must be at least 8 characters."
        if not re.search(r"[a-z]", new_password): return False, "New password must contain a lowercase letter."
        if not re.search(r"[A-Z]", new_password): return False, "New password must contain an uppercase letter."
        if not re.search(r"[0-9]", new_password): return False, "New password must contain a number."
        if not re.search(r"[^A-Za-z0-9]", new_password): return False, "New password must contain a special symbol."

        # Update Password
        target_user['password_hash'] = generate_password_hash(new_password)
        self._save_users(users)
        return True, "Password changed successfully."

# 3. MOCK STORAGE (Unchanged)
class MockStorage:
    def __init__(self, base_path):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    def upload_file(self, file_obj, filename):
        full_path = os.path.join(self.base_path, filename)
        file_obj.save(full_path)
        return filename

# 4. MOCK DATABASE (Unchanged)
class MockDatabase:
    def __init__(self, db_path):
        self.video_file = os.path.join(db_path, 'videos.json')
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
        tag_list = [t.strip() for t in tags.split(',')] if tags else []

        new_video = {
            'video_id': str(uuid.uuid4()),
            'user_id': user_id,
            'title': title,
            'description': description,
            'tags': tag_list,
            'filename': filename,
            'thumbnail': thumbnail_filename,
            'created_at': "2026-01-28" 
        }
        videos.insert(0, new_video)
        self._write(videos)
        return new_video
    
    def get_all_videos(self):
        return self._read()

# 5. STUBS
class MockNotifier:
    def notify(self, user_id, message): pass 

class MockAnalyzer:
    def analyze(self, video_path): return []