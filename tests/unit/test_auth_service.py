import pytest
import jwt
from datetime import datetime, timedelta
from services.auth_service import auth_service
from models.user import User

def test_register_user(mongo, test_user_data):
    """Test user registration."""
    result = auth_service.register_user(**test_user_data)
    
    assert 'user' in result
    assert 'token' in result
    assert result['user']['email'] == test_user_data['email'].lower()
    assert 'password_hash' not in result['user']
    
    # Verify token
    payload = jwt.decode(result['token'], auth_service.secret_key, algorithms=['HS256'])
    assert payload['email'] == test_user_data['email'].lower()

def test_register_duplicate_user(mongo, test_user_data):
    """Test registering a duplicate user raises an error."""
    auth_service.register_user(**test_user_data)
    
    with pytest.raises(ValueError, match="User with this email already exists"):
        auth_service.register_user(**test_user_data)

def test_login_user(mongo, test_user_data):
    """Test user login."""
    # First register the user
    auth_service.register_user(**test_user_data)
    
    # Then try to login
    result = auth_service.login_user(
        email=test_user_data['email'],
        password=test_user_data['password']
    )
    
    assert 'user' in result
    assert 'token' in result
    assert result['user']['email'] == test_user_data['email'].lower()
    assert 'password_hash' not in result['user']

def test_login_with_wrong_password(mongo, test_user_data):
    """Test login with incorrect password."""
    auth_service.register_user(**test_user_data)
    
    with pytest.raises(ValueError, match="Invalid email or password"):
        auth_service.login_user(
            email=test_user_data['email'],
            password='wrong_password'
        )

def test_login_nonexistent_user(mongo):
    """Test login with non-existent user."""
    with pytest.raises(ValueError, match="Invalid email or password"):
        auth_service.login_user(
            email='nonexistent@example.com',
            password='password123'
        )

def test_generate_token(mongo, test_user_data):
    """Test token generation."""
    user = User.create(**test_user_data)
    token = auth_service.generate_token(user)
    
    payload = jwt.decode(token, auth_service.secret_key, algorithms=['HS256'])
    assert payload['email'] == user.email
    assert payload['user_id'] == str(user._id)
    assert payload['role'] == user.role
    
    # Check expiration
    exp_time = datetime.fromtimestamp(payload['exp'])
    expected_exp = datetime.utcnow() + timedelta(seconds=auth_service.jwt_expiration)
    assert abs((exp_time - expected_exp).total_seconds()) < 5  # Allow 5 seconds difference

def test_verify_token(mongo, test_user_data):
    """Test token verification."""
    # Register user and get token
    result = auth_service.register_user(**test_user_data)
    token = result['token']
    
    # Verify token
    user = auth_service.verify_token(token)
    assert user is not None
    assert user.email == test_user_data['email'].lower()

def test_verify_invalid_token(mongo):
    """Test verification of invalid token."""
    with pytest.raises(ValueError, match="Invalid token"):
        auth_service.verify_token("invalid_token")

def test_verify_expired_token(mongo, test_user_data):
    """Test verification of expired token."""
    user = User.create(**test_user_data)
    
    # Create an expired token
    payload = {
        'user_id': str(user._id),
        'email': user.email,
        'role': user.role,
        'exp': datetime.utcnow() - timedelta(seconds=1)  # Token expired 1 second ago
    }
    expired_token = jwt.encode(payload, auth_service.secret_key, algorithm='HS256')
    
    with pytest.raises(ValueError, match="Token has expired"):
        auth_service.verify_token(expired_token)

def test_refresh_token(mongo, test_user_data):
    """Test token refresh."""
    # Register user and get token
    result = auth_service.register_user(**test_user_data)
    old_token = result['token']
    
    # Refresh token
    new_token = auth_service.refresh_token(old_token)
    
    assert new_token != old_token
    
    # Verify new token
    payload = jwt.decode(new_token, auth_service.secret_key, algorithms=['HS256'])
    assert payload['email'] == test_user_data['email'].lower()

def test_refresh_invalid_token(mongo):
    """Test refreshing an invalid token."""
    with pytest.raises(ValueError):
        auth_service.refresh_token("invalid_token") 