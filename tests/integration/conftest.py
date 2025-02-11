import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from config.database import db
from bson import ObjectId
import jwt
import os
from datetime import datetime, timedelta

@pytest.fixture(scope="session")
def app_config():
    """Test configuration"""
    return {
        "BASE_URL": "http://localhost:3000",
        "API_URL": "http://localhost:5000/api",
        "JWT_SECRET": "test_secret",
        "MONGODB_TEST_URI": "mongodb://localhost:27017/ubereats_test"
    }

@pytest.fixture(scope="session")
def db_connection(app_config):
    """Create test database connection"""
    # Switch to test database
    db.init_db(app_config["MONGODB_TEST_URI"])
    yield db.get_db()
    # Clean up test database after all tests
    db.get_db().client.drop_database("ubereats_test")

@pytest.fixture(scope="session")
def chrome_options():
    """Chrome options for Selenium tests"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return options

@pytest.fixture(scope="session")
def driver(chrome_options):
    """Selenium WebDriver fixture"""
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(10)
    yield driver
    driver.quit()

@pytest.fixture
def test_user(db_connection):
    """Create a test user"""
    user = {
        "email": "owner@test.com",
        "password_hash": "hashed_password123",
        "first_name": "Test",
        "last_name": "Owner",
        "role": "restaurant_owner",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = db_connection.users.insert_one(user)
    user_id = str(result.inserted_id)
    user["_id"] = user_id
    yield user
    db_connection.users.delete_one({"_id": result.inserted_id})

@pytest.fixture
def auth_token(test_user, app_config):
    """Generate JWT token for test user"""
    token = jwt.encode(
        {
            "user_id": test_user["_id"],
            "email": test_user["email"],
            "role": test_user["role"],
            "exp": datetime.utcnow() + timedelta(hours=1)
        },
        app_config["JWT_SECRET"],
        algorithm="HS256"
    )
    return token

@pytest.fixture
def test_restaurant(db_connection, test_user):
    """Create a test restaurant"""
    restaurant = {
        "name": "Integration Test Restaurant",
        "owner_id": test_user["_id"],
        "cuisine_types": ["Test"],
        "address": {
            "street": "123 Test St",
            "city": "Test City",
            "state": "TS",
            "zip_code": "12345",
            "location": {
                "type": "Point",
                "coordinates": [-73.935242, 40.730610]
            }
        },
        "price_range": "$$",
        "opening_hours": [
            {
                "day": 0,
                "open": "09:00",
                "close": "22:00"
            }
        ],
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = db_connection.restaurants.insert_one(restaurant)
    restaurant_id = str(result.inserted_id)
    yield {"_id": restaurant_id, **restaurant}
    db_connection.restaurants.delete_one({"_id": result.inserted_id})

@pytest.fixture
def authenticated_session(driver, app_config, test_user, auth_token):
    """Create authenticated session with localStorage token"""
    driver.get(app_config["BASE_URL"])
    
    # Set authentication token in localStorage
    driver.execute_script(
        f"window.localStorage.setItem('token', '{auth_token}')"
    )
    
    # Set user data in localStorage
    driver.execute_script(
        f"window.localStorage.setItem('user', '{{'id': '{test_user['_id']}', 'role': '{test_user['role']}'}}')"
    )
    
    return driver

@pytest.fixture(autouse=True)
def cleanup_db(db_connection):
    """Clean up test data after each test"""
    yield
    collections = ['tax_rules', 'menu_items', 'orders']
    for collection in collections:
        db_connection[collection].delete_many({})

def pytest_configure(config):
    """Configure test markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as a slow test"
    ) 