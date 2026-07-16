from sqlalchemy.ext.asyncio import AsyncSession
from shared.base_service import BaseService
from app.repositories.conversation_repository import ConversationRepository
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.conversation import (
    ConversationCreate,
    ConversationRead,
    ConversationDetail,
    MessageRead,
)
from app.config import CONV_TITLE_MAX_LEN


class ConversationNotFoundError(Exception):
    """Conversation not found."""


class ConversationService(BaseService):
    def __init__(
        self,
        session: AsyncSession,
        repository: ConversationRepository,
    ) -> None:
        super().__init__()
        self._session = session
        self._repository = repository

    async def _get_owned(
        self, conversation_id: int, organisation_id: int, user_id: int
    ) -> Conversation:
        conversation = await self._repository.get_conversation(conversation_id)
        if (
            conversation is None
            or conversation.organisation_id != organisation_id
            or conversation.user_id != user_id
        ):
            raise ConversationNotFoundError(
                f"conversation {conversation_id} does not exist"
            )
        return conversation

    async def create(
        self, data: ConversationCreate, user_id: int
    ) -> ConversationRead:
        conversation = Conversation(
            organisation_id=data.organisation_id,
            user_id=user_id,
            title=data.title[:CONV_TITLE_MAX_LEN],
        )
        try:
            await self._repository.create_conversation(conversation)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
        return ConversationRead.model_validate(conversation)

    async def list_conversations(
        self, organisation_id: int, user_id: int
    ) -> list[ConversationRead]:
        conversations = await self._repository.list_conversations(
            organisation_id, user_id
        )
        return [ConversationRead.model_validate(c) for c in conversations]

    async def get_detail(
        self, conversation_id: int, organisation_id: int, user_id: int
    ) -> ConversationDetail:
        conversation = await self._get_owned(
            conversation_id, organisation_id, user_id
        )
        messages = await self._repository.list_messages(conversation_id)
        return ConversationDetail(
            id=conversation.id,
            organisation_id=conversation.organisation_id,
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at,
            messages=[MessageRead.model_validate(m) for m in messages],
        )

    async def delete(
        self, conversation_id: int, organisation_id: int, user_id: int
    ) -> None:
        conversation = await self._get_owned(
            conversation_id, organisation_id, user_id
        )
        try:
            await self._repository.delete_conversation(conversation)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    async def get_or_create(
        self,
        conversation_id: int | None,
        organisation_id: int,
        user_id: int,
        first_question: str,
    ) -> Conversation:
        if conversation_id is not None:
            return await self._get_owned(
                conversation_id, organisation_id, user_id
            )

        conversation = Conversation(
            organisation_id=organisation_id,
            user_id=user_id,
            title=first_question[: CONV_TITLE_MAX_LEN],
        )
        await self._repository.create_conversation(conversation)
        await self._session.commit()
        return conversation

    async def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        sources: list | None = None,
    ) -> None:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources=sources,
        )
        try:
            await self._repository.add_message(message)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
