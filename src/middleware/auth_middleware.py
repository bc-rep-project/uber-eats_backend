from functools import wraps
from flask import request, jsonify
from services.auth_service import auth_service

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check if token is in headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401

        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            current_user = auth_service.verify_token(token)
            if not current_user:
                return jsonify({'message': 'Invalid token'}), 401
            return f(current_user, *args, **kwargs)
        except ValueError as e:
            return jsonify({'message': str(e)}), 401
        except Exception as e:
            return jsonify({'message': 'Something went wrong'}), 500

    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401

        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            current_user = auth_service.verify_token(token)
            if not current_user:
                return jsonify({'message': 'Invalid token'}), 401
            if current_user.role != 'admin':
                return jsonify({'message': 'Admin privileges required'}), 403
            return f(current_user, *args, **kwargs)
        except ValueError as e:
            return jsonify({'message': str(e)}), 401
        except Exception as e:
            return jsonify({'message': 'Something went wrong'}), 500

    return decorated 