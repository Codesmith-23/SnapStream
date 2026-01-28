from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, name, email, password_hash, bio="", avatar_url=None):
        self.id = id
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.bio = bio
        self.avatar_url = avatar_url