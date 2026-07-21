from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.connection_manager import manager

router = APIRouter()


@router.websocket("/audit")
async def audit(websocket: WebSocket, token: str) -> None:
    #demander user id a kevin 
    await manager.connect(websocket, user_id=0)
    try:
        while True:
            message = await websocket.receive_text()
            await websocket.send_text(message)
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)
# ajouter une route pour avoir la liste des user connecte