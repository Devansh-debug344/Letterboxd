from datetime import datetime
from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    omdb_id: str
    rating: float = Field(..., ge=0.5, le=5)
    review: str | None = None
    spoiler: bool = False


class ReviewUpdate(BaseModel):
    omdb_id: str
    rating: float | None = Field(default=None, ge=0.5, le=5)
    review: str | None = None
    spoiler: bool | None = None


class ReviewDelete(BaseModel):
    omdb_id: str


class ReviewOut(BaseModel):
    id: int
    movie_id: int
    user_id: int
    movie_name: str
    user_name: str
    rating: float
    review: str | None
    likes: int
    updated_at: datetime

    class Config:
        from_attributes: True