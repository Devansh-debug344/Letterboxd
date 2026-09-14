from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from app.db.base import Base

class AuthEvent(Base):
    __tablename__ = "auth_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    event_type = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False)
    reason = Column(String, nullable=True, default=None)  
    ip_address = Column(String, nullable=True, default=None) 
    user_agent = Column(String, nullable=True, default=None)  
    created_at = Column(DateTime, default=datetime.now(timezone.utc), index=True)
    
    user = relationship("User", foreign_keys=[user_id])