from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, conint
from bson import ObjectId

class ReviewImage(BaseModel):
    url: str
    caption: Optional[str]

class ReviewResponse(BaseModel):
    comment: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Review(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    user_id: str
    restaurant_id: str
    order_id: str
    rating: conint(ge=1, le=5)  # Rating from 1 to 5
    comment: str
    images: List[ReviewImage] = []
    food_rating: conint(ge=1, le=5)
    service_rating: conint(ge=1, le=5)
    delivery_rating: Optional[conint(ge=1, le=5)]
    likes_count: int = 0
    is_verified_order: bool = True
    response: Optional[ReviewResponse]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "user_id": "user123",
                "restaurant_id": "rest123",
                "order_id": "order123",
                "rating": 4,
                "comment": "Great food and quick delivery!",
                "images": [
                    {
                        "url": "https://example.com/images/review1.jpg",
                        "caption": "Delicious burger"
                    }
                ],
                "food_rating": 5,
                "service_rating": 4,
                "delivery_rating": 4,
                "is_verified_order": True
            }
        }

    def update_timestamps(self):
        self.updated_at = datetime.utcnow()

    def add_response(self, comment: str):
        """Add restaurant response to the review"""
        self.response = ReviewResponse(
            comment=comment,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.update_timestamps()

    def update_response(self, comment: str):
        """Update restaurant response"""
        if self.response:
            self.response.comment = comment
            self.response.updated_at = datetime.utcnow()
            self.update_timestamps()

    def increment_likes(self):
        """Increment likes count"""
        self.likes_count += 1
        self.update_timestamps()

    def decrement_likes(self):
        """Decrement likes count"""
        if self.likes_count > 0:
            self.likes_count -= 1
            self.update_timestamps() 