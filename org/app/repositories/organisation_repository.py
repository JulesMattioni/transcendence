"""Data access for organisations."""

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.organisation import Organisation
from app.schemas.organisation import OrganisationUpdate


class OrganisationRepository:
    """Persist and query :class:`Organisation` rows."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the repository to a database session."""
        self.session = session

    async def create_organisation(self, name_org: str) -> Organisation:
        """Insert a new organisation and return it (flushed, not committed)."""
        new_org = Organisation(name=name_org)
        self.session.add(new_org)
        await self.session.flush()
        return new_org

    async def get_by_id(self, org_id: int) -> Organisation | None:
        """Return the organisation with ``org_id``, or ``None``."""
        return await self.session.get(Organisation, org_id)

    async def update(
        self, org_id: int, table_data: OrganisationUpdate
    ) -> Organisation | None:
        """Apply the set fields of ``table_data`` to the organisation.

        Args:
            org_id: Organisation to update.
            table_data: Partial update; only set fields are applied.

        Returns:
            The updated organisation, or ``None`` if it does not exist.
        """
        organisation = await self.get_by_id(org_id)
        if organisation:
            update_dict = table_data.model_dump(exclude_unset=True)
            for key, value in update_dict.items():
                if hasattr(organisation, key):
                    setattr(organisation, key, value)
            await self.session.flush()
            return organisation
        return None

    async def delete_org(self, org_id: int) -> bool:
        """Delete the organisation; return ``True`` if one was removed."""
        organisation = await self.get_by_id(org_id)
        if organisation:
            await self.session.delete(organisation)
            await self.session.flush()
            return True
        return False
