# app/services/base.py
from abc import ABC, abstractmethod

class StorageService(ABC):
    @abstractmethod
    def upload_file(self, file_obj, filename):
        pass

class VideoDBService(ABC):  # <--- Renamed from DatabaseService to match your imports
    @abstractmethod
    def get_all_videos(self):
        pass
    @abstractmethod
    def put_video(self, title, description, tags, filename, user_id, thumbnail_filename=None):
        pass
    @abstractmethod
    def search(self, query):
        pass

class UserService(ABC):     # <--- Added this (was missing)
    @abstractmethod
    def authenticate(self, email, password):
        pass
    @abstractmethod
    def get_user_by_id(self, user_id):
        pass
    @abstractmethod
    def create_user(self, name, email, password):
        pass
    @abstractmethod
    def update_avatar(self, user_id, avatar_filename):
        pass

class NotifierService(ABC):
    @abstractmethod
    def send_notification(self, subject, message):
        pass

class AnalyzerService(ABC):
    @abstractmethod
    def detect_labels(self, media_url):
        pass