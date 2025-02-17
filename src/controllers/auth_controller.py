from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from bson import ObjectId
import os

from ..models.user import User
from ..config.database import db
from ..middleware.auth import token_required

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Check if user already exists
        if db.users.find_one({'email': data['email']}):
            return jsonify({'message': 'Email already registered'}), 400
        
        # Create new user
        user = User(
            email=data['email'],
            password=generate_password_hash(data['password']),
            first_name=data['firstName'],
            last_name=data['lastName'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Insert user into database
        result = db.users.insert_one(user.dict(exclude={'id'}))
        user.id = str(result.inserted_id)
        
        # Generate token
        token = jwt.encode({
            'user_id': str(result.inserted_id),
            'exp': datetime.utcnow() + timedelta(days=1)
        }, os.getenv('JWT_SECRET'))
        
        return jsonify({
            'token': token,
            'user': {
                'id': str(result.inserted_id),
                'email': user.email,
                'firstName': user.first_name,
                'lastName': user.last_name
            }
        }), 201
        
    except Exception as e:
        return jsonify({'message': str(e)}), 400

@auth.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        # Find user
        user = db.users.find_one({'email': data['email']})
        if not user or not check_password_hash(user['password'], data['password']):
            return jsonify({'message': 'Invalid credentials'}), 401
        
        # Generate token
        token = jwt.encode({
            'user_id': str(user['_id']),
            'exp': datetime.utcnow() + timedelta(days=1)
        }, os.getenv('JWT_SECRET'))
        
        return jsonify({
            'token': token,
            'user': {
                'id': str(user['_id']),
                'email': user['email'],
                'firstName': user['first_name'],
                'lastName': user['last_name']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 400

@auth.route('/refresh', methods=['POST'])
@token_required
def refresh_token(current_user):
    try:
        # Generate new token
        token = jwt.encode({
            'user_id': str(current_user['_id']),
            'exp': datetime.utcnow() + timedelta(days=1)
        }, os.getenv('JWT_SECRET'))
        
        return jsonify({'token': token}), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 400

@auth.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    # In a more complex implementation, you might want to invalidate the token
    # For now, the frontend will handle token removal
    return jsonify({'message': 'Successfully logged out'}), 200

@auth.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    return jsonify({
        'id': str(current_user['_id']),
        'email': current_user['email'],
        'firstName': current_user['first_name'],
        'lastName': current_user['last_name']
    }), 200