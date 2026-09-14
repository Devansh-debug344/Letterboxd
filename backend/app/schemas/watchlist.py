from pydantic import BaseModel
from typing import Optional
class CreateSaveMovies(BaseModel):
       omdb_id : str 


class SaveMoviesOut(BaseModel):
       movie_id : int
       user_id : int

       class Config:
              from_attributes = True

class SaveMoviesUpdate(BaseModel):
       movie_name : str
       rating : Optional[int] = None
       status : Optional[str] = None
       note : Optional[str] = None

class SaveMoviesDelete(BaseModel):
       movie_name : str
    