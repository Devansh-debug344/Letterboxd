from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import setting

db_url = setting.db_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    db_url,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=2,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
