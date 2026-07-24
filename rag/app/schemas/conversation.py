from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.query import Source


class ConversationCreate(BaseModel):
    """
    Metadata sent by the client when creating a conversation.

    user_id comes from the authenticated user, not from the body.
    """

    organisation_id: int
    title: str = Field(min_length=1, max_length=255)


class MessageRead(BaseModel):
    """
    A single message as returned to the client.

    Reads its values directly from the ORM object (from_attributes).
    sources is the list of cited document excerpts for an assistant
    message, or None for a user message.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    sources: list[Source] | None
    created_at: datetime


class ConversationRead(BaseModel):
    """
    A conversation's metadata as returned to the client.

    Reads its values directly from the ORM object (from_attributes) and
    excludes the messages so lists stay lightweight.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    organisation_id: int
    user_id: int
    title: str
    created_at: datetime


class ConversationDetail(ConversationRead):
    """
    A conversation's metadata together with its full message history.

    Returned when a single conversation is opened, so the client can
    render the whole exchange.
    """

    messages: list[MessageRead]
