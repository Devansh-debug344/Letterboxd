from sqlalchemy.orm import Session
from app.models.auth_event import AuthEvent
from datetime import datetime, timezone
from app.schemas.auth_event import AuthEventSchema
from app.crud.auth_event import add_auth_event_db
class AuditService:
    @staticmethod
    def log_event(auth_event : AuthEventSchema , db : Session):
        """
        Log an auth event
        
        Args:
            event_type: "login", "logout", "failed_login", "refresh", "logout_all"
            status: "success" or "failed"
            user_id: User ID (can be None for signup attempts)
            reason: Why it failed (if status is failed)
            ip_address: Client IP
            user_agent: Browser/client info
        """


        add_auth_event_db(auth_event , db)

