from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
from config import Config

# Import this to ensure services are initialized
from app import config_services 

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 1. Setup CORS
    CORS(app)

    # 2. Setup Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # 3. User Loader (Connects Flask-Login to your Database)
    # We use the global 'users_service' from config_services
    @login_manager.user_loader
    def load_user(user_id):
        return config_services.users_service.get_user_by_id(user_id)

    # 4. Register Blueprints (The Routes)
    from app.routes.auth import auth_bp
    from app.routes.web import web_bp
    from app.routes.stream import stream_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(web_bp)
    app.register_blueprint(stream_bp)

    return app