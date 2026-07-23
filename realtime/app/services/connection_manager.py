from dataclasses import dataclass
from datetime import datetime, timezone
from fastapi import WebSocket
from shared.base_service import BaseService


@dataclass
class User:
    websocket: WebSocket
    connected_at: datetime
    first_name: str
    last_name: str


class ConnectionManager(BaseService):
    def __init__(self) -> None:
        super().__init__()
        self._users: dict[int, User] = {}

    async def connect(
        self,
        websocket: WebSocket,
        user_id: int,
        first_name,
        last_name,
    ):
        await websocket.accept()
        self._users[user_id] = User(
            websocket=websocket,
            connected_at=datetime.now(timezone.utc),
            first_name=first_name,
            last_name=last_name,
        )

    def get_name_from_id(self, user_id: int):
        response = self._users.get(user_id, None)
        if not response:
            return None
        return {
            "first_name": response.first_name,
            "last_name": response.last_name,
        }

    def disconnect(self, user_id: int):
        self._users.pop(user_id, None)

    async def broadcast_id(self, message: dict, user_id):
        if user_id in self._users:
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
