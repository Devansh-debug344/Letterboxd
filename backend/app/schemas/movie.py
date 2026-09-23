from pydantic import BaseModel
from typing import Optional
# title, description, genre, release year, image URL
class MoviesOut(BaseModel):
     id : int
     imdb_id: Optional[str] = None
     title : str
     genre : str
     year : int
     plot  : str
     language : Optional[str] = None
     country : Optional[str] = None
     poster: Optional[str] = None
     

     class Config:
          from_attributes = True

class MovieStats(BaseModel):
    imdb_id: str
    title: str
    avg_rating: float | None
    review_count: int
    watched_count: int
    watchlist_count: int
