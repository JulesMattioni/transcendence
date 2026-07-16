from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.event_target import EventTarget
from app.schemas.event_type import EventType


class EventIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_type: EventType
    actor_id: int
    target: EventTarget | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
