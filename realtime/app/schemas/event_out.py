"""Outbound event schema broadcast to the connected clients."""

from datetime import datetime
from app.schemas.event_in import EventIn


class EventOut(EventIn):
    """Fully-resolved event pushed to the audit WebSocket clients.

    Built from an :class:`EventIn` by the dispatcher, it promotes the
    optional inbound identity fields into required ones and adds the
    metadata generated server-side (a unique id and a timestamp) plus the
    organisation name resolved from ``org_id``.

    Attributes:
        event_id: Unique identifier of the event (UUID4 string).
        timestamp: UTC instant at which the event was built.
        user_id: Identifier of the user the event is about (required).
        first_name: User's first name (required).
        last_name: User's last name (required).
        org_name: Human-readable organisation name, resolved for file
            events; ``None`` for auth events.
    """

    event_id: str
    timestamp: datetime
    user_id: int
    first_name: str
    last_name: str
    org_name: str | None = None
