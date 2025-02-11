from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field
from bson import ObjectId

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    PICKED_UP = "picked_up"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    CASH = "cash"

class ItemCustomization(BaseModel):
    name: str
    options: List[str]

class OrderItem(BaseModel):
    menu_item_id: str
    name: str
    quantity: int = Field(..., gt=0)
    unit_price: float
    customizations: List[ItemCustomization] = []
    special_instructions: Optional[str]
    subtotal: float

    def calculate_subtotal(self) -> float:
        return self.unit_price * self.quantity

class DeliveryInfo(BaseModel):
    address: str
    city: str
    state: str
    zip_code: str
    latitude: float
    longitude: float
    instructions: Optional[str]
    driver_id: Optional[str]
    estimated_delivery_time: Optional[datetime]
    actual_delivery_time: Optional[datetime]

class PaymentInfo(BaseModel):
    method: PaymentMethod
    subtotal: float
    tax: float
    delivery_fee: float
    service_fee: float
    tip: float = 0.0
    total: float
    status: PaymentStatus = PaymentStatus.PENDING
    transaction_id: Optional[str]

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    user_id: str
    restaurant_id: str
    items: List[OrderItem]
    status: OrderStatus = OrderStatus.PENDING
    delivery_info: DeliveryInfo
    payment_info: PaymentInfo
    is_scheduled: bool = False
    scheduled_for: Optional[datetime]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    estimated_preparation_time: int  # in minutes
    special_instructions: Optional[str]

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "user_id": "user123",
                "restaurant_id": "rest123",
                "items": [
                    {
                        "menu_item_id": "item123",
                        "name": "Classic Burger",
                        "quantity": 2,
                        "unit_price": 9.99,
                        "customizations": [
                            {
                                "name": "Cheese",
                                "options": ["American"]
                            }
                        ],
                        "special_instructions": "No onions please",
                        "subtotal": 19.98
                    }
                ],
                "delivery_info": {
                    "address": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "zip_code": "10001",
                    "latitude": 40.730610,
                    "longitude": -73.935242,
                    "instructions": "Ring doorbell 2B"
                },
                "payment_info": {
                    "method": "credit_card",
                    "subtotal": 19.98,
                    "tax": 1.77,
                    "delivery_fee": 2.99,
                    "service_fee": 1.99,
                    "tip": 4.00,
                    "total": 30.73
                },
                "estimated_preparation_time": 20
            }
        }

    def update_status(self, new_status: OrderStatus):
        """Update order status and timestamp"""
        self.status = new_status
        self.updated_at = datetime.utcnow()

    def calculate_total(self) -> float:
        """Calculate total order amount"""
        return (
            self.payment_info.subtotal +
            self.payment_info.tax +
            self.payment_info.delivery_fee +
            self.payment_info.service_fee +
            self.payment_info.tip
        )

    def can_cancel(self) -> bool:
        """Check if order can be cancelled"""
        return self.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED]

    def can_modify(self) -> bool:
        """Check if order can be modified"""
        return self.status == OrderStatus.PENDING 