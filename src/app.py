from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os
from routes.auth_routes import auth_bp
from routes.order import order
from routes.webhook import webhook
from services.notification_service import socketio
from config.database import db, init_db
from config.paypal import configure_paypal, validate_paypal_config
from config.environment import validate_environment
from routes.restaurant_settings import restaurant_settings
from controllers.grocery_controller import grocery

# Load environment variables
load_dotenv()

def create_app():
    """Create and configure the Flask application"""
    # Validate environment variables first
    validate_environment()
    
    app = Flask(__name__)
    
    # Enable CORS
    CORS(app)
    
    # Configure app
    app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/ubereats')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
    
    # Initialize database
    if not init_db():
        raise RuntimeError("Failed to initialize database connection")
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(order, url_prefix='/api')
    app.register_blueprint(webhook)
    app.register_blueprint(restaurant_settings, url_prefix='/api')
    app.register_blueprint(grocery, url_prefix='/api/grocery')

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
    
    # Add CSP headers
    @app.after_request
    def add_security_headers(response):
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https:;"
        return response
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True) 