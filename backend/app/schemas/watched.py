from datetime import datetime
from pydantic import BaseModel, Field


class WatchedCreate(BaseModel):
    omdb_id: str
    rating: float | None = None
    watched_at: datetime | None = None


class WatchedOut(BaseModel):
    id: int
    omdb_id: int
    title: str
    year: int | None
    poster: str | None
    rating: float | None
    watched_at: datetime

    class Config:
      from_attributes: True