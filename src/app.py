from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os
from routes.auth_routes import auth_bp
from routes.order import order
from routes.webhook import webhook
from services.notification_service import socketio
from config.database import db
from config.paypal import configure_paypal, validate_paypal_config

# Load environment variables
load_dotenv()

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Enable CORS
    CORS(app)
    
    # Configure app
    app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/ubereats')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(order)
    app.register_blueprint(webhook)
    
    # Initialize database
    db.connect()

    # Configure PayPal
    configure_paypal()
    validate_paypal_config()

    # Initialize SocketIO
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Register error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500
    
    # Register routes
    @app.route('/health')
    def health_check():
        return {'status': 'healthy'}, 200
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True) 