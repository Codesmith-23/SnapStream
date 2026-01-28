import os
import logging
from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
from config import Config

# Import Services
from app.services.mock_impl import MockStorage, MockDatabase, MockUsers, MockNotifier, MockAnalyzer

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Logging Setup
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # CORS
    CORS(app)

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    app.login_manager = login_manager

    # ============================================
    # SERVICE LAYER INITIALIZATION (FIXED)
    # ============================================
    logger.info('[INFO] Initializing services with clean storage paths...')
    
    # Grab paths from Config (USING THE NEW NAMES)
    db_folder = app.config['MOCK_DB_FOLDER']
    media_folder = app.config['MOCK_MEDIA_FOLDER']
    
    # Initialize services
    app.services = {
        'storage': MockStorage(base_path=media_folder),
        'db': MockDatabase(db_path=db_folder),
        'database': MockDatabase(db_path=db_folder), # Alias for safety
        'notifier': MockNotifier(),
        'analyzer': MockAnalyzer(),
        'users': MockUsers(db_path=db_folder)
    }
    
    logger.info(f'[INFO] Media Root: {media_folder}')
    logger.info(f'[INFO] Database Root: {db_folder}')

    # User Loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return app.services['users'].get_user_by_id(user_id)

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.web import web_bp
    from app.routes.stream import stream_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(web_bp)
    app.register_blueprint(stream_bp)

    return app