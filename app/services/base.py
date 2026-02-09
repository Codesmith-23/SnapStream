from abc import ABC, abstractmethod

# --- 1. STORAGE INTERFACE ---
class StorageService(ABC):
    @abstractmethod
    def upload_file(self, file_obj, filename):
        """
        Uploads a file to the storage backend.
        Returns the filename (or path/URL) on success.
        """
        pass

# --- 2. VIDEO DATABASE INTERFACE ---
class VideoDBService(ABC):
    @abstractmethod
    def put_video(self, title, description, tags, filename, user_id, thumbnail_filename=None):
        """
        Saves video metadata.
        """
        pass

    @abstractmethod
    def get_all_videos(self):
        """
        Retrieves all videos.
        """
        pass

    @abstractmethod
    def get_video(self, video_id):
        """
        Retrieves a single video by ID.
        """
        pass

    @abstractmethod
    def get_user_videos(self, user_id):
        """
        Retrieves all videos uploaded by a specific user.
        """
        pass

# --- 3. USERS SERVICE INTERFACE (The Missing Part) ---
class UsersService(ABC):
    @abstractmethod
    def create_user(self, email, username, password):
        """
        Creates a new user. 
        Returns (UserObj, None) on success, or (None, error_message) on failure.
        """
        pass

    @abstractmethod
    def validate_login(self, email, password):
        """
        Validates credentials.
        Returns (UserObj, None) on success, or (None, error_message) on failure.
        """
        pass

    @abstractmethod
    def get_user_by_id(self, user_id):
        """
        Fetches a user object by ID.
        """
        pass
    
    @abstractmethod
    def get_user_by_email(self, email):
        """
        Fetches a user object by Email.
        """
        pass

    @abstractmethod
    def update_profile(self, user_id, new_username, avatar_filename=None):
        """
        Updates username and/or avatar.
        Returns (SuccessBool, MessageString).
        """
        pass

    @abstractmethod
    def change_password(self, user_id, current_password, new_password):
        """
        Updates password securely.
        Returns (SuccessBool, MessageString).
        """
        pass

# --- 4. Notification Service (SNS) ---

class NotificationService(ABC):
    @abstractmethod
    def send_notification(self, subject, message):
        """
        Sends a notification (Email/SMS) to the admin or user.
        """
        pass

# --- 5. Analysis (Rekognition) ---

class AnalyzerService(ABC):
    @abstractmethod
    def detect_labels(self, bucket, filename, max_labels=5):
        """
        Scans an image and returns a list of tags.
        """
        pass
