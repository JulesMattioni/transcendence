from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.conversation import Conversation
from app.models.message import Message


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_conversation(
        self, conversation: Conversation
    ) -> Conversation:
        self._session.add(conversation)
        await self._session.flush()
        await self._session.refresh(conversation)
        return conversation

    async def get_conversation(
        self, conversation_id: int
    ) -> Conversation | None:
        return await self._session.get(Conversation, conversation_id)

    async def list_conversations(
        self, organisation_id: int, user_id: int
    ) -> list[Conversation]:
        command = (
            select(Conversation)
            .where(
                Conversation.organisation_id == organisation_id,
                Conversation.user_id == user_id,
            )
            .order_by(Conversation.created_at.desc(), Conversation.id.desc())
        )
        result = await self._session.execute(command)
        return list(result.scalars().all())

    async def list_messages(self, conversation_id: int) -> list[Message]:
        command = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc(), Message.id.asc())
        )
        result = await self._session.execute(command)
        return list(result.scalars().all())

    async def add_message(self, message: Message) -> Message:
        self._session.add(message)
        await self._session.flush()
        await self._session.refresh(message)
        return message

    async def delete_conversation(self, conversation: Conversation) -> None:
        await self._session.delete(conversation)
        await self._session.flush()
