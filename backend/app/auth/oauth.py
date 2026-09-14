from fastapi import HTTPException , status , Depends 
from app.schemas.login import DataToken
from jose import jwt , JWTError
from datetime import datetime , timezone , timedelta
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.crud.user import get_user_by_id
from app.services.token_blacklist import token_blacklist
TOKEN_EXPIRE_TIME = 50

from app.config import setting
oath2_schema = OAuth2PasswordBearer(tokenUrl="/login")
ALGORITHM = "HS256"

def create_access_token(data : dict):
     
     expire_time = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_TIME)

     user_id = str(data['user_id'])

     to_encode = {
         "sub": user_id, 
         "exp": expire_time,
        } 

     jwt_encode = jwt.encode(to_encode , setting.JWT_SECRET_TOKEN, ALGORITHM)

     return jwt_encode

def verify_access_token(token : str , credentials_exception):
    try:
        payload =  jwt.decode(token , setting.JWT_SECRET_TOKEN , ALGORITHM)

        user_id = payload.get("sub")

        if not id:
            raise credentials_exception
        data_token = DataToken(id=int(user_id))

    except JWTError as e:
        print(e)
        raise credentials_exception
    return data_token 

def get_current_user(token : str = Depends(oath2_schema), db : Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not Validate Credentials",headers={"WWW-Authenticate": "Bearer"})


    # if token_blacklist.is_blacklisted(token):
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Token has been revoked"
    #     )

    token = verify_access_token(token , credentials_exception)

    user = get_user_by_id(token.id , db)

    return user