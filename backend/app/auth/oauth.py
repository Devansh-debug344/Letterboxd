from fastapi import HTTPException , status , Depends 
from app.schemas.login import DataToken
from jose import jwt , JWTError
from datetime import datetime , timezone , timedelta
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
TOKEN_EXPIRE_TIME = 500

from app.config import setting
oath2_schema = OAuth2PasswordBearer(tokenUrl="/login")
ALGORITHM = "HS256"

def create_access_token(data : dict):
     to_encode = data.copy()
     expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_TIME)
     to_encode.update({"exp" : expire})

     jwt_encode = jwt.encode(to_encode , setting.SECRET_KEY, ALGORITHM)

     return jwt_encode

def verify_access_token(token : str , credentials_exception):
    try:
        payload =  jwt.decode(token , setting.SECRET_KEY , ALGORITHM)

        id : str = payload["user_id"]

        if not id:
            raise credentials_exception
        data_token = DataToken(id=id)

    except JWTError as e:
        print(e)
        raise credentials_exception
    return data_token 

def get_current_user(token : str = Depends(oath2_schema), db : Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not Validate Credentials",headers={"WWW-Authenticate": "Bearer"})

    token = verify_access_token(token , credentials_exception)

    user = db.query(User).filter(User.id == token.id).first()

    return user