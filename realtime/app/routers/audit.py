"""WebSocket router streaming audit events to authenticated clients."""

from fastapi import APIRouter, WebSocket
from app.services.connection_manager import manager
from app.services.get_current_user import get_current_user


import logging

router = APIRouter()

logger = logging.getLogger(__name__)


@router.websocket("/audit")
async def audit(websocket: WebSocket, token: str) -> None:
    """Authenticate a client and keep its audit WebSocket open.

    The ``token`` is validated against the ``auth`` service; on failure
    the socket is closed with code ``1008``. On success the connection is
    registered with the shared :data:`manager` so the dispatcher can push
    events to it, then the handler loops echoing received text back as a
    keep-alive. The connection is always unregistered when the loop ends.

    Args:
        websocket: The incoming WebSocket connection.
        token: Bearer token passed as a query parameter.
    """
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
        manager.disconnect(user["id"], websocket)
