from datetime import datetime
from app.schemas.event_in import EventIn


class EventOut(EventIn):
    event_id: str
    timestamp: datetime
    first_name: str | None
    last_name: str | None
    org_name: str | None
