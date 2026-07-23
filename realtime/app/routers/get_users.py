"""Router exposing the currently-connected friends of a user."""

from fastapi import APIRouter
from app.services.connection_manager import manager
from fastapi import HTTPException

router = APIRouter()


@router.get("/connected_friends", status_code=200)
async def get_connected_member(user_id: int) -> list[dict]:
    """Return the online organisation members related to ``user_id``.

    Args:
        user_id: Identifier of the user whose online peers are wanted.

    Returns:
        Member records (as returned by the ``org`` service) for the peers
        currently connected.

    Raises:
        HTTPException: Re-raised as-is on upstream failure; any other
            error is wrapped into a ``422``.
    """
    try:
        friends = await manager.get_connected_friends(user_id)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"An error occured {e}",
        )
    return friends
