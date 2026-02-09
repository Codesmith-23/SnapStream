from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, send_from_directory, current_app
from flask_login import login_required, current_user
import os
import traceback
from werkzeug.utils import secure_filename

# Import services
from app.config_services import (
    db_service, 
    storage_service, 
    analyzer_service, 
    notifier_service
)

stream_bp = Blueprint('stream', __name__)

@stream_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        print("\n" + "="*40)
        print("[DEBUG] --- STARTING UPLOAD ---")
        
        # --- FIX: SMART FILE DETECTION ---
        # We look for 'video' OR 'video_file' to match whatever your HTML sends
        video_file = request.files.get('video') or request.files.get('video_file')
        thumb_file = request.files.get('thumbnail') or request.files.get('thumbnail_file')

        # 1. Check if files were found
        if not video_file:
            print("[ERROR] Video file missing! Checked 'video' and 'video_file'")
            flash('No video file found.')
            return redirect(request.url)
            
        if not thumb_file:
            print("[ERROR] Thumbnail file missing! Checked 'thumbnail' and 'thumbnail_file'")
            flash('No thumbnail file found.')
            return redirect(request.url)
        
        print(f"[DEBUG] Video Filename: '{video_file.filename}'")
        print(f"[DEBUG] Thumb Filename: '{thumb_file.filename}'")

        if video_file.filename == '' or thumb_file.filename == '':
            print("[ERROR] One of the filenames is empty")
            flash('No selected file')
            return redirect(request.url)

        try:
            # 2. Clean Names
            clean_vid_name = secure_filename(video_file.filename)
            clean_thumb_name = secure_filename(thumb_file.filename)
            
            # 3. Storage Upload
            print(f"[DEBUG] Saving video to Storage...")
            video_url = storage_service.upload_file(video_file, clean_vid_name)
            print(f"[DEBUG] Video Saved: {video_url}")
            
            print(f"[DEBUG] Saving thumbnail to Storage...")
            thumb_url = storage_service.upload_file(thumb_file, clean_thumb_name)
            print(f"[DEBUG] Thumbnail Saved: {thumb_url}")

            if not video_url or not thumb_url:
                print("[ERROR] Storage Service returned None!")
                flash('Upload failed due to storage error.')
                return redirect(request.url)

            # 4. AI Analysis
            print("[DEBUG] Running AI Analysis...")
            bucket_name = os.environ.get('AWS_BUCKET_NAME', 'mock-bucket')
            ai_tags = analyzer_service.detect_labels(bucket_name, thumb_url)
            print(f"[DEBUG] AI Tags Found: {ai_tags}")
            
            # 5. Database Save
            title = request.form.get('title')
            tags = request.form.get('tags', '')
            user_tag_list = [t.strip() for t in tags.split(',') if t.strip()]
            final_tags = list(set(user_tag_list + ai_tags))
            
            print("[DEBUG] Saving to Database...")
            db_service.put_video(
                title=title,
                description=request.form.get('description'),
                tags=final_tags,
                filename=video_url,
                thumbnail_filename=thumb_url,
                user_id=current_user.id
            )
            print("[SUCCESS] Database Entry Created!")

            # 6. Notification
            notifier_service.send_notification(
                subject=f"New Upload: {title}",
                message=f"User {current_user.username} uploaded video."
            )

            flash('Video uploaded successfully!')
            return redirect(url_for('web.gallery'))

        except Exception as e:
            print(f"[CRITICAL ERROR] Exception during upload: {e}")
            traceback.print_exc()
            flash('An internal error occurred.')
            return redirect(request.url)

    return render_template('upload.html')

@stream_bp.route('/watch/<video_id>')
def watch(video_id):
    video = db_service.get_video(video_id)
    if not video:
        abort(404)
    return render_template('watch.html', video=video)

# --- File Server Route ---
@stream_bp.route('/file/<path:filename>')
def stream_file(filename):
    """
    Serves files from Local Folder (if running locally)
    OR redirects to S3 URL (if running on AWS).
    """
    if os.environ.get('FLASK_ENV') == 'production':
        # AWS: Redirect to the public S3 URL
        bucket = os.environ.get('AWS_BUCKET_NAME')
        region = os.environ.get('AWS_REGION', 'us-east-1')
        s3_url = f"https://{bucket}.s3.{region}.amazonaws.com/{filename}"
        return redirect(s3_url)
    else:
        # Local: Serve from the 'mock_aws/local_s3' folder
        directory = current_app.config['MOCK_MEDIA_FOLDER']
        return send_from_directory(directory, filename)