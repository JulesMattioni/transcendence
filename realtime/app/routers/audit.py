from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.connection_manager import manager
from app.services.get_current_user import get_current_user
import httpx
from fastapi import HTTPException

router = APIRouter()


@router.websocket("/audit")
async def audit(websocket: WebSocket, token: str) -> None:
    try:
        user = await get_current_user(token)
    except HTTPException:
        await websocket.close(code=1008)
        return
    await manager.connect(websocket, user.id)
    try:
        while True:
            message = await websocket.receive_text()
            await websocket.send_text(message)
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)
