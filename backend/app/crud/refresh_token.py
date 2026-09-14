from datetime import datetime
from app.models.refresh_token import RefreshToken
from sqlalchemy.orm import Session


def add_refresh_token_db(user_id : int , hashed_token : str , expires_at : datetime , db : Session) -> RefreshToken:

    db_token = RefreshToken(
            user_id=user_id,
            token=hashed_token,
            expires_at=expires_at
        )
   
    
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    
    return db_token

def get_token_db(hashed_token : str , db : Session):

    return db.query(RefreshToken).filter(RefreshToken.token == hashed_token).first()

def revoke_alltoken_by_id(user_id : int , db : Session):

    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id
    ).update({"revoked": True})
    db.commit()

def revoke_token_by_id(user_id : int , db : Session):
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked == False
    ).update({"revoked": True})

    db.commit()

   

def revoke_all_token(db_token : RefreshToken , db : Session):
    db.query(RefreshToken).filter(
            RefreshToken.user_id == db_token.user_id
        ).update({"revoked": True})
    
    db.commit()
        