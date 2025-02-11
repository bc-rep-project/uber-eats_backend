import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from models.tax_rule import TaxRule
from config.database import db
import time

@pytest.fixture(scope="module")
def driver():
    """Setup Chrome WebDriver"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    yield driver
    driver.quit()

@pytest.fixture
def test_restaurant():
    """Create a test restaurant"""
    restaurant = {
        "name": "Integration Test Restaurant",
        "owner_id": "test_owner",
        "cuisine_types": ["Test"],
        "address": {
            "street": "123 Test St",
            "city": "Test City",
            "state": "TS",
            "zip_code": "12345"
        }
    }
    result = db.get_db().restaurants.insert_one(restaurant)
    restaurant_id = str(result.inserted_id)
    yield {"_id": restaurant_id, **restaurant}
    db.get_db().restaurants.delete_one({"_id": result.inserted_id})

@pytest.fixture
def authenticated_session(driver, test_restaurant):
    """Login and return authenticated session"""
    # Login as restaurant owner
    driver.get("http://localhost:3000/login")
    
    email_input = driver.find_element(By.NAME, "email")
    password_input = driver.find_element(By.NAME, "password")
    
    email_input.send_keys("owner@test.com")
    password_input.send_keys("password123")
    password_input.send_keys(Keys.RETURN)
    
    # Wait for redirect to dashboard
    WebDriverWait(driver, 10).until(
        EC.url_to_be(f"http://localhost:3000/restaurant/dashboard")
    )
    
    return driver

def test_end_to_end_tax_rule_management(authenticated_session, test_restaurant):
    """Test complete tax rule management flow"""
    driver = authenticated_session
    
    # Navigate to settings page
    driver.get(f"http://localhost:3000/restaurant/settings")
    
    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//h6[text()='Tax Rules']"))
    )
    
    # 1. Create new tax rule
    driver.find_element(By.XPATH, "//button[text()='Add Tax Rule']").click()
    
    # Fill form
    name_input = driver.find_element(By.NAME, "name")
    rate_input = driver.find_element(By.NAME, "rate")
    description_input = driver.find_element(By.NAME, "description")
    
    name_input.send_keys("Integration Test Tax")
    rate_input.send_keys("8.5")
    description_input.send_keys("Test tax rule created by integration test")
    
    # Submit form
    driver.find_element(By.XPATH, "//button[text()='Save']").click()
    
    # Verify tax rule appears in table
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//td[text()='Integration Test Tax']"))
    )
    
    # Verify in database
    tax_rule = db.get_db().tax_rules.find_one({"name": "Integration Test Tax"})
    assert tax_rule is not None
    assert tax_rule["rate"] == 8.5
    
    # 2. Edit tax rule
    edit_button = driver.find_element(
        By.XPATH,
        "//td[text()='Integration Test Tax']/following-sibling::td//button[@data-testid='edit-button']"
    )
    edit_button.click()
    
    # Update form
    name_input = driver.find_element(By.NAME, "name")
    rate_input = driver.find_element(By.NAME, "rate")
    
    name_input.clear()
    name_input.send_keys("Updated Test Tax")
    rate_input.clear()
    rate_input.send_keys("9.5")
    
    # Submit form
    driver.find_element(By.XPATH, "//button[text()='Save']").click()
    
    # Verify changes in table
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//td[text()='Updated Test Tax']"))
    )
    
    # Verify in database
    updated_rule = db.get_db().tax_rules.find_one({"_id": tax_rule["_id"]})
    assert updated_rule["name"] == "Updated Test Tax"
    assert updated_rule["rate"] == 9.5
    
    # 3. Delete tax rule
    delete_button = driver.find_element(
        By.XPATH,
        "//td[text()='Updated Test Tax']/following-sibling::td//button[@data-testid='delete-button']"
    )
    delete_button.click()
    
    # Wait for deletion
    time.sleep(1)  # Brief wait for animation
    
    # Verify removal from table
    assert len(driver.find_elements(By.XPATH, "//td[text()='Updated Test Tax']")) == 0
    
    # Verify deletion in database
    deleted_rule = db.get_db().tax_rules.find_one({"_id": tax_rule["_id"]})
    assert deleted_rule is None

def test_tax_rule_validation_messages(authenticated_session):
    """Test form validation messages appear correctly"""
    driver = authenticated_session
    
    # Navigate to settings page
    driver.get(f"http://localhost:3000/restaurant/settings")
    
    # Open add tax rule dialog
    driver.find_element(By.XPATH, "//button[text()='Add Tax Rule']").click()
    
    # Try to submit empty form
    driver.find_element(By.XPATH, "//button[text()='Save']").click()
    
    # Verify validation messages
    assert driver.find_element(By.TEXT, "Name is required").is_displayed()
    assert driver.find_element(By.TEXT, "Tax rate is required").is_displayed()
    
    # Try invalid tax rate
    rate_input = driver.find_element(By.NAME, "rate")
    rate_input.send_keys("101")
    
    validation_message = driver.find_element(By.TEXT, "Tax rate must be between 0 and 100")
    assert validation_message.is_displayed()
    
    # Try negative minimum order amount
    min_order_input = driver.find_element(By.NAME, "minimumOrderAmount")
    min_order_input.send_keys("-50")
    
    validation_message = driver.find_element(By.TEXT, "Minimum order amount cannot be negative")
    assert validation_message.is_displayed()

def test_tax_rule_real_time_updates(authenticated_session, test_restaurant):
    """Test that changes are reflected in real-time across multiple sessions"""
    driver1 = authenticated_session
    
    # Create second session
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver2 = webdriver.Chrome(options=options)
    driver2.get("http://localhost:3000/login")
    
    # Login in second session
    email_input = driver2.find_element(By.NAME, "email")
    password_input = driver2.find_element(By.NAME, "password")
    
    email_input.send_keys("owner2@test.com")
    password_input.send_keys("password123")
    password_input.send_keys(Keys.RETURN)
    
    try:
        # Navigate both sessions to settings
        driver1.get(f"http://localhost:3000/restaurant/settings")
        driver2.get(f"http://localhost:3000/restaurant/settings")
        
        # Create tax rule in first session
        driver1.find_element(By.XPATH, "//button[text()='Add Tax Rule']").click()
        
        name_input = driver1.find_element(By.NAME, "name")
        rate_input = driver1.find_element(By.NAME, "rate")
        
        name_input.send_keys("Real-time Test Tax")
        rate_input.send_keys("7.5")
        
        driver1.find_element(By.XPATH, "//button[text()='Save']").click()
        
        # Verify tax rule appears in both sessions
        WebDriverWait(driver1, 10).until(
            EC.presence_of_element_located((By.XPATH, "//td[text()='Real-time Test Tax']"))
        )
        
        WebDriverWait(driver2, 10).until(
            EC.presence_of_element_located((By.XPATH, "//td[text()='Real-time Test Tax']"))
        )
        
        # Edit in second session
        edit_button = driver2.find_element(
            By.XPATH,
            "//td[text()='Real-time Test Tax']/following-sibling::td//button[@data-testid='edit-button']"
        )
        edit_button.click()
        
        name_input = driver2.find_element(By.NAME, "name")
        name_input.clear()
        name_input.send_keys("Updated Real-time Tax")
        
        driver2.find_element(By.XPATH, "//button[text()='Save']").click()
        
        # Verify update appears in both sessions
        WebDriverWait(driver1, 10).until(
            EC.presence_of_element_located((By.XPATH, "//td[text()='Updated Real-time Tax']"))
        )
        
        WebDriverWait(driver2, 10).until(
            EC.presence_of_element_located((By.XPATH, "//td[text()='Updated Real-time Tax']"))
        )
        
    finally:
        driver2.quit()

def test_tax_calculation_integration(authenticated_session, test_restaurant):
    """Test tax calculation works correctly in order flow"""
    driver = authenticated_session
    
    # First create a tax rule
    driver.get(f"http://localhost:3000/restaurant/settings")
    
    driver.find_element(By.XPATH, "//button[text()='Add Tax Rule']").click()
    
    name_input = driver.find_element(By.NAME, "name")
    rate_input = driver.find_element(By.NAME, "rate")
    
    name_input.send_keys("Order Tax")
    rate_input.send_keys("10")  # 10% tax
    
    driver.find_element(By.XPATH, "//button[text()='Save']").click()
    
    # Navigate to menu and add items
    driver.get(f"http://localhost:3000/restaurant/menu")
    
    # Add menu item
    driver.find_element(By.XPATH, "//button[text()='Add Menu Item']").click()
    
    item_name = driver.find_element(By.NAME, "name")
    item_price = driver.find_element(By.NAME, "price")
    
    item_name.send_keys("Test Item")
    item_price.send_keys("100")  # $100 item
    
    driver.find_element(By.XPATH, "//button[text()='Save']").click()
    
    # Navigate to order page
    driver.get(f"http://localhost:3000/restaurant/{test_restaurant['_id']}")
    
    # Add item to cart
    driver.find_element(By.XPATH, "//button[contains(text(), 'Add to Cart')]").click()
    
    # Go to cart
    driver.find_element(By.XPATH, "//button[contains(text(), 'View Cart')]").click()
    
    # Verify tax calculation
    subtotal = driver.find_element(By.ID, "subtotal").text
    tax = driver.find_element(By.ID, "tax").text
    total = driver.find_element(By.ID, "total").text
    
    assert subtotal == "$100.00"
    assert tax == "$10.00"  # 10% of $100
    assert total == "$110.00" 

def test_multiple_tax_rules_calculation(authenticated_session, test_restaurant):
    """Test calculation with multiple tax rules"""
    driver = authenticated_session
    
    # Navigate to settings page
    driver.get(f"http://localhost:3000/restaurant/settings")
    
    # Create first tax rule (State tax)
    driver.find_element(By.XPATH, "//button[text()='Add Tax Rule']").click()
    
    name_input = driver.find_element(By.NAME, "name")
    rate_input = driver.find_element(By.NAME, "rate")
    description_input = driver.find_element(By.NAME, "description")
    
    name_input.send_keys("State Tax")
    rate_input.send_keys("8")  # 8% state tax
    description_input.send_keys("State sales tax")
    
    driver.find_element(By.XPATH, "//button[text()='Save']").click()
    
    # Create second tax rule (City tax)
    driver.find_element(By.XPATH, "//button[text()='Add Tax Rule']").click()
    
    name_input = driver.find_element(By.NAME, "name")
    rate_input = driver.find_element(By.NAME, "rate")
    description_input = driver.find_element(By.NAME, "description")
    
    name_input.send_keys("City Tax")
    rate_input.send_keys("2")  # 2% city tax
    description_input.send_keys("City sales tax")
    
    driver.find_element(By.XPATH, "//button[text()='Save']").click()
    
    # Add menu item and test combined tax calculation
    driver.get(f"http://localhost:3000/restaurant/menu")
    
    driver.find_element(By.XPATH, "//button[text()='Add Menu Item']").click()
    
    item_name = driver.find_element(By.NAME, "name")
    item_price = driver.find_element(By.NAME, "price")
    
    item_name.send_keys("Test Item")
    item_price.send_keys("100")  # $100 item
    
    driver.find_element(By.XPATH, "//button[text()='Save']").click()
    
    # Add to cart and verify combined tax
    driver.get(f"http://localhost:3000/restaurant/{test_restaurant['_id']}")
    driver.find_element(By.XPATH, "//button[contains(text(), 'Add to Cart')]").click()
    driver.find_element(By.XPATH, "//button[contains(text(), 'View Cart')]").click()
    
    subtotal = driver.find_element(By.ID, "subtotal").text
    state_tax = driver.find_element(By.ID, "state-tax").text
    city_tax = driver.find_element(By.ID, "city-tax").text
    total_tax = driver.find_element(By.ID, "total-tax").text
    total = driver.find_element(By.ID, "total").text
    
    assert subtotal == "$100.00"
    assert state_tax == "$8.00"  # 8% of $100
    assert city_tax == "$2.00"   # 2% of $100
    assert total_tax == "$10.00"  # Combined tax
    assert total == "$110.00"    # Subtotal + total tax

def test_tax_rule_with_minimum_order(authenticated_session, test_restaurant):
    """Test tax rule with minimum order amount"""
    driver = authenticated_session
    
    # Navigate to settings page
    driver.get(f"http://localhost:3000/restaurant/settings")
    
    # Create tax rule with minimum order amount
    driver.find_element(By.XPATH, "//button[text()='Add Tax Rule']").click()
    
    name_input = driver.find_element(By.NAME, "name")
    rate_input = driver.find_element(By.NAME, "rate")
    min_order_input = driver.find_element(By.NAME, "minimumOrderAmount")
    
    name_input.send_keys("Luxury Tax")
    rate_input.send_keys("5")  # 5% luxury tax
    min_order_input.send_keys("50")  # Applies to orders over $50
    
    driver.find_element(By.XPATH, "//button[text()='Save']").click()
    
    # Test with item below minimum
    driver.get(f"http://localhost:3000/restaurant/menu")
    
    # Add low-price item
    driver.find_element(By.XPATH, "//button[text()='Add Menu Item']").click()
    item_name = driver.find_element(By.NAME, "name")
    item_price = driver.find_element(By.NAME, "price")
    item_name.send_keys("Budget Item")
    item_price.send_keys("40")  # $40 item
    driver.find_element(By.XPATH, "//button[text()='Save']").click()
    
    # Verify no tax applied
    driver.get(f"http://localhost:3000/restaurant/{test_restaurant['_id']}")
    driver.find_element(By.XPATH, "//button[contains(text(), 'Add to Cart')]").click()
    driver.find_element(By.XPATH, "//button[contains(text(), 'View Cart')]").click()
    
    tax = driver.find_element(By.ID, "tax").text
    assert tax == "$0.00"  # No tax under minimum order
    
    # Test with item above minimum
    driver.get(f"http://localhost:3000/restaurant/menu")
    
    # Add high-price item
    driver.find_element(By.XPATH, "//button[text()='Add Menu Item']").click()
    item_name = driver.find_element(By.NAME, "name")
    item_price = driver.find_element(By.NAME, "price")
    item_name.send_keys("Luxury Item")
    item_price.send_keys("100")  # $100 item
    driver.find_element(By.XPATH, "//button[text()='Save']").click()
    
    # Verify tax applied
    driver.get(f"http://localhost:3000/restaurant/{test_restaurant['_id']}")
    driver.find_element(By.XPATH, "//button[contains(text(), 'Add to Cart')]").click()
    driver.find_element(By.XPATH, "//button[contains(text(), 'View Cart')]").click()
    
    tax = driver.find_element(By.ID, "tax").text
    assert tax == "$5.00"  # 5% of $100

def test_tax_rule_delivery_pickup_options(authenticated_session, test_restaurant):
    """Test tax rules with different delivery/pickup settings"""
    driver = authenticated_session
    
    # Navigate to settings page
    driver.get(f"http://localhost:3000/restaurant/settings")
    
    # Create delivery-only tax rule
    driver.find_element(By.XPATH, "//button[text()='Add Tax Rule']").click()
    
    name_input = driver.find_element(By.NAME, "name")
    rate_input = driver.find_element(By.NAME, "rate")
    delivery_switch = driver.find_element(By.NAME, "appliesToDelivery")
    pickup_switch = driver.find_element(By.NAME, "appliesToPickup")
    
    name_input.send_keys("Delivery Tax")
    rate_input.send_keys("5")  # 5% delivery tax
    delivery_switch.click()  # Enable delivery tax
    pickup_switch.click()    # Disable pickup tax
    
    driver.find_element(By.XPATH, "//button[text()='Save']").click()
    
    # Add test item
    driver.get(f"http://localhost:3000/restaurant/menu")
    driver.find_element(By.XPATH, "//button[text()='Add Menu Item']").click()
    item_name = driver.find_element(By.NAME, "name")
    item_price = driver.find_element(By.NAME, "price")
    item_name.send_keys("Test Item")
    item_price.send_keys("100")
    driver.find_element(By.XPATH, "//button[text()='Save']").click()
    
    # Test delivery order
    driver.get(f"http://localhost:3000/restaurant/{test_restaurant['_id']}")
    driver.find_element(By.XPATH, "//button[contains(text(), 'Add to Cart')]").click()
    driver.find_element(By.XPATH, "//button[contains(text(), 'View Cart')]").click()
    
    # Select delivery option
    delivery_option = driver.find_element(By.ID, "delivery-option")
    delivery_option.click()
    
    tax = driver.find_element(By.ID, "tax").text
    assert tax == "$5.00"  # 5% tax for delivery
    
    # Test pickup order
    pickup_option = driver.find_element(By.ID, "pickup-option")
    pickup_option.click()
    
    tax = driver.find_element(By.ID, "tax").text
    assert tax == "$0.00"  # No tax for pickup

@pytest.mark.slow
def test_tax_rule_concurrent_updates(authenticated_session, test_restaurant):
    """Test concurrent updates to tax rules"""
    driver1 = authenticated_session
    
    # Create second session
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver2 = webdriver.Chrome(options=options)
    
    try:
        # Set up tax rule in first session
        driver1.get(f"http://localhost:3000/restaurant/settings")
        driver1.find_element(By.XPATH, "//button[text()='Add Tax Rule']").click()
        
        name_input = driver1.find_element(By.NAME, "name")
        rate_input = driver1.find_element(By.NAME, "rate")
        
        name_input.send_keys("Concurrent Test Tax")
        rate_input.send_keys("10")
        
        # Before saving in first session, try to create same rule in second session
        driver2.get(f"http://localhost:3000/restaurant/settings")
        driver2.find_element(By.XPATH, "//button[text()='Add Tax Rule']").click()
        
        name_input2 = driver2.find_element(By.NAME, "name")
        rate_input2 = driver2.find_element(By.NAME, "rate")
        
        name_input2.send_keys("Concurrent Test Tax")
        rate_input2.send_keys("15")
        
        # Save in first session
        driver1.find_element(By.XPATH, "//button[text()='Save']").click()
        
        # Try to save in second session
        driver2.find_element(By.XPATH, "//button[text()='Save']").click()
        
        # Verify error message in second session
        error_message = driver2.find_element(By.CLASS_NAME, "error-message")
        assert "Tax rule with this name already exists" in error_message.text
        
        # Verify first session's value persisted
        tax_rate = driver1.find_element(
            By.XPATH,
            "//td[text()='Concurrent Test Tax']/following-sibling::td[1]"
        ).text
        assert tax_rate == "10%"
        
    finally:
        driver2.quit() 