import httpx
from fastapi import HTTPException
from app.config import ORG_BASE_URL


class OrgClient:
    """
    Outbound HTTP client resolving a caller's role from the org service.

    Unlike the fire-and-forget clients, this one is awaited: its answer
    decides whether a request is authorised, so a transport failure must
    deny access rather than silently allow it.
    """

    def __init__(self, base_url: str = ORG_BASE_URL) -> None:
        """
        Initialize the client with the org service base URL.

        Args:
            base_url: Base URL of the org service.
        """

        self._base_url = base_url

    async def get_member_role(
        self, organisation_id: int, user_id: int
    ) -> int | None:
        """
        Return the caller's role id within an organisation.

        Args:
            organisation_id: Organisation the membership is checked in.
            user_id: Id of the authenticated user.

        Returns:
            The member's role id, or None when the user is not a member.

        Raises:
            HTTPException: 503 when the org service cannot be reached or
            answers with an unexpected status.
        """

        url = (
            f"{self._base_url}/internal/organisations/{organisation_id}"
            f"/members/{user_id}/role"
        )
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(10.0)
            ) as client:
                response = await client.get(url)
        except httpx.HTTPError:
            raise HTTPException(
                status_code=503, detail="Org service unavailable"
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=503, detail="Org service unavailable"
            )

        return response.json()["role_id"]
