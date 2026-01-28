# app/routes/web.py
# Web Routes: Gallery, Upload, Admin, and Settings
# Integrated with Flask-Login and Mock Services

import logging
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

# Configure logging
logger = logging.getLogger(__name__)

web_bp = Blueprint('web', __name__)

# Configuration
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'webm', 'mkv'}
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB


def allowed_video_file(filename):
    """Check if video file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS


def allowed_image_file(filename):
    """Check if image file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


# ============================================
# HOME / GALLERY PAGE
# ============================================

@web_bp.route('/')
def index():
    """Render the Landing Page (index.html)"""
    return render_template('index.html')

@web_bp.route('/gallery', methods=['GET'])
def gallery():
    """
    Render gallery with all videos.
    Supports optional search query parameter.
    """
    try:
        db = current_app.services['db']  # Changed 'database' to 'db' to match your config
        
        # Get search query if present
        search_query = request.args.get('search', '').strip()
        
        if search_query:
            logger.info(f'[INFO] Gallery search: query="{search_query}"')
            videos = db.search(search_query)
        else:
            logger.info('[INFO] Gallery loaded: displaying all videos')
            videos = db.get_all_videos()
        
        # Sort by creation date (newest first)
        if videos:
            videos.sort(key=lambda v: v.get('created_at', ''), reverse=True)
        
        logger.info(f'[INFO] Gallery rendered: {len(videos)} videos')
        return render_template('gallery.html', videos=videos, search_query=search_query)
    
    except Exception as e:
        logger.error(f'[ERROR] Gallery load failed: {str(e)}')
        return render_template('gallery.html', videos=[], error='Failed to load gallery'), 500


# ============================================
# UPLOAD PAGE & HANDLER
# ============================================

@web_bp.route('/upload', methods=['GET'])
@login_required  # <--- Integrated Flask-Login
def upload_page():
    """Render upload form"""
    logger.info(f'[INFO] Upload page accessed by user {current_user.id}')
    return render_template('upload.html')


# app/routes/web.py

# ... (keep imports and top code) ...

@web_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    upload_id = str(uuid.uuid4())[:8]
    
    try:
        storage = current_app.services['storage']
        db = current_app.services['db']
        
        # 1. Validate Video
        if 'video_file' not in request.files:
            return {'error': 'No video file provided'}, 400
        
        video_file = request.files['video_file']
        if video_file.filename == '':
            return {'error': 'No file selected'}, 400
        
        # 2. Validate Metadata
        title = request.form.get('title', 'Untitled')
        description = request.form.get('description', '')
        tags = request.form.get('tags', '')
        
        # 3. Save Video
        ext = video_file.filename.split('.')[-1]
        video_filename = f"vid_{upload_id}_{int(datetime.now().timestamp())}.{ext}"
        storage.upload_file(video_file, video_filename)
        
        # 4. Handle Thumbnail (THE FIX IS HERE)
        thumbnail_filename = None
        
        # Check for BOTH possible names
        if 'thumbnail' in request.files:
            thumb_file = request.files['thumbnail']
        elif 'thumbnail_file' in request.files:
            thumb_file = request.files['thumbnail_file']
        else:
            thumb_file = None

        # Process the found file
        if thumb_file and thumb_file.filename:
            t_ext = thumb_file.filename.split('.')[-1]
            # Handle blobs that might not have extensions
            if not t_ext or len(t_ext) > 4: t_ext = 'jpg'
                
            t_name = f"thumb_{upload_id}_{int(datetime.now().timestamp())}.{t_ext}"
            thumbnail_filename = storage.upload_file(thumb_file, t_name)
            print(f"[DEBUG] Saved thumbnail as: {thumbnail_filename}")
        
        # 5. Save DB Entry
        db.put_video(
            title, 
            description, 
            tags, 
            video_filename, 
            current_user.id, 
            thumbnail_filename=thumbnail_filename
        )
        
        flash('Upload successful!', 'success')
        return redirect(url_for('web.gallery'))
    
    except Exception as e:
        logger.error(f'[ERROR] Upload failed: {str(e)}')
        return {'error': 'Upload failed'}, 500
    
# ============================================
# ADMIN DASHBOARD
# ============================================

@web_bp.route('/admin', methods=['GET'])
@login_required
def admin():
    """
    Admin dashboard for managing videos.
    """
    try:
        db = current_app.services['db']
        logger.info('[INFO] Admin dashboard accessed')
        
        # Get all videos
        videos = db.get_all_videos()
        
        # Simple Stats
        stats = {
            'total_videos': len(videos),
            'total_views': sum(v.get('views', 0) for v in videos),
            'total_likes': sum(1 for v in videos if v.get('liked', False))
        }
        
        return render_template('admin.html', videos=videos, stats=stats)
    
    except Exception as e:
        logger.error(f'[ERROR] Admin dashboard load failed: {str(e)}')
        return render_template('admin.html', videos=[], stats={}, error='Failed to load dashboard'), 500


# ============================================
# SETTINGS PAGE
# ============================================

@web_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """
    User settings page (profile, preferences).
    """
    if request.method == 'POST':
        # Handle Avatar Update
        if 'avatar' in request.files:
            avatar_file = request.files['avatar']
            if avatar_file and avatar_file.filename:
                storage = current_app.services['storage']
                users = current_app.services['users']
                
                ext = avatar_file.filename.split('.')[-1]
                fname = f"avatar_{current_user.id}_{int(datetime.now().timestamp())}.{ext}"
                
                storage.upload_file(avatar_file, fname)
                users.update_avatar(current_user.id, fname)
                flash('Profile updated!', 'success')
                
        return redirect(url_for('web.settings'))

    return render_template('settings.html', user=current_user)


@web_bp.route('/watch/<video_id>')
def watch(video_id):
    db = current_app.services['db']
    videos = db.get_all_videos()
    
    # Find the specific video
    video = next((v for v in videos if v['video_id'] == video_id), None)
    
    if not video:
        abort(404)
        
    # Get other videos for "Up Next" (excluding current one)
    recommendations = [v for v in videos if v['video_id'] != video_id]
    
    return render_template('watch.html', video=video, recommended=recommendations)


@web_bp.route('/video/<video_id>/like', methods=['POST'])
@login_required
def like(video_id):
    """
    STUB: Keeps the server happy when 'watch.html' tries to generate the Like URL.
    Does not actually save to DB yet.
    """
    return {'liked': True, 'likes': 1}



@web_bp.route('/video/<video_id>/view', methods=['POST'])
def count_view(video_id):
    """
    STUB: Placeholder for view counting.
    """
    return {'views': 1}

# ============================================
# ERROR HANDLERS
# ============================================

@web_bp.errorhandler(404)
def page_not_found(e):
    logger.warning(f'[WARN] 404 Not Found: {request.path}')
    return render_template('errors/404.html'), 404

@web_bp.route('/logout')
@login_required
def logout():
    return redirect(url_for('auth.logout'))