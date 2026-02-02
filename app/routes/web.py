import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

# Import your services
from app.services.mock_impl import MockUsers, MockStorage, MockDatabase

web_bp = Blueprint('web', __name__)

# --- INITIALIZE SERVICES ---
# We need these variables to be available to all functions below
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MOCK_DIR = os.path.join(BASE_DIR, 'mock_aws')

users_service = MockUsers(os.path.join(MOCK_DIR, 'local_db'))
storage_service = MockStorage(os.path.join(MOCK_DIR, 'local_s3'))
db_service = MockDatabase(os.path.join(MOCK_DIR, 'local_db'))

@web_bp.route('/')
def gallery():
    videos = db_service.get_all_videos()
    search_query = request.args.get('search', '').lower()
    
    if search_query:
        videos = [v for v in videos if search_query in v['title'].lower() or search_query in ' '.join(v['tags']).lower()]
    
    return render_template('gallery.html', videos=videos)

@web_bp.route('/watch/<video_id>')
def watch(video_id):
    videos = db_service.get_all_videos()
    video = next((v for v in videos if v['video_id'] == video_id), None)
    
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
        # Upload Video
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
    # Filter videos for the current logged-in user only
    all_videos = db_service.get_all_videos()
    my_videos = [v for v in all_videos if v['user_id'] == current_user.id]
    
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
            
            avatar_filename = None
            if avatar_file and avatar_file.filename:
                safe_name = secure_filename(avatar_file.filename)
                unique_name = f"avatar_{current_user.id}_{safe_name}"
                avatar_filename = storage_service.upload_file(avatar_file, unique_name)

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