from dataclasses import dataclass
from datetime import datetime, timezone
from fastapi import WebSocket
from shared.base_service import BaseService
from app.services.get_members_from_organisation_id import (
    get_members_from_organisation_id,
)

from app.services.get_orgs_from_user_id import get_orgs_from_user_id


@dataclass
class User:
    websockets: list[WebSocket]
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
        if user_id in self._users:
            self._users[user_id].websockets.append(websocket)
        else:
            self._users[user_id] = User(
                websockets=[websocket],
                connected_at=datetime.now(timezone.utc),
                first_name=first_name,
                last_name=last_name,
            )

    async def get_connected_friends(self, user_id):
        orgs = await get_orgs_from_user_id(user_id)
        friends = {}
        for org in orgs["organisation"]:
            org_members = await get_members_from_organisation_id(org["org_id"])
            for member in org_members:
                if member["user_id"] in self._users:
                    friends[member["user_id"]] = member
        return list(friends.values())

    def get_name_from_id(self, user_id: int):
        response = self._users.get(user_id, None)
        if not response:
            return None
        return {
            "first_name": response.first_name,
            "last_name": response.last_name,
        }

    def disconnect(self, user_id: int, websocket: WebSocket):
        user = self._users.get(user_id)
        if user is None:
            return
        if websocket in user.websockets:
            user.websockets.remove(websocket)
        if not user.websockets:
            del self._users[user_id]

    async def broadcast_id(self, message: dict, user_id):
        dead: list[tuple[WebSocket, int]] = []
        if user_id in self._users:
            for websocket in self._users[user_id].websockets:
                try:
                    await websocket.send_json(message)
                except Exception:
                    dead.append(
                        (
                            websocket,
                            user_id,
                        )
                    )
                    self._logger.warning("dropping dead socket", exc_info=True)
            for to_disconnect in dead:
                websocket, user_id = to_disconnect
                self.disconnect(user_id, websocket)


manager = ConnectionManager()
