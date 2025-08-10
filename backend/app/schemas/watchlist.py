from pydantic import BaseModel
from typing import Optional
class CreateSaveMovies(BaseModel):
       movie_name : str
       rating : Optional[int] = None
       status : Optional[str] = None
       note : Optional[str] = None


class SaveMoviesOut(BaseModel):
       movie_id : int
       movie_name : str
       user_name : str
       status : Optional[str] = None
       note : Optional[str] = None

       class Config:
              orm_mode = True

class SaveMoviesUpdate(BaseModel):
       movie_name : str
       rating : Optional[int] = None
       status : Optional[str] = None
       note : Optional[str] = None

class SaveMoviesDelete(BaseModel):
       movie_name : str
    