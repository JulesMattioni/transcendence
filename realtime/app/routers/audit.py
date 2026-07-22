from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.connection_manager import manager
from app.services.get_current_user import get_current_user
from app.services.event_dispatcher import dispatcher
from fastapi import HTTPException

router = APIRouter()


def mock_org():
    return {
        "user_id": 42,
        "organisations": [
            {"org_id": 1, "name": "Belle Organisation", "role": "admin"},
            {"org_id": 2, "name": "Magnifique Organisation", "role": "reader"},
        ],
    }


@router.websocket("/audit")
async def audit(websocket: WebSocket, token: str) -> None:
    try:
        user = await get_current_user(token)
    except HTTPException:
        await websocket.close(code=1008)
        return
    try:
        user_org = mock_org()  # mock
    except HTTPException:
        await websocket.close(code=1008)
        return
    await manager.connect(
        websocket,
        user["id"],
        user_org["organisations"],
        user["first_name"],
        user["last_name"],
    )

    # await dispatcher.add_client(user["id"])
    try:
        while True:
            message = await websocket.receive_text()
            await websocket.send_text(message)
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(user["id"])
