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
    """
    Service handling conversation and message lifecycle.

    Coordinates the repository (database) and owns the transaction
    boundary: it is the only layer that commits or rolls back the
    session. Every read and write is scoped to the conversation's owner.
    """

    def __init__(
        self,
        session: AsyncSession,
        repository: ConversationRepository,
    ) -> None:
        """
        Initialize the service with its collaborators.

        Args:
            session: Async SQLAlchemy session used for transactions.
            repository: Repository for conversation and message
            persistence.
        """

        super().__init__()
        self._session = session
        self._repository = repository

    async def _get_owned(
        self, conversation_id: int, organisation_id: int, user_id: int
    ) -> Conversation:
        """
        Return the conversation if it belongs to the given user and org.

        A conversation from another user or organisation is
        indistinguishable from a missing one, so its existence is never
        leaked.

        Args:
            conversation_id: Id of the requested conversation.
            organisation_id: Organisation the conversation must belong to.
            user_id: User the conversation must belong to.

        Returns:
            The matching Conversation ORM object.

        Raises:
            ConversationNotFoundError: If it does not exist or belongs to
            another user or organisation.
        """

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
        """
        Create an empty conversation for a user.

        The title is truncated to CONV_TITLE_MAX_LEN.

        Args:
            data: Client-provided title and organisation_id.
            user_id: Id of the authenticated user owning the conversation.

        Returns:
            ConversationRead with the created conversation's metadata.
        """

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
        """
        List a user's conversations in an organisation, newest first.

        Args:
            organisation_id: Organisation whose conversations are listed.
            user_id: Owner whose conversations are listed.

        Returns:
            The user's conversations as ConversationRead, newest first.
        """

        conversations = await self._repository.list_conversations(
            organisation_id, user_id
        )
        return [ConversationRead.model_validate(c) for c in conversations]

    async def get_detail(
        self, conversation_id: int, organisation_id: int, user_id: int
    ) -> ConversationDetail:
        """
        Return a conversation with its full message history.

        Args:
            conversation_id: Id of the requested conversation.
            organisation_id: Organisation the conversation must belong to.
            user_id: User the conversation must belong to.

        Returns:
            ConversationDetail with the metadata and ordered messages.

        Raises:
            ConversationNotFoundError: If it does not exist for this user
            and organisation.
        """

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
        """
        Delete a conversation and, by cascade, its messages.

        Args:
            conversation_id: Id of the conversation to delete.
            organisation_id: Organisation the conversation must belong to.
            user_id: User the conversation must belong to.

        Raises:
            ConversationNotFoundError: If it does not exist for this user
            and organisation.
        """

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
        """
        Return the referenced conversation, or start a new one.

        Used by the streaming query endpoint so a question can either
        continue an existing conversation or open one titled after the
        first question (truncated to CONV_TITLE_MAX_LEN).

        Args:
            conversation_id: Existing conversation to continue, or None to
            create one.
            organisation_id: Organisation the conversation belongs to.
            user_id: User the conversation belongs to.
            first_question: Question used as the title of a new
            conversation.

        Returns:
            The existing or newly created Conversation.

        Raises:
            ConversationNotFoundError: If conversation_id is given but does
            not exist for this user and organisation.
        """

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
        """
        Append a message to a conversation and commit it.

        Args:
            conversation_id: Conversation the message belongs to.
            role: Author of the message, "user" or "assistant".
            content: Text content of the message.
            sources: Cited document sources for an assistant message, or
            None.
        """

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
