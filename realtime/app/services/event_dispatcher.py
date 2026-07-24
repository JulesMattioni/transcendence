"""Event dispatcher: resolves recipients and broadcasts events."""

from app.services.connection_manager import manager
from app.schemas.event_out import EventOut, EventIn
from app.schemas.event_type import EventType
from datetime import timezone, datetime
from app.schemas.roles import Role
from uuid import uuid4
import httpx
from fastapi import HTTPException
from app.services.get_members_from_organisation_id import (
    get_members_from_organisation_id,
)

from app.services.get_orgs_from_user_id import get_orgs_from_user_id


class Dispatcher:
    """Turn an inbound event into an outbound one and route it.

    Heart of the fan-out logic: it validates and enriches a raw
    :class:`EventIn` into a fully-formed :class:`EventOut`, works out who
    should receive it, and pushes it through the shared connection
    :data:`manager`. Routing rules:

    - auth events (login/logout) reach the *admins* of every organisation
      the user belongs to;
    - file events reach *all* members of the file's organisation.
    """

    async def get_org_name_from_org_id(self, org_id: int) -> dict:
        """Fetch an organisation's details from the ``org`` service.

        Args:
            org_id: Identifier of the organisation to resolve.

        Returns:
            The decoded JSON describing the organisation (incl. ``name``).

        Raises:
            HTTPException: ``503`` if ``org`` is unreachable, otherwise
                the upstream status code.
        """
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            try:
                response = await client.get(
                    f"http://org:8000/organisations/{org_id}"
                )
            except httpx.HTTPError:
                raise HTTPException(
                    status_code=503, detail="Org service unavailable"
                )
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error getting organisation name from org_id {org_id}",
            )
        return response.json()

    async def send_event_to_admins_of_org(
        self,
        org_id: int,
        event: EventOut,
        excluded: list[int],
    ) -> list:
        """Broadcast an event to the admins of one organisation.

        Args:
            org_id: Organisation whose admins should be notified.
            event: The event to deliver.
        """
        members = [
            member["user_id"]
            for member in await get_members_from_organisation_id(org_id)
            if member["role_id"] == Role.ADMIN
            and member["user_id"] not in excluded
        ]
        for member in members:
            await manager.broadcast_id(event.model_dump(mode="json"), member)
        return members

    async def send_event_to_all_org(self, org_id: int, event: EventOut):
        """Broadcast an event to every member of one organisation.

        Args:
            org_id: Organisation whose members should be notified.
            event: The event to deliver.
        """
        members = [
            member["user_id"]
            for member in await get_members_from_organisation_id(org_id)
        ]
        for member in members:
            await manager.broadcast_id(event.model_dump(mode="json"), member)

    async def send_auth_event_to_concerned(self, event: EventOut):
        """Route an auth event to the admins of the user's organisations.

        Args:
            event: The resolved auth event to deliver.
        """
        organisations = await get_orgs_from_user_id(event.user_id)
        excluded = []
        for organisation in organisations["organisation"]:
            who_received = await self.send_event_to_admins_of_org(
                organisation["org_id"], event, excluded
            )
            excluded += who_received

    async def send_file_event_to_concerned(self, event: EventOut):
        """Route a file event to all members of its organisation.

        Args:
            event: The resolved file event to deliver.

        Raises:
            HTTPException: ``422`` if the event carries no ``org_id``.
        """
        if event.org_id is None:
            raise HTTPException(status_code=422, detail="org_id is required")
        await self.send_event_to_all_org(event.org_id, event)

    async def build_event_out(self, event: EventIn):
        """Validate and enrich an inbound event into an outbound one.

        Applies the per-type requirements that :class:`EventIn` cannot
        express on its own, generates the event id and timestamp, and
        resolves the extra data each type needs (user name for file
        events, organisation name).

        Args:
            event: The raw inbound event to process.

        Returns:
            A fully-populated :class:`EventOut`.

        Raises:
            HTTPException: ``422`` for an unknown type or a missing
                required field; ``404`` if a file event references an
                unknown/offline user.
        """
        if event.event_type not in (
            EventType.AUTH_LOGIN,
            EventType.AUTH_LOGOUT,
            EventType.FILE_CREATED,
            EventType.FILE_UPDATED,
            EventType.FILE_DELETED,
        ):
            raise HTTPException(status_code=422, detail="unknow event")
        if event.user_id is None:
            raise HTTPException(status_code=422, detail="user_id is required")
        if event.event_type in (EventType.AUTH_LOGIN, EventType.AUTH_LOGOUT):
            if event.first_name is None or event.last_name is None:
                raise HTTPException(
                    status_code=422,
                    detail="first_name and last_name are required",
                )
            return EventOut(
                event_id=str(uuid4()),
                timestamp=datetime.now(timezone.utc),
                event_type=event.event_type,
                first_name=event.first_name,
                last_name=event.last_name,
                user_id=event.user_id,
                org_name=None,
                file_name=None,
            )
        elif event.event_type in (
            EventType.FILE_CREATED,
            EventType.FILE_UPDATED,
            EventType.FILE_DELETED,
        ):
            user = manager.get_name_from_id(event.user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            if event.org_id is None or not event.file_name:
                raise HTTPException(
                    status_code=422,
                    detail="Organisation id or file name not provided",
                )

            responses = await self.get_org_name_from_org_id(event.org_id)
            org_name = responses["name"]
            return EventOut(
                event_id=str(uuid4()),
                timestamp=datetime.now(timezone.utc),
                event_type=event.event_type,
                file_name=event.file_name,
                org_name=org_name,
                org_id=event.org_id,
                first_name=user["first_name"],
                last_name=user["last_name"],
                user_id=event.user_id,
            )
        raise HTTPException(status_code=422, detail="Unprocessable event")

    async def publish_event(self, event_in: EventIn):
        """Build an outbound event and dispatch it to its recipients.

        Single public entry point used by the ingestion endpoint;
        delegates recipient resolution to the per-type
        ``send_*_to_concerned`` helpers.

        Args:
            event_in: The raw inbound event to publish.
        """
        event_out = await self.build_event_out(event_in)
        if event_out.event_type in (
            EventType.AUTH_LOGIN,
            EventType.AUTH_LOGOUT,
        ):
            await self.send_auth_event_to_concerned(event_out)
        elif event_out.event_type in (
            EventType.FILE_CREATED,
            EventType.FILE_UPDATED,
            EventType.FILE_DELETED,
        ):
            await self.send_file_event_to_concerned(event_out)


dispatcher = Dispatcher()
