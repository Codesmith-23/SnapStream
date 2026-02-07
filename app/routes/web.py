import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

# Import services from config
from app.config_services import users_service, storage_service, db_service

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def home():
    """
    Landing Page
    """
    return render_template('index.html')

@web_bp.route('/explore')
def gallery():
    """
    The Video Feed
    """
    videos = db_service.get_all_videos()
    search_query = request.args.get('search', '').lower()
    
    if search_query:
        videos = [v for v in videos if search_query in v['title'].lower() or search_query in ' '.join(v['tags']).lower()]
    
    return render_template('gallery.html', videos=videos)

# --- FIX: THIS IS NOW ON ITS OWN LINE ---
@web_bp.route('/watch/<video_id>')
def watch(video_id):
    """
    Video Player Page
    """
    # 1. Get all videos (or optimize to get one)
    videos = db_service.get_all_videos()
    
    # 2. Find the specific video
    video = next((v for v in videos if v['video_id'] == video_id), None)
    
    # 3. Handle 'Not Found'
    if not video:
        return render_template('404.html'), 404
    
    return render_template('watch.html', video=video)

@web_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_page():
    if request.method == 'POST':
        return upload()
    return render_template('upload.html')

def upload():
    if 'video_file' not in request.files:
        flash('No video file part', 'error')
        return redirect(request.url)
        
    file = request.files['video_file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(request.url)

    if file:
        filename = secure_filename(file.filename)
        # Uses S3 on EC2, Local folder on laptop
        saved_filename = storage_service.upload_file(file, filename)
        
        # Handle Thumbnail
        thumbnail_filename = None
        if 'thumbnail' in request.files:
            thumb = request.files['thumbnail']
            if thumb.filename != '':
                t_name = secure_filename(thumb.filename)
                thumbnail_filename = storage_service.upload_file(thumb, t_name)

        # Save to DB
        db_service.put_video(
            title=request.form.get('title'),
            description=request.form.get('description'),
            tags=request.form.get('tags'),
            filename=saved_filename,
            user_id=current_user.id,
            thumbnail_filename=thumbnail_filename
        )
        
        flash('Video uploaded successfully!', 'success')
        return redirect(url_for('web.gallery'))

@web_bp.route('/admin')
@login_required
def admin():
    # 1. Get all videos from DB
    all_videos = db_service.get_all_videos()
    
    # 2. FILTER: Keep only videos where user_id matches the logged-in user
    my_videos = [v for v in all_videos if v['user_id'] == current_user.id]
    
    # 3. Render the new template
    return render_template('admin.html', videos=my_videos)

@web_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        action = request.form.get('action')
        
        # --- HANDLE PROFILE UPDATE ---
        if action == 'update_profile':
            new_username = request.form.get('username')
            avatar_file = request.files.get('avatar')
            delete_flag = request.form.get('delete_avatar') # <--- 1. CATCH THE FLAG
            
            avatar_filename = None
            
            # 2. DECIDE WHAT TO DO
            if delete_flag == '1':
                # Special Code: Tell the service to DELETE the image
                avatar_filename = "__DELETE__" 
            elif avatar_file and avatar_file.filename:
                # Normal Upload
                safe_name = secure_filename(avatar_file.filename)
                unique_name = f"avatar_{current_user.id}_{safe_name}"
                avatar_filename = storage_service.upload_file(avatar_file, unique_name)

            # 3. CALL SERVICE
            success, msg = users_service.update_profile(current_user.id, new_username, avatar_filename)
            
            if success:
                flash(msg, 'success')
            else:
                flash(msg, 'error')

        # --- HANDLE PASSWORD CHANGE ---
        elif action == 'change_password':
            current_pass = request.form.get('current_password')
            new_pass = request.form.get('new_password')
            confirm_pass = request.form.get('confirm_password')

            if new_pass != confirm_pass:
                flash("New passwords do not match.", 'error')
            else:
                success, msg = users_service.change_password(current_user.id, current_pass, new_pass)
                if success:
                    flash(msg, 'success')
                else:
                    flash(msg, 'error')

        return redirect(url_for('web.settings'))

    return render_template('settings.html', user=current_user)