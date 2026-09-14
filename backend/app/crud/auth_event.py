from sqlalchemy.orm import Session
from app.schemas.auth_event import AuthEventSchema
from app.models.auth_event import AuthEvent
def add_auth_event_db(auth_event :  AuthEventSchema , db :  Session):

    event = AuthEvent(
                user_id=auth_event.user_id,
                event_type=auth_event.event_type,
                status=auth_event.status,
                reason=auth_event.reason,
                ip_address=auth_event.ip_address,
                user_agent=auth_event.user_agent
    )     
    db.add(event)
    db.commit()
