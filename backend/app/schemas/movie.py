from pydantic import BaseModel
# title, description, genre, release year, image URL
class MoviesOut(BaseModel):
     id : int
     title : str
     genre : str
     year : int
     plot  : str

     class Config:
          from_attributes = True

class MovieStats(BaseModel):
    imdb_id: str
    title: str
    avg_rating: float | None
    review_count: int
    watched_count: int
    watchlist_count: int