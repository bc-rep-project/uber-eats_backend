import json
import pytest
from models.user import User

def test_register_endpoint(client, test_user_data):
    """Test the registration endpoint."""
    response = client.post(
        '/api/auth/register',
        data=json.dumps(test_user_data),
        content_type='application/json'
    )
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'user' in data
    assert 'token' in data
    assert data['user']['email'] == test_user_data['email'].lower()
    assert 'password_hash' not in data['user']

def test_register_missing_fields(client):
    """Test registration with missing required fields."""
    incomplete_data = {
        'email': 'test@example.com',
        'password': 'password123'
        # Missing first_name and last_name
    }
    
    response = client.post(
        '/api/auth/register',
        data=json.dumps(incomplete_data),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'message' in data
    assert 'Missing required field' in data['message']

def test_login_endpoint(client, test_user_data):
    """Test the login endpoint."""
    # First register the user
    client.post(
        '/api/auth/register',
        data=json.dumps(test_user_data),
        content_type='application/json'
    )
    
    # Then try to login
    login_data = {
        'email': test_user_data['email'],
        'password': test_user_data['password']
    }
    
    response = client.post(
        '/api/auth/login',
        data=json.dumps(login_data),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'user' in data
    assert 'token' in data
    assert data['user']['email'] == test_user_data['email'].lower()

def test_login_wrong_password(client, test_user_data):
    """Test login with wrong password."""
    # First register the user
    client.post(
        '/api/auth/register',
        data=json.dumps(test_user_data),
        content_type='application/json'
    )
    
    # Try to login with wrong password
    login_data = {
        'email': test_user_data['email'],
        'password': 'wrong_password'
    }
    
    response = client.post(
        '/api/auth/login',
        data=json.dumps(login_data),
        content_type='application/json'
    )
    
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'message' in data
    assert data['message'] == 'Invalid email or password'

def test_refresh_token_endpoint(client, test_user_data):
    """Test the token refresh endpoint."""
    # First register and get a token
    register_response = client.post(
        '/api/auth/register',
        data=json.dumps(test_user_data),
        content_type='application/json'
    )
    token = json.loads(register_response.data)['token']
    
    # Try to refresh the token
    response = client.post(
        '/api/auth/refresh-token',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'token' in data
    assert data['token'] != token

def test_refresh_token_invalid_token(client):
    """Test token refresh with invalid token."""
    response = client.post(
        '/api/auth/refresh-token',
        headers={'Authorization': 'Bearer invalid_token'}
    )
    
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'message' in data
    assert 'Invalid token' in data['message']

def test_get_current_user(client, test_user_data):
    """Test getting current user information."""
    # First register and get a token
    register_response = client.post(
        '/api/auth/register',
        data=json.dumps(test_user_data),
        content_type='application/json'
    )
    token = json.loads(register_response.data)['token']
    
    # Try to get current user info
    response = client.get(
        '/api/auth/me',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'user' in data
    assert data['user']['email'] == test_user_data['email'].lower()
    assert 'password_hash' not in data['user']

def test_get_current_user_no_token(client):
    """Test getting current user without token."""
    response = client.get('/api/auth/me')
    
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'message' in data
    assert data['message'] == 'Token is missing' 