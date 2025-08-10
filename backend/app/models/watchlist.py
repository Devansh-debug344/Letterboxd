from app.db.base import Base
from sqlalchemy import Column , String , Integer, DateTime , ForeignKey ,  Float 
from sqlalchemy.orm import relationship

# title, description, genre, release year, image URL
class WatchList(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    movie_id = Column(Integer, ForeignKey("movies.id"))
    status = Column(String , default = "unwatched")
    note = Column(String, nullable=True)
    rating = Column(Float, nullable=True)

    user = relationship('User' , back_populates = 'watchlist')
    movie = relationship('Movie' , back_populates = 'watchlisted_by')