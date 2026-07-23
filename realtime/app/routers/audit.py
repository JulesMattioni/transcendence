from fastapi import APIRouter, WebSocket
from app.services.connection_manager import manager
from app.services.get_current_user import get_current_user
from app.services.event_dispatcher import dispatcher

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
        while True:
            message = await websocket.receive_text()
            await websocket.send_text(message)
    except Exception as e:
        logger.warning(e)
    finally:
        manager.disconnect(user["id"])
