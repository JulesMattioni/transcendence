from fastapi import APIRouter
from app.services.connection_manager import manager
from fastapi import HTTPException

router = APIRouter()


@router.get("/connected_friends", status_code=200)
async def get_connected_member(user_id: int) -> list[dict]:
    try:
        friends = await manager.get_connected_friends(user_id)

    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"An error occured {e}",
        )
    return friends
