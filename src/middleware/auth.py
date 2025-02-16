from functools import wraps
from flask import request, current_app, g, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from .error_handlers import BusinessError
import jwt
import os
from bson import ObjectId

from ..config.database import db

def auth_required(roles=None):
    """
    Decorator for routes that require authentication.
    Optionally checks if user has required roles.
    
    Args:
        roles (list): Optional list of required roles
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Verify JWT token
            verify_jwt_in_request()
            
            # Get user identity and claims
            user_id = get_jwt_identity()
            claims = get_jwt()
            
            # Store user info in g for route handlers
            g.user_id = user_id
            g.user_roles = claims.get('roles', [])
            
            # Check roles if specified
            if roles:
                if not set(roles).intersection(set(g.user_roles)):
                    raise BusinessError(
                        message='Insufficient permissions',
                        code='AUTH_INSUFFICIENT_ROLES',
                        status_code=403,
                        details=f'Required roles: {roles}'
                    )
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def admin_required(fn):
    """Decorator for routes that require admin role"""
    return auth_required(roles=['admin'])(fn)

def restaurant_required(fn):
    """Decorator for routes that require restaurant owner role"""
    return auth_required(roles=['restaurant_owner'])(fn)

def delivery_required(fn):
    """Decorator for routes that require delivery driver role"""
    return auth_required(roles=['delivery_driver'])(fn)

def get_token_from_header():
    """Extract token from Authorization header"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
        
    parts = auth_header.split()
    if parts[0].lower() != 'bearer' or len(parts) != 2:
        return None
        
    return parts[1]

def init_auth_middleware(app):
    """Initialize authentication middleware"""
    
    @app.before_request
    def authenticate_request():
        # Skip auth for public endpoints
        if request.endpoint in app.config.get('PUBLIC_ENDPOINTS', []):
            return
            
        # Skip auth for OPTIONS requests (CORS)
        if request.method == 'OPTIONS':
            return
            
        token = get_token_from_header()
        if not token:
            raise BusinessError(
                message='Missing authentication token',
                code='AUTH_MISSING_TOKEN',
                status_code=401
            )

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401
                
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
            
        try:
            # Decode token
            data = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=["HS256"])
            current_user = db.users.find_one({'_id': ObjectId(data['user_id'])})
            
            if not current_user:
                return jsonify({'message': 'Invalid token'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
            
        return f(current_user, *args, **kwargs)
        
    return decorated 