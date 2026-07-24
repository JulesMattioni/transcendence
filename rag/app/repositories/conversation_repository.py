from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.conversation import Conversation
from app.models.message import Message


class ConversationRepository:
    """
    Data-access layer for Conversation and Message. Talks SQL only.

    It receives an AsyncSession and never creates one itself: the caller
    (the service) owns the session and the transaction boundary.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize the repository with its database session.

        Args:
            session: Async SQLAlchemy session used for all queries.
        """

        self._session = session

    async def create_conversation(
        self, conversation: Conversation
    ) -> Conversation:
        """
        Persist a new conversation.

        Args:
            conversation: Conversation ORM object to persist.

        Returns:
            The same Conversation, refreshed with its generated id.
        """

        self._session.add(conversation)
        await self._session.flush()
        await self._session.refresh(conversation)
        return conversation

    async def get_conversation(
        self, conversation_id: int
    ) -> Conversation | None:
        """
        Fetch a conversation by its id.

        Args:
            conversation_id: Id of the requested conversation.

        Returns:
            The matching Conversation, or None if it does not exist.
        """

        return await self._session.get(Conversation, conversation_id)

    async def list_conversations(
        self, organisation_id: int, user_id: int
    ) -> list[Conversation]:
        """
        List a user's conversations in an organisation, newest first.

        Args:
            organisation_id: Organisation the conversations belong to.
            user_id: Owner whose conversations are listed.

        Returns:
            The user's conversations, newest first.
        """

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
        """
        List a conversation's messages in chronological order.

        Args:
            conversation_id: Conversation whose messages are listed.

        Returns:
            The conversation's messages, oldest first.
        """

        command = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc(), Message.id.asc())
        )
        result = await self._session.execute(command)
        return list(result.scalars().all())

    async def add_message(self, message: Message) -> Message:
        """
        Persist a new message in a conversation.

        Args:
            message: Message ORM object to persist.

        Returns:
            The same Message, refreshed with its generated id.
        """

        self._session.add(message)
        await self._session.flush()
        await self._session.refresh(message)
        return message

    async def delete_conversation(self, conversation: Conversation) -> None:
        """
        Delete a conversation; its messages cascade in the database.

        Args:
            conversation: Conversation ORM object to delete.
        """

        await self._session.delete(conversation)
        await self._session.flush()
