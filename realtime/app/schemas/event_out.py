from datetime import datetime
from app.schemas.event_in import EventIn


class EventOut(EventIn):
    event_id: str
    timestamp: datetime
    user_id: int
    first_name: str
    last_name: str
    org_name: str | None = None
