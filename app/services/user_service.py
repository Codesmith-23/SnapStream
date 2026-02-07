from app.models.user import User
class UsersService:
    def __init__(self, db_service):
        self.db = db_service

    # app/services/users_service.py

    def update_profile(self, user_id, new_username, avatar_filename=None):
        try:
            user = self.db.get_user_by_id(user_id)
            if not user:
                return False, "User not found"

            # Update Username
            if new_username and new_username != user.username:
                user.username = new_username

            # --- THE FIX IS HERE ---
            if avatar_filename == "__DELETE__":
                # 1. User clicked Remove -> Set DB field to None
                user.avatar = None 
            elif avatar_filename:
                # 2. User uploaded file -> Save new filename
                user.avatar = avatar_filename
            # 3. Else (None) -> Keep existing avatar

            self.db.update_user(user)
            return True, "Profile updated successfully"

        except Exception as e:
            print(f"Error updating profile: {e}")
            return False, "An error occurred"