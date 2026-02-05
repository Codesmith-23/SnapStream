from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, email, username, avatar=None):
        self.id = id
        self.email = email
        self.username = username
        self.avatar = avatar