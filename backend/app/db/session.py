from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker

from app.config import setting

engine = create_engine(setting.db_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db= SessionLocal()
    try:
       yield db
    finally:
        db.close()   