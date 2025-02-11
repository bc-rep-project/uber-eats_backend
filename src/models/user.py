from datetime import datetime
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from config.database import db

class User:
    def __init__(self, email, password, first_name, last_name, phone_number=None):
        self.email = email.lower()
        self.password_hash = generate_password_hash(password)
        self.first_name = first_name
        self.last_name = last_name
        self.phone_number = phone_number
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.is_active = True
        self.is_verified = False
        self.role = "customer"
        self.preferences = {
            "notifications": True,
            "language": "en",
            "dark_mode": False
        }
        self.saved_addresses = []
        self.payment_methods = []

    @staticmethod
    def create(email, password, first_name, last_name, phone_number=None):
        # Check if user already exists
        if db.get_db().users.find_one({"email": email.lower()}):
            raise ValueError("User with this email already exists")

        user = User(email, password, first_name, last_name, phone_number)
        result = db.get_db().users.insert_one(user.to_dict())
        user._id = result.inserted_id
        return user

    @staticmethod
    def get_by_email(email):
        user_data = db.get_db().users.find_one({"email": email.lower()})
        if user_data:
            return User.from_dict(user_data)
        return None

    @staticmethod
    def get_by_id(user_id):
        user_data = db.get_db().users.find_one({"_id": ObjectId(user_id)})
        if user_data:
            return User.from_dict(user_data)
        return None

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def update(self, **kwargs):
        updates = {}
        allowed_fields = ['first_name', 'last_name', 'phone_number', 'preferences']
        
        for field in allowed_fields:
            if field in kwargs:
                updates[field] = kwargs[field]
        
        if updates:
            updates['updated_at'] = datetime.utcnow()
            db.get_db().users.update_one(
                {"_id": self._id},
                {"$set": updates}
            )
            for key, value in updates.items():
                setattr(self, key, value)

    def add_address(self, address):
        if 'type' not in address or 'address' not in address:
            raise ValueError("Address must contain 'type' and 'address' fields")
        
        db.get_db().users.update_one(
            {"_id": self._id},
            {
                "$push": {"saved_addresses": address},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        self.saved_addresses.append(address)

    def add_payment_method(self, payment_method):
        if 'type' not in payment_method or 'last4' not in payment_method:
            raise ValueError("Payment method must contain 'type' and 'last4' fields")
        
        db.get_db().users.update_one(
            {"_id": self._id},
            {
                "$push": {"payment_methods": payment_method},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        self.payment_methods.append(payment_method)

    def to_dict(self):
        return {
            "email": self.email,
            "password_hash": self.password_hash,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone_number": self.phone_number,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "role": self.role,
            "preferences": self.preferences,
            "saved_addresses": self.saved_addresses,
            "payment_methods": self.payment_methods
        }

    @staticmethod
    def from_dict(data):
        user = User(
            email=data['email'],
            password="",  # Password hash is already stored
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone_number=data.get('phone_number')
        )
        user._id = data['_id']
        user.password_hash = data['password_hash']
        user.created_at = data['created_at']
        user.updated_at = data['updated_at']
        user.is_active = data['is_active']
        user.is_verified = data['is_verified']
        user.role = data['role']
        user.preferences = data['preferences']
        user.saved_addresses = data['saved_addresses']
        user.payment_methods = data['payment_methods']
        return user 