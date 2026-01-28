import os
from flask import Blueprint, send_from_directory, current_app, abort

stream_bp = Blueprint('stream', __name__)

@stream_bp.route('/files/<path:filename>')
def stream_file(filename):
    """
    Debugs why files aren't loading.
    """
    try:
        # 1. Get the configured folder
        directory = current_app.config['MOCK_MEDIA_FOLDER']
        
        # 2. Construct the full path
        full_path = os.path.join(directory, filename)
        
        # 3. DEBUG PRINT (Check your terminal when you refresh the page!)
        print(f"[STREAM] Request for: {filename}")
        print(f"[STREAM] Looking in:  {full_path}")

        # 4. Check if file exists
        if not os.path.exists(full_path):
            print(f"[STREAM ERROR] File NOT FOUND at: {full_path}")
            return abort(404)

        print(f"[STREAM SUCCESS] Serving file.")
        return send_from_directory(directory, filename)
    
    except Exception as e:
        print(f"[STREAM EXCEPTION] {e}")
        return abort(404)