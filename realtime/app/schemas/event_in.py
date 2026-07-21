from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.event_type import EventType


class EventIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_type: EventType
    user_id: int | None = None
    file_id: str | None = None
