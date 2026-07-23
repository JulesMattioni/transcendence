"""In-memory registry of the active WebSocket connections."""

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
    """A connected user and the WebSocket connections they hold.

    A user may be connected from several tabs/devices at once, hence a
    list of sockets rather than a single connection.

    Attributes:
        websockets: The user's currently open connections.
        connected_at: UTC time of the user's first connection.
        first_name: User's first name.
        last_name: User's last name.
    """

    websockets: list[WebSocket]
    connected_at: datetime
    first_name: str
    last_name: str


class ConnectionManager(BaseService):
    """Track live WebSocket connections and broadcast events to them.

    Single source of truth for "who is online". Connections are indexed
    by user id so an event can reach every socket a user holds. The
    registry lives in memory only and is local to a single process.

    Attributes:
        _users: Maps a user id to the :class:`User` holding their sockets.
    """

    def __init__(self) -> None:
        """Initialise an empty connection registry."""
        super().__init__()
        self._users: dict[int, User] = {}

    async def connect(
        self,
        websocket: WebSocket,
        user_id: int,
        first_name,
        last_name,
    ):
        """Accept a WebSocket and register it under ``user_id``.

        Appends the socket to the user's existing entry if any, otherwise
        creates a new :class:`User` entry.

        Args:
            websocket: The connection to accept and store.
            user_id: Identifier of the connecting user.
            first_name: User's first name.
            last_name: User's last name.
        """
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
        """Return the connected members of the user's organisations.

        Gathers the members of every organisation the user belongs to and
        keeps only those currently connected, de-duplicated across orgs.

        Args:
            user_id: Identifier of the user whose online peers are wanted.

        Returns:
            A list of member records for the connected peers.
        """
        orgs = await get_orgs_from_user_id(user_id)
        friends = {}
        for org in orgs["organisation"]:
            org_members = await get_members_from_organisation_id(org["org_id"])
            for member in org_members:
                if member["user_id"] in self._users:
                    friends[member["user_id"]] = member
        return list(friends.values())

    def get_name_from_id(self, user_id: int):
        """Return the stored name of a connected user.

        Args:
            user_id: Identifier of the user to look up.

        Returns:
            ``{"first_name": ..., "last_name": ...}`` if the user is
            connected, otherwise ``None``.
        """
        response = self._users.get(user_id, None)
        if not response:
            return None
        return {
            "first_name": response.first_name,
            "last_name": response.last_name,
        }

    def disconnect(self, user_id: int, websocket: WebSocket):
        """Remove one socket, forgetting the user once it was their last.

        Args:
            user_id: Identifier of the user owning the socket.
            websocket: The connection to remove.
        """
        user = self._users.get(user_id)
        if user is None:
            return
        if websocket in user.websockets:
            user.websockets.remove(websocket)
        if not user.websockets:
            del self._users[user_id]

    async def broadcast_id(self, message: dict, user_id):
        """Send a JSON message to every socket held by a user.

        Sockets that raise while sending are treated as dead and pruned
        once the broadcast completes.

        Args:
            message: JSON-serialisable payload to deliver.
            user_id: Identifier of the recipient user.
        """
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
