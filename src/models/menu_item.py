from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from bson import ObjectId

class CustomizationOption(BaseModel):
    name: str
    price: float = 0.0
    is_available: bool = True

class Customization(BaseModel):
    name: str
    required: bool = False
    multiple_select: bool = False
    min_selections: int = 0
    max_selections: Optional[int] = None
    options: List[CustomizationOption]

class NutritionalInfo(BaseModel):
    calories: Optional[float]
    protein: Optional[float]  # in grams
    carbohydrates: Optional[float]  # in grams
    fat: Optional[float]  # in grams
    allergens: List[str] = []

class MenuItem(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    restaurant_id: str
    name: str
    description: str
    price: float = Field(..., ge=0.0)
    category: str
    image_url: Optional[str]
    customizations: List[Customization] = []
    nutritional_info: Optional[NutritionalInfo]
    is_available: bool = True
    is_featured: bool = False
    is_vegetarian: bool = False
    is_vegan: bool = False
    is_gluten_free: bool = False
    spiciness_level: int = Field(0, ge=0, le=3)  # 0=Not Spicy, 1=Mild, 2=Medium, 3=Hot
    preparation_time: int  # in minutes
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "restaurant_id": "rest123",
                "name": "Classic Burger",
                "description": "Juicy beef patty with lettuce, tomato, and special sauce",
                "price": 9.99,
                "category": "Burgers",
                "image_url": "https://example.com/images/classic-burger.jpg",
                "customizations": [
                    {
                        "name": "Cheese",
                        "required": False,
                        "multiple_select": False,
                        "options": [
                            {
                                "name": "American",
                                "price": 1.00
                            },
                            {
                                "name": "Cheddar",
                                "price": 1.00
                            }
                        ]
                    },
                    {
                        "name": "Extra Toppings",
                        "required": False,
                        "multiple_select": True,
                        "max_selections": 3,
                        "options": [
                            {
                                "name": "Bacon",
                                "price": 2.00
                            },
                            {
                                "name": "Avocado",
                                "price": 1.50
                            }
                        ]
                    }
                ],
                "nutritional_info": {
                    "calories": 650,
                    "protein": 35,
                    "carbohydrates": 28,
                    "fat": 45,
                    "allergens": ["dairy", "gluten"]
                },
                "preparation_time": 10
            }
        }

    def update_timestamps(self):
        self.updated_at = datetime.utcnow()

    def calculate_price_with_customizations(self, selected_customizations: List[dict]) -> float:
        """Calculate total price including customizations"""
        total_price = self.price

        for selection in selected_customizations:
            customization = next(
                (c for c in self.customizations if c.name == selection["name"]), None
            )
            if customization:
                for option in selection.get("options", []):
                    option_price = next(
                        (o.price for o in customization.options if o.name == option), 0
                    )
                    total_price += option_price

        return total_price 