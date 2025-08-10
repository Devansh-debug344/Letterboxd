from app.db.base import Base
from sqlalchemy import Column , String , Integer , DateTime
from datetime import datetime , timezone
from sqlalchemy.orm import relationship
class User(Base):
    __tablename__ = "users"

    id = Column(Integer , primary_key=True , index= True)
    username = Column(String , unique=True , nullable= False)
    email = Column(String , unique=True , nullable = False)
    password = Column(String , unique=True , nullable=False)
    joined_at = Column(DateTime , default = datetime.now(timezone.utc))

    watchlist = relationship("WatchList", back_populates="user", cascade="all,delete-orphan")
     
    review = relationship('Review' , back_populates='user', cascade="all,delete-orphan")
