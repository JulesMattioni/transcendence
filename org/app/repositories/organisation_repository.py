from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select




class OrganisationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session