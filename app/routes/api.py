from flask import Blueprint, jsonify, request, current_app, url_for
from flask_login import current_user, login_required

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/search')
def search():
    query = request.args.get('q', '').strip()
    db = current_app.services['db']
    videos = db.search(query) if query else db.get_all_videos()
    
    # Enrich data for frontend
    results = []
    for v in videos:
        # Add full URLs so the frontend JavaScript can use them easily
        v['thumbnail_url'] = url_for('stream.stream_file', filename=v['thumbnail']) if v.get('thumbnail') else None
        v['video_url'] = url_for('stream.stream_file', filename=v['filename'])
        results.append(v)
        
    return jsonify({'results': results})

@api_bp.route('/videos/<video_id>')
def get_video(video_id):
    db = current_app.services['db']
    # Start by getting all videos to find the one we need
    # (In a real DB, you'd have a get_by_id method, but this works for Mock)
    videos = db.get_all_videos()
    video = next((v for v in videos if v['video_id'] == video_id), None)
    
    if not video:
        return jsonify({'error': 'Not found'}), 404
        
    return jsonify(video)

@api_bp.route('/videos/<video_id>/like', methods=['POST'])
@login_required
def like_video(video_id):
    db = current_app.services['db']
    # Toggle like (this is a simplified mock logic)
    # In a real app, you'd track *who* liked it. 
    # Here we just toggle the boolean on the video itself.
    videos = db.get_all_videos()
    video = next((v for v in videos if v['video_id'] == video_id), None)
    
    if video:
        video['liked'] = not video.get('liked', False)
        # Note: MockDB usually saves automatically on modification depending on implementation,
        # but explicitly calling put/save is safer. 
        # For this MockDB, modification in place works if using the list reference.
        # To be safe, let's assume the DB service handles persistance on next write.
        db._write(videos) # Force save
        return jsonify({'liked': video['liked']})
        
    return jsonify({'error': 'Video not found'}), 404

@api_bp.route('/videos/<video_id>/view', methods=['POST'])
def view_video(video_id):
    db = current_app.services['db']
    videos = db.get_all_videos()
    video = next((v for v in videos if v['video_id'] == video_id), None)
    
    if video:
        video['views'] = video.get('views', 0) + 1
        db._write(videos) # Force save
        return jsonify({'views': video['views']})
        
    return jsonify({'error': 'Video not found'}), 404