from pydantic import BaseModel 
from typing import Optional
from datetime import datetime
class CreateUser(BaseModel):
    username : str
    email : str
    password : str

class UserOut(BaseModel):
    username : str
    email : str
    password : str
    joined_at : datetime

    class Config:
        orm_mode = True
   
class UserProfile(BaseModel):
    username : str
    email : str
    joined_at : datetime

    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    username : Optional[str] = None
    email : Optional[str] = None