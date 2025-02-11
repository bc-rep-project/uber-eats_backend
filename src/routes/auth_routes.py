from flask import Blueprint, request, jsonify
from services.auth_service import auth_service
from middleware.auth_middleware import token_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'Missing required field: {field}'}), 400

        # Optional field
        phone_number = data.get('phone_number')

        # Register user
        result = auth_service.register_user(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone_number=phone_number
        )

        return jsonify(result), 201

    except ValueError as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        return jsonify({'message': 'Error during registration'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'message': 'Missing email or password'}), 400

        # Login user
        result = auth_service.login_user(
            email=data['email'],
            password=data['password']
        )

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({'message': str(e)}), 401
    except Exception as e:
        return jsonify({'message': 'Error during login'}), 500

@auth_bp.route('/refresh-token', methods=['POST'])
@token_required
def refresh_token(current_user):
    try:
        token = request.headers.get('Authorization').split(" ")[1]
        new_token = auth_service.refresh_token(token)
        return jsonify({'token': new_token}), 200
    except ValueError as e:
        return jsonify({'message': str(e)}), 401
    except Exception as e:
        return jsonify({'message': 'Error refreshing token'}), 500

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    try:
        return jsonify({'user': auth_service._user_to_dict(current_user)}), 200
    except Exception as e:
        return jsonify({'message': 'Error fetching user data'}), 500 