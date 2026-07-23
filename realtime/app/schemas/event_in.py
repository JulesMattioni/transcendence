"""Inbound event schema for the internal ingestion endpoint."""

from pydantic import BaseModel, ConfigDict

from app.schemas.event_type import EventType


class EventIn(BaseModel):
    """Raw event received on ``POST /internal/events``.

    Only ``event_type`` is always required; which of the other fields
    matter depends on the type, so they stay optional here and are
    validated by
    :meth:`app.services.event_dispatcher.Dispatcher.build_event_out`.
    ``extra="forbid"`` rejects any undeclared field.
    """

    model_config = ConfigDict(extra="forbid")
    event_type: EventType
    user_id: int | None = None
    first_name: str | None = None
    last_name: str | None = None
    org_id: int | None = None
    file_name: str | None = None
