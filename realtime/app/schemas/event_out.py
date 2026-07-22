from datetime import datetime, timezone
from uuid import uuid4
from app.schemas.event_in import EventIn


class EventOut(EventIn):
    event_id: str
    timestamp: datetime
    user_id: int | None
    first_name: str | None
    last_name: str | None

