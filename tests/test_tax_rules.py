import pytest
from datetime import datetime
from bson import ObjectId
from models.tax_rule import TaxRule
from config.database import db

@pytest.fixture
def test_restaurant():
    """Fixture to create a test restaurant"""
    restaurant_id = str(ObjectId())
    return {"_id": restaurant_id, "name": "Test Restaurant"}

@pytest.fixture
def test_user():
    """Fixture to create a test user with restaurant owner role"""
    return {
        "_id": str(ObjectId()),
        "email": "owner@test.com",
        "role": "restaurant_owner"
    }

@pytest.fixture
def sample_tax_rule(test_restaurant):
    """Fixture to create a sample tax rule"""
    return {
        "restaurant_id": test_restaurant["_id"],
        "name": "Test Sales Tax",
        "description": "Test tax rule description",
        "rate": 8.875,
        "is_active": True,
        "applies_to_delivery": True,
        "applies_to_pickup": True,
        "minimum_order_amount": 0.0
    }

def test_tax_rule_model():
    """Test TaxRule model creation and methods"""
    tax_rule = TaxRule(
        restaurant_id="test123",
        name="Test Tax",
        rate=10.0
    )
    
    # Test default values
    assert tax_rule.is_active == True
    assert tax_rule.applies_to_delivery == True
    assert tax_rule.applies_to_pickup == True
    assert tax_rule.minimum_order_amount == 0.0
    
    # Test tax calculation
    assert tax_rule.calculate_tax(100.0) == 10.0
    assert tax_rule.calculate_tax(0.0) == 0.0
    
    # Test minimum order amount
    tax_rule.minimum_order_amount = 50.0
    assert tax_rule.calculate_tax(40.0) == 0.0
    assert tax_rule.calculate_tax(60.0) == 6.0
    
    # Test inactive rule
    tax_rule.is_active = False
    assert tax_rule.calculate_tax(100.0) == 0.0

def test_create_tax_rule(client, test_user, test_restaurant, sample_tax_rule):
    """Test creating a new tax rule"""
    # Login as restaurant owner
    client.set_user(test_user)
    
    response = client.post(
        '/api/restaurant/settings/tax-rules',
        json=sample_tax_rule
    )
    
    assert response.status_code == 201
    data = response.get_json()
    
    assert data["name"] == sample_tax_rule["name"]
    assert data["rate"] == sample_tax_rule["rate"]
    assert "_id" in data
    
    # Verify in database
    saved_rule = db.get_db().tax_rules.find_one({"_id": ObjectId(data["_id"])})
    assert saved_rule is not None
    assert saved_rule["name"] == sample_tax_rule["name"]

def test_get_tax_rules(client, test_user, test_restaurant, sample_tax_rule):
    """Test retrieving tax rules"""
    # Insert test data
    db.get_db().tax_rules.insert_one(sample_tax_rule)
    
    # Login as restaurant owner
    client.set_user(test_user)
    
    response = client.get(
        f'/api/restaurant/settings/tax-rules?restaurant_id={test_restaurant["_id"]}'
    )
    
    assert response.status_code == 200
    data = response.get_json()
    
    assert len(data) == 1
    assert data[0]["name"] == sample_tax_rule["name"]
    assert data[0]["rate"] == sample_tax_rule["rate"]

def test_update_tax_rule(client, test_user, test_restaurant, sample_tax_rule):
    """Test updating a tax rule"""
    # Insert test data
    result = db.get_db().tax_rules.insert_one(sample_tax_rule)
    rule_id = str(result.inserted_id)
    
    # Login as restaurant owner
    client.set_user(test_user)
    
    # Update data
    update_data = {
        "restaurant_id": test_restaurant["_id"],
        "name": "Updated Tax Rule",
        "rate": 9.5,
        "is_active": False
    }
    
    response = client.put(
        f'/api/restaurant/settings/tax-rules/{rule_id}',
        json=update_data
    )
    
    assert response.status_code == 200
    data = response.get_json()
    
    assert data["name"] == update_data["name"]
    assert data["rate"] == update_data["rate"]
    assert data["is_active"] == update_data["is_active"]
    
    # Verify in database
    updated_rule = db.get_db().tax_rules.find_one({"_id": ObjectId(rule_id)})
    assert updated_rule["name"] == update_data["name"]

def test_delete_tax_rule(client, test_user, test_restaurant, sample_tax_rule):
    """Test deleting a tax rule"""
    # Insert test data
    result = db.get_db().tax_rules.insert_one(sample_tax_rule)
    rule_id = str(result.inserted_id)
    
    # Login as restaurant owner
    client.set_user(test_user)
    
    response = client.delete(
        f'/api/restaurant/settings/tax-rules/{rule_id}?restaurant_id={test_restaurant["_id"]}'
    )
    
    assert response.status_code == 200
    
    # Verify deletion in database
    deleted_rule = db.get_db().tax_rules.find_one({"_id": ObjectId(rule_id)})
    assert deleted_rule is None

def test_unauthorized_access(client):
    """Test unauthorized access to tax rules endpoints"""
    # No user logged in
    response = client.get('/api/restaurant/settings/tax-rules')
    assert response.status_code == 401
    
    # Non-restaurant owner user
    client.set_user({"_id": "user123", "role": "customer"})
    response = client.get('/api/restaurant/settings/tax-rules')
    assert response.status_code == 403

def test_validation(client, test_user, test_restaurant):
    """Test input validation"""
    # Login as restaurant owner
    client.set_user(test_user)
    
    # Missing required fields
    response = client.post(
        '/api/restaurant/settings/tax-rules',
        json={"restaurant_id": test_restaurant["_id"]}
    )
    assert response.status_code == 400
    
    # Invalid tax rate
    response = client.post(
        '/api/restaurant/settings/tax-rules',
        json={
            "restaurant_id": test_restaurant["_id"],
            "name": "Test Tax",
            "rate": 101  # Over 100%
        }
    )
    assert response.status_code == 400
    
    # Invalid minimum order amount
    response = client.post(
        '/api/restaurant/settings/tax-rules',
        json={
            "restaurant_id": test_restaurant["_id"],
            "name": "Test Tax",
            "rate": 10,
            "minimum_order_amount": -50  # Negative amount
        }
    )
    assert response.status_code == 400 