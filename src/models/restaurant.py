from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from bson import ObjectId

class OpeningHours(BaseModel):
    day: int = Field(..., ge=0, le=6)  # 0 = Sunday, 6 = Saturday
    open: str
    close: str

class Location(BaseModel):
    type: str = "Point"
    coordinates: List[float]  # [longitude, latitude]

class Address(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "USA"
    location: Location

class RestaurantImage(BaseModel):
    url: str
    alt: str
    is_primary: bool = False

class Restaurant(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    name: str
    description: str
    owner_id: str
    cuisine_types: List[str]
    address: Address
    rating: float = Field(0.0, ge=0.0, le=5.0)
    total_ratings: int = 0
    price_range: str = Field(..., pattern="^[$]{1,4}$")  # $, $$, $$$, $$$$
    opening_hours: List[OpeningHours]
    is_active: bool = True
    features: List[str] = []  # ["delivery", "takeout", "dine-in", etc.]
    delivery_fee: float = 0.0
    minimum_order: float = 0.0
    estimated_delivery_time: int  # in minutes
    preparation_time: int  # in minutes
    images: List[RestaurantImage] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "name": "Burger Palace",
                "description": "Best burgers in town",
                "owner_id": "user123",
                "cuisine_types": ["American", "Fast Food"],
                "address": {
                    "street": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "zip_code": "10001",
                    "country": "USA",
                    "location": {
                        "type": "Point",
                        "coordinates": [-73.935242, 40.730610]
                    }
                },
                "price_range": "$$",
                "opening_hours": [
                    {
                        "day": 0,
                        "open": "11:00",
                        "close": "22:00"
                    }
                ],
                "features": ["delivery", "takeout"],
                "delivery_fee": 2.99,
                "minimum_order": 10.00,
                "estimated_delivery_time": 30,
                "preparation_time": 15
            }
        }

    def update_timestamps(self):
        self.updated_at = datetime.utcnow()

    def calculate_rating(self, new_rating: float):
        """Update restaurant rating when a new review is added"""
        self.rating = ((self.rating * self.total_ratings) + new_rating) / (self.total_ratings + 1)
        self.total_ratings += 1
        self.update_timestamps() 