from pydantic import BaseModel


class AuthEventSchema(BaseModel):
        event_type: str
        status: str
        user_id: int | None = None
        reason: str | None = None
        ip_address: str | None = None
        user_agent: str | None= None