from datetime import datetime, timezone, timedelta
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.utils import generate_refresh_token, hash_token
from app.config import setting
from app.auth.oauth import create_access_token
from sqlalchemy.orm import Session
from app.crud.refresh_token import add_refresh_token_db , get_token_db , revoke_all_token

def create_refresh_token(user_id : int , db : Session)->tuple[str  , RefreshToken]:

    plain_token =  generate_refresh_token()
    hashed_token = hash_token(plain_token)

    expires_at = datetime.now(timezone.utc) + timedelta(days=setting.REFRESH_TOKEN_EXPIRE_DAYS)

    db_token = add_refresh_token_db(user_id , hashed_token , expires_at , db)

    if not db_token:
        return "Error in adding refresh token to db"

    return plain_token , db_token

def verify_refresh_token(token : str, db : Session) -> dict:

    hashed_token = hash_token(token)

    db_token = get_token_db(hashed_token , db)

    if not db_token:
        return {"valid": False, "error": "Token not found"}

    if db_token.rotated_at is not None:

        revoke_all_token(db_token , db)
        return {"valid": False, "error": "Token reuse detected. All tokens revoked. Please login again."}

    if db_token.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        return {"valid": False, "error": "Token expired"}

    if db_token.revoked:
        return {"valid": False, "error": "Token revoked"}
    
    return {"valid": True, "user_id": db_token.user_id}   

def rotate_refresh_token(old_token : str , db : Session) -> tuple[str , str , int]:

    result = verify_refresh_token(old_token , db)

    if not result["valid"]:
        raise ValueError(result["error"])

    user_id = result["user_id"]
    hashed_old_token = hash_token(old_token)

    old_db_token = get_token_db(hashed_old_token , db)

    old_db_token.rotated_at = datetime.now(timezone.utc)

    new_refresh_token , _ = create_refresh_token(user_id , db)

    new_access_token = create_access_token({"user_id" : user_id})

    db.commit()

    return new_access_token , new_refresh_token , user_id