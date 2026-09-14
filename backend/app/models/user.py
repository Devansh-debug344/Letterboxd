from app.db.base import Base
from sqlalchemy import Column , String , Integer , DateTime
from datetime import datetime , timezone
from sqlalchemy.orm import relationship
class User(Base):
    __tablename__ = "users"

    id = Column(Integer , primary_key=True , index= True)
    username = Column(String , unique=True , nullable= False)
    email = Column(String , unique=True , nullable = False)
    password = Column(String , nullable=False)
    joined_at = Column(DateTime , default = datetime.now(timezone.utc))

    watchlists = relationship("WatchList", back_populates="user", cascade="all,delete-orphan")
     
    review = relationship('Review' , back_populates='user', cascade="all,delete-orphan")

    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all,delete-orphan")

    watched_items = relationship('Watched' , back_populates='user' , cascade="all,delete-orphan")


    # cascade="all, delete-orphan"

    # Delete Parent: When you delete a parent object via the ORM (session.delete(parent)), SQLAlchemy will look up all loaded children in memory and emit separate DELETE SQL statements for every single one of them.
    # The "Orphan" part: If you simply remove a child from a parent's collection (parent.posts.remove(old_post)), the child becomes an "orphan". The ORM will automatically delete that specific child row from the database when you commit, because it can no longer exist without its parent

    