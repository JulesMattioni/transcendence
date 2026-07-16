from datetime import datetime, timezone
from uuid import uuid4
from app.schemas.event_in import EventIn


class EventOut(EventIn):
    event_id: str
    timestamp: datetime

    @classmethod
    def from_event_in(cls, event: EventIn) -> "EventOut":
        return EventOut(
            event_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc),
            event_type=event.event_type,
            actor_id=event.actor_id,
            target=event.target,
            payload=event.payload,
        )