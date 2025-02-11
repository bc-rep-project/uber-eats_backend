import pytest
from models.user import User
from werkzeug.security import check_password_hash

def test_create_user(mongo, test_user_data):
    """Test creating a new user."""
    user = User.create(**test_user_data)
    
    assert user is not None
    assert user.email == test_user_data['email'].lower()
    assert user.first_name == test_user_data['first_name']
    assert user.last_name == test_user_data['last_name']
    assert user.phone_number == test_user_data['phone_number']
    assert user.is_active is True
    assert user.is_verified is False
    assert user.role == 'customer'

def test_create_duplicate_user(mongo, test_user_data):
    """Test that creating a duplicate user raises an error."""
    User.create(**test_user_data)
    
    with pytest.raises(ValueError, match="User with this email already exists"):
        User.create(**test_user_data)

def test_get_user_by_email(mongo, test_user_data):
    """Test retrieving a user by email."""
    created_user = User.create(**test_user_data)
    retrieved_user = User.get_by_email(test_user_data['email'])
    
    assert retrieved_user is not None
    assert str(retrieved_user._id) == str(created_user._id)
    assert retrieved_user.email == created_user.email.lower()

def test_get_nonexistent_user(mongo):
    """Test retrieving a non-existent user returns None."""
    user = User.get_by_email('nonexistent@example.com')
    assert user is None

def test_verify_password(mongo, test_user_data):
    """Test password verification."""
    user = User.create(**test_user_data)
    
    assert user.verify_password(test_user_data['password']) is True
    assert user.verify_password('wrong_password') is False

def test_update_user(mongo, test_user_data):
    """Test updating user information."""
    user = User.create(**test_user_data)
    
    updates = {
        'first_name': 'Updated',
        'last_name': 'Name',
        'phone_number': '+9876543210'
    }
    
    user.update(**updates)
    
    updated_user = User.get_by_email(test_user_data['email'])
    assert updated_user.first_name == updates['first_name']
    assert updated_user.last_name == updates['last_name']
    assert updated_user.phone_number == updates['phone_number']

def test_add_address(mongo, test_user_data):
    """Test adding an address to user."""
    user = User.create(**test_user_data)
    
    address = {
        'type': 'home',
        'address': '123 Test St',
        'city': 'Test City',
        'state': 'TS',
        'zip': '12345'
    }
    
    user.add_address(address)
    
    updated_user = User.get_by_email(test_user_data['email'])
    assert len(updated_user.saved_addresses) == 1
    assert updated_user.saved_addresses[0] == address

def test_add_invalid_address(mongo, test_user_data):
    """Test adding an invalid address raises an error."""
    user = User.create(**test_user_data)
    
    invalid_address = {'city': 'Test City'}  # Missing required fields
    
    with pytest.raises(ValueError, match="Address must contain 'type' and 'address' fields"):
        user.add_address(invalid_address)

def test_add_payment_method(mongo, test_user_data):
    """Test adding a payment method to user."""
    user = User.create(**test_user_data)
    
    payment_method = {
        'type': 'credit_card',
        'last4': '4242',
        'exp_month': 12,
        'exp_year': 2025
    }
    
    user.add_payment_method(payment_method)
    
    updated_user = User.get_by_email(test_user_data['email'])
    assert len(updated_user.payment_methods) == 1
    assert updated_user.payment_methods[0] == payment_method

def test_add_invalid_payment_method(mongo, test_user_data):
    """Test adding an invalid payment method raises an error."""
    user = User.create(**test_user_data)
    
    invalid_payment = {'type': 'credit_card'}  # Missing required fields
    
    with pytest.raises(ValueError, match="Payment method must contain 'type' and 'last4' fields"):
        user.add_payment_method(invalid_payment)

def test_user_to_dict(mongo, test_user_data):
    """Test converting user to dictionary."""
    user = User.create(**test_user_data)
    user_dict = user.to_dict()
    
    assert user_dict['email'] == test_user_data['email'].lower()
    assert user_dict['first_name'] == test_user_data['first_name']
    assert user_dict['last_name'] == test_user_data['last_name']
    assert user_dict['phone_number'] == test_user_data['phone_number']
    assert 'password_hash' in user_dict
    assert check_password_hash(user_dict['password_hash'], test_user_data['password']) 