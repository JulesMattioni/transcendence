from fastapi import APIRouter, WebSocket
from app.services.connection_manager import manager
from app.services.get_current_user import get_current_user
from app.services.event_dispatcher import dispatcher
from app.schemas.event_in import EventIn
from app.schemas.event_type import EventType
import logging

router = APIRouter()

logger = logging.getLogger(__name__)


@router.websocket("/audit")
async def audit(websocket: WebSocket, token: str) -> None:
    try:
        user = await get_current_user(token)
    except Exception:
        await websocket.close(code=1008)
        return
    await manager.connect(
        websocket,
        user["id"],
        user["first_name"],
        user["last_name"],
    )

    try:
        await dispatcher.publish_event(
            EventIn(event_type=EventType.AUTH_LOGIN, user_id=user["id"])
        )
    except Exception as e:
        logger.warning(e)
    try:
        while True:
            message = await websocket.receive_text()
            await websocket.send_text(message)
    except Exception as e:
        logger.warning(e)
    finally:
        try:
            await dispatcher.publish_event(
                EventIn(
                    event_type=EventType.AUTH_LOGOUT,
                    user_id=user["id"],
                    first_name=user["first_name"],
                    last_name=user["last_name"],
                )
            )
        except Exception as e:
            logger.warning(e)
        manager.disconnect(user["id"])
