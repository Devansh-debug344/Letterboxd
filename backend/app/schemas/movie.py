from pydantic import BaseModel
# title, description, genre, release year, image URL
class MoviesOut(BaseModel):
     id : int
     title : str
     genre : str
     year : int
     plot  : str

     class Config:
          orm_mode = True

