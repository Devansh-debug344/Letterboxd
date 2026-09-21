from pydantic import BaseModel
from typing import Optional


class Login(BaseModel):
    username : str
    password : str

class Token(BaseModel):
    access_token : str
    token_type : str

class DataToken(BaseModel):
    id: int

class LogoutResponse(BaseModel):
    message: str