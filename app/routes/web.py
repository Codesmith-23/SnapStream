import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

# Import services
from app.config_services import users_service, db_service, storage_service

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def home():
    """ Landing Page """
    return render_template('index.html')

@web_bp.route('/explore')
def gallery():
    """ The Video Feed """
    videos = db_service.get_all_videos()
    search_query = request.args.get('search', '').lower()
    
    if search_query:
        videos = [
            v for v in videos 
            if search_query in v['title'].lower() or 
            search_query in ' '.join(v.get('tags', [])).lower()
        ]
    
    return render_template('gallery.html', videos=videos)

# --- NOTE: 'Watch' and 'Upload' are removed from here. ---
# --- They are now handled in 'stream.py' to keep code clean. ---

@web_bp.route('/admin')
@login_required
def admin():
    # Admin/Profile Page
    all_videos = db_service.get_all_videos()
    # Filter for logged-in user
    my_videos = [v for v in all_videos if v.get('user_id') == current_user.id]
    return render_template('admin.html', videos=my_videos)

@web_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        action = request.form.get('action')
        
        # --- UPDATE PROFILE ---
        if action == 'update_profile':
            new_username = request.form.get('username')
            avatar_file = request.files.get('avatar')
            delete_flag = request.form.get('delete_avatar')
            
            avatar_filename = None
            if delete_flag == '1':
                avatar_filename = "__DELETE__" 
            elif avatar_file and avatar_file.filename:
                safe_name = secure_filename(avatar_file.filename)
                unique_name = f"avatar_{current_user.id}_{safe_name}"
                avatar_filename = storage_service.upload_file(avatar_file, unique_name)

            success, msg = users_service.update_profile(current_user.id, new_username, avatar_filename)
            flash(msg, 'success' if success else 'error')

        # --- CHANGE PASSWORD ---
        elif action == 'change_password':
            current_pass = request.form.get('current_password')
            new_pass = request.form.get('new_password')
            confirm_pass = request.form.get('confirm_password')

            if new_pass != confirm_pass:
                flash("New passwords do not match.", 'error')
            else:
                success, msg = users_service.change_password(current_user.id, current_pass, new_pass)
                flash(msg, 'success' if success else 'error')

        return redirect(url_for('web.settings'))

    return render_template('settings.html', user=current_user)