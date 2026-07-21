from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.connection_manager import manager
import httpx
from fastapi import Header, HTTPException

router = APIRouter()


async def get_current_user(token: str):
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        try:
            response = await client.get(
                "http://auth:8000/me",
                headers={"Authorization": f"Bearer {token}"},
            )
        except httpx.HTTPError:
            raise HTTPException(
                status_code=503, detail="Auth service unavailable"
            )

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid token")
    return response


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
