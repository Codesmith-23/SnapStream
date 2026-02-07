from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, username, email, password_hash, bio="", avatar=None):
        """
        User Model
        - username: Matches 'user.username' in your templates
        - avatar: Matches 'user.avatar' in your templates (stores the filename)
        """
        self.id = id
        self.username = username  # FIXED: Was 'name'
        self.email = email
        self.password_hash = password_hash
        self.bio = bio
        self.avatar = avatar      # FIXED: Was 'avatar_url'