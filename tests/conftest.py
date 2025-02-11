import pytest
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from app import create_app

# Load test environment variables
load_dotenv()

@pytest.fixture
def app():
    """Create and configure a test Flask application instance."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['MONGO_URI'] = os.getenv('TEST_MONGO_URI', 'mongodb://localhost:27017/ubereats_test')
    return app

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

@pytest.fixture
def mongo():
    """Create a MongoDB test database connection."""
    client = MongoClient(os.getenv('TEST_MONGO_URI', 'mongodb://localhost:27017/ubereats_test'))
    db = client.get_database()
    yield db
    # Clean up the test database after tests
    client.drop_database(db.name)
    client.close()

@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        'email': 'test@example.com',
        'password': 'Test123!',
        'first_name': 'Test',
        'last_name': 'User',
        'phone_number': '+1234567890'
    }

@pytest.fixture
def test_admin_data():
    """Sample admin user data for testing."""
    return {
        'email': 'admin@example.com',
        'password': 'Admin123!',
        'first_name': 'Admin',
        'last_name': 'User',
        'phone_number': '+1987654321',
        'role': 'admin'
    } 