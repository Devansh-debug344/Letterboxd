from app.db.base import Base
from datetime import datetime , timezone
from sqlalchemy import Column , String , Integer, DateTime , ForeignKey ,  Float 
from sqlalchemy.orm import relationship

# title, description, genre, release year, image URL
class WatchList(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    movie_id = Column(Integer, ForeignKey("movies.id" , ondelete="CASCADE"))
    created_at = Column(DateTime(timezone=True), default= datetime.now(timezone.utc))
    

    user = relationship('User' , back_populates = 'watchlists')
    movie = relationship('Movie' , back_populates = 'watchlisted_by')