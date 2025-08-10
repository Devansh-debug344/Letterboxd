from pydantic import BaseModel
from typing import Optional
from datetime import datetime
class ReviewCreate(BaseModel):
      movie_name : str
      review : str
      likes : int

class ReviewOut(BaseModel):
      movie_id : int 
      user_id : int
      movie_name : str
      user_name : str
      review : str
      likes : int
      updated_at : datetime

      class Config:
            orm_mode = True

class ReviewUpdate(BaseModel):
    movie_name : str
    review : Optional[str] = None
    likes : Optional[int] = None

class ReviewDelete(BaseModel):
    movie_name : str
