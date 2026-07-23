"""HTTP client listing the members of an organisation."""

import httpx
from fastapi import HTTPException


async def get_members_from_organisation_id(org_id):
    """Fetch an organisation's members from the ``org`` service.

    Args:
        org_id: Identifier of the organisation.

    Returns:
        The decoded list of member records (each with ``user_id`` and
        ``role_id``).

    Raises:
        HTTPException: ``503`` if ``org`` is unreachable, otherwise the
            upstream status code.
    """
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
