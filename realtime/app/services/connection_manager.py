from dataclasses import dataclass
from datetime import datetime, timezone
from fastapi import WebSocket
from shared.base_service import BaseService


@dataclass
class User:
    websocket: WebSocket
    connected_at: datetime



class ConnectionManager(BaseService):
    def __init__(self) -> None:
        super().__init__()
        self._users: dict[int, User] = {}

    async def connect(
        self,
        websocket: WebSocket,
        user_id: int,
        organisations,
        first_name,
        last_name,
    ):
        await websocket.accept()
        self._users[user_id] = User(
            websocket=websocket,
            connected_at=datetime.now(timezone.utc),
        )

    def disconnect(self, user_id: int):
        del self._users[user_id]

    async def broadcast_id(self, message: dict, user_id):
        try:
            await self._users[user_id].websocket.send_json(message)
        except Exception:
            del self._users[user_id]
            self._logger.warning("dropping dead socket", exc_info=True)

    async def broadcast_all(self, message: dict):
        dead: list[int] = []
        for user_id, user in list(self._users.items()):
            try:
                await user.websocket.send_json(message)
            except Exception:
                dead.append(user_id)
                self._logger.warning("dropping dead socket", exc_info=True)
        for user_id in dead:
            del self._users[user_id]


manager = ConnectionManager()
