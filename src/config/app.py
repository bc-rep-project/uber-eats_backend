from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configure app
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000))
    app.config['MONGO_URI'] = os.getenv('MONGO_URI')
    
    # Initialize extensions
    CORS(app, resources={r"/api/*": {"origins": os.getenv('CORS_ORIGINS', '*')}})
    jwt = JWTManager(app)
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Initialize MongoDB
    mongo = MongoClient(app.config['MONGO_URI'])
    db = mongo[os.getenv('MONGO_DB_NAME', 'ubereats')]
    
    # Make db available to all requests
    @app.before_request
    def before_request():
        app.db = db
    
    # Register error handlers
    from ..middleware.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    # Register routes
    from ..routes import register_routes
    register_routes(app)
    
    # Register WebSocket events
    from ..websocket import register_socket_events
    register_socket_events(socketio)
    
    return app, socketio

# Create the application instance
app, socketio = create_app() 