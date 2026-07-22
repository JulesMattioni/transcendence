from dataclasses import dataclass
from datetime import datetime, timezone
from fastapi import WebSocket
from shared.base_service import BaseService


@dataclass
class Connection:
    user_id: int
    connected_at: datetime


class ConnectionManager(BaseService):
    def __init__(self) -> None:
        super().__init__()
        self._connections: dict[WebSocket, Connection] = {}
        self._index: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self._connections[websocket] = Connection(
            user_id=user_id,
            connected_at=datetime.now(timezone.utc),
        )
        self._index[user_id] = WebSocket

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.pop(websocket, None)

    async def broadcast_id(self, message: dict, id):
        dead: list[WebSocket] = []
        try:
            await self._index[id].send_json(message)
        except Exception:
            dead.append(self._index[id])
            self._logger.warning("dropping dead socket", exc_info=True)
        for websocket in dead:
            self.disconnect(websocket)

    async def broadcast_all(self, message: dict):
        dead: list[WebSocket] = []
        for websocket, connection in list(self._connections.items()):
            try:
                await websocket.send_json(message)
            except Exception:
                dead.append(websocket)
                self._logger.warning("dropping dead socket", exc_info=True)
        for websocket in dead:
            self.disconnect(websocket)


manager = ConnectionManager()
