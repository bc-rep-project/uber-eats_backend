from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from bson import ObjectId

class GroceryCategory(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    name: str
    icon: str
    order: int = 0

class GroceryProduct(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    store_id: str
    name: str
    description: Optional[str]
    price: float
    original_price: Optional[float]
    calories: Optional[str]
    image_url: str
    category: str
    in_stock: bool = True
    unit: str = "item"  # item, lb, oz, etc.
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class GroceryStore(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    name: str
    description: str
    image_url: str
    delivery_time: str  # e.g., "30-50"
    delivery_fee: float
    minimum_order: float = 0.0
    rating: float = Field(0.0, ge=0.0, le=5.0)
    total_ratings: int = 0
    categories: List[str] = []  # References to GroceryCategory ids
    offers: Optional[str]
    is_featured: bool = False
    address: dict
    operating_hours: List[dict]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True 