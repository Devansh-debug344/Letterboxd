from app.db.base import Base
from sqlalchemy import Column , String , Integer, DateTime , Float , ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime , timezone
from sqlalchemy.orm import relationship

class Review(Base):

    __tablename__ = "reviews"

    id = Column(Integer , primary_key=True , index=True)
    movie_id = Column(Integer , ForeignKey("movies.id"))
    user_id = Column(Integer , ForeignKey("users.id"))
    review = Column(String , nullable=False)
    likes = Column(Integer , default=0)
    updated_at = Column(DateTime , default=datetime.now(timezone.utc))

    user = relationship('User' , back_populates = 'review')
    movie = relationship('Movie' , back_populates = 'review_by')