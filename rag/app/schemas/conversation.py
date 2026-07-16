from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.query import Source


class ConversationCreate(BaseModel):
    organisation_id: int
    title: str = Field(min_length=1, max_length=255)


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    sources: list[Source] | None
    created_at: datetime


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organisation_id: int
    user_id: int
    title: str
    created_at: datetime


class ConversationDetail(ConversationRead):
    messages: list[MessageRead]
