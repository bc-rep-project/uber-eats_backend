from pymongo import ASCENDING, DESCENDING, GEOSPHERE, TEXT

def setup_indexes(db):
    """Set up all necessary indexes for the application"""
    
    # Restaurant indexes
    db.restaurants.create_index([("name", TEXT), ("cuisine_types", TEXT), ("description", TEXT)])
    db.restaurants.create_index([("address.location", GEOSPHERE)])
    db.restaurants.create_index([("owner_id", ASCENDING)])
    db.restaurants.create_index([("cuisine_types", ASCENDING)])
    db.restaurants.create_index([("is_active", ASCENDING)])
    db.restaurants.create_index([("rating", DESCENDING)])

    # Menu item indexes
    db.menu_items.create_index([("restaurant_id", ASCENDING)])
    db.menu_items.create_index([("name", TEXT), ("description", TEXT)])
    db.menu_items.create_index([("category", ASCENDING)])
    db.menu_items.create_index([("is_available", ASCENDING)])
    db.menu_items.create_index([
        ("restaurant_id", ASCENDING),
        ("category", ASCENDING),
        ("is_available", ASCENDING)
    ])

    # Order indexes
    db.orders.create_index([("user_id", ASCENDING)])
    db.orders.create_index([("restaurant_id", ASCENDING)])
    db.orders.create_index([("status", ASCENDING)])
    db.orders.create_index([("created_at", DESCENDING)])
    db.orders.create_index([
        ("restaurant_id", ASCENDING),
        ("status", ASCENDING),
        ("created_at", DESCENDING)
    ])
    db.orders.create_index([
        ("user_id", ASCENDING),
        ("status", ASCENDING),
        ("created_at", DESCENDING)
    ])

    # Review indexes
    db.reviews.create_index([("restaurant_id", ASCENDING)])
    db.reviews.create_index([("user_id", ASCENDING)])
    db.reviews.create_index([("order_id", ASCENDING)])
    db.reviews.create_index([("rating", DESCENDING)])
    db.reviews.create_index([
        ("restaurant_id", ASCENDING),
        ("created_at", DESCENDING)
    ])
    db.reviews.create_index([("comment", TEXT)])

    # User indexes
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.users.create_index([("phone_number", ASCENDING)], sparse=True)
    db.users.create_index([("role", ASCENDING)])
    
    print("All database indexes have been created successfully") 