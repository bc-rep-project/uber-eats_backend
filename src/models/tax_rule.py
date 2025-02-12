from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, condecimal
from bson import ObjectId

class TaxRule(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    restaurant_id: str
    name: str
    description: Optional[str]
    rate: condecimal(ge=0, le=100, decimal_places=2)  # Tax rate as percentage
    is_active: bool = True
    applies_to_delivery: bool = True
    applies_to_pickup: bool = True
    minimum_order_amount: float = 0.0  # Minimum order amount for tax to apply
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "restaurant_id": "rest123",
                "name": "Sales Tax",
                "description": "Standard state sales tax",
                "rate": 8.875,  # 8.875%
                "is_active": True,
                "applies_to_delivery": True,
                "applies_to_pickup": True,
                "minimum_order_amount": 0.0
            }
        }

    def update_timestamps(self):
        self.updated_at = datetime.utcnow()

    def calculate_tax(self, subtotal: float) -> float:
        """Calculate tax amount for a given subtotal"""
        if subtotal < self.minimum_order_amount or not self.is_active:
            return 0.0
        return round(subtotal * (float(self.rate) / 100), 2) 