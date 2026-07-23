from app.services.connection_manager import manager
from app.schemas.event_out import EventOut, EventIn
from app.schemas.event_type import EventType
from datetime import timezone, datetime
from app.schemas.roles import Role
from uuid import uuid4
import httpx
from fastapi import HTTPException


class Dispatcher:

    async def get_organisation_name_from_org_id(
        self, org_id: int
    ) -> list[dict]:
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

    async def get_organisations_from_user_id(self, user_id: int) -> list[dict]:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            try:
                response = await client.get(
                    f"http://org:8000/organisations/users/"
                    f"{user_id}/organisations"
                )
            except httpx.HTTPError:
                raise HTTPException(
                    status_code=503, detail="Org service unavailable"
                )
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error getting organisation from user id {user_id}",
            )
        return response.json()

    async def get_members_from_organisation_id(self, org_id):
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            try:
                response = await client.get(
                    f"http://org:8000/internal/organisations/{org_id}/members"
                )
            except httpx.HTTPError:
                raise HTTPException(
                    status_code=503, detail="Org service unavailable"
                )
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error getting organisation from user id {org_id}",
            )
        return response.json()

    async def send_event_to_admins_of_org(self, org_id: int, event: EventOut):
        members = [
            member["user_id"]
            for member in await self.get_members_from_organisation_id(org_id)
            if member["role_id"] == Role.ADMIN
        ]
        for member in members:
            await manager.broadcast_id(event.model_dump(mode="json"), member)

    async def send_event_to_all_org(self, org_id: int, event: EventOut):
        members = [
            member["user_id"]
            for member in await self.get_members_from_organisation_id(org_id)
        ]
        for member in members:
            await manager.broadcast_id(event.model_dump(mode="json"), member)

    async def send_auth_event_to_concerned(self, event: EventOut):
        organisations = await self.get_organisations_from_user_id(
            event.user_id
        )
        for organisation in organisations["organisation"]:
            await self.send_event_to_admins_of_org(
                organisation["org_id"], event
            )

    async def send_file_event_to_concerned(self, event: EventOut):
        await self.send_event_to_all_org(event.org_id, event)

    async def build_event_out(self, event: EventIn):

        if event.event_type not in (
            EventType.AUTH_LOGIN,
            EventType.AUTH_LOGOUT,
            EventType.FILE_CREATED,
            EventType.FILE_UPDATED,
            EventType.FILE_DELETED,
        ):
            raise HTTPException(status_code=422, detail="unknow event")
        if event.event_type in (EventType.AUTH_LOGIN, EventType.AUTH_LOGOUT):
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
                raise ValueError("User not found")
            if not event.org_id or not event.file_name:
                raise ValueError("Organisation id or file name not provided")
            responses = await self.get_organisation_name_from_org_id(
                event.org_id
            )
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

    async def publish_event(self, event_in: EventIn):

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
