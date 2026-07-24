from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import get_session
from app.repositories.conversation_repository import ConversationRepository
from app.services.conversation_service import (
    ConversationService,
    ConversationNotFoundError,
)
from app.schemas.conversation import (
    ConversationCreate,
    ConversationRead,
    ConversationDetail,
)
from app.get_user import get_current_user_id

router = APIRouter(prefix="/conversations", tags=["conversations"])


def get_conversation_service(
    session: AsyncSession = Depends(get_session),
) -> ConversationService:
    """
    Build a ConversationService with its dependencies for one request.

    Args:
        session: Async SQLAlchemy session provided by the shared
        get_session dependency.

    Returns:
        A ConversationService wired with its repository.
    """

    repository = ConversationRepository(session)
    return ConversationService(session, repository)


@router.post(
    "", response_model=ConversationRead, status_code=status.HTTP_201_CREATED
)
async def create_conversation(
    data: ConversationCreate,
    service: ConversationService = Depends(get_conversation_service),
    user_id: int = Depends(get_current_user_id),
) -> ConversationRead:
    """
    Create an empty conversation for the authenticated user.

    Args:
        data: Title and organisation of the new conversation.
        service: Injected ConversationService instance.
        user_id: Id of the authenticated user, resolved via auth.

    Returns:
        ConversationRead with the created conversation's metadata.
    """

    return await service.create(data, user_id)


@router.get("", response_model=list[ConversationRead])
async def list_conversations(
    organisation_id: int,
    service: ConversationService = Depends(get_conversation_service),
    user_id: int = Depends(get_current_user_id),
) -> list[ConversationRead]:
    """
    List the authenticated user's conversations in an organisation.

    Args:
        organisation_id: Organisation whose conversations are listed.
        service: Injected ConversationService instance.
        user_id: Id of the authenticated user, resolved via auth.

    Returns:
        The user's conversations, newest first.
    """

    return await service.list_conversations(organisation_id, user_id)


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: int,
    organisation_id: int,
    service: ConversationService = Depends(get_conversation_service),
    user_id: int = Depends(get_current_user_id),
) -> ConversationDetail:
    """
    Return a single conversation with its full message history.

    Args:
        conversation_id: Id of the requested conversation.
        organisation_id: Organisation the conversation must belong to.
        service: Injected ConversationService instance.
        user_id: Id of the authenticated user, resolved via auth.

    Returns:
        ConversationDetail with the metadata and ordered messages.

    Raises:
        HTTPException: 404 when the conversation does not exist for this
        user and organisation.
    """

    try:
        return await service.get_detail(
            conversation_id, organisation_id, user_id
        )
    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: int,
    organisation_id: int,
    service: ConversationService = Depends(get_conversation_service),
    user_id: int = Depends(get_current_user_id),
) -> None:
    """
    Delete a conversation and its messages.

    Args:
        conversation_id: Id of the conversation to delete.
        organisation_id: Organisation the conversation must belong to.
        service: Injected ConversationService instance.
        user_id: Id of the authenticated user, resolved via auth.

    Raises:
        HTTPException: 404 when the conversation does not exist for this
        user and organisation.
    """

    try:
        await service.delete(conversation_id, organisation_id, user_id)
    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )
