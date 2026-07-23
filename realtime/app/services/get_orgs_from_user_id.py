"""HTTP client listing the organisations of a user."""

import httpx
from fastapi import HTTPException


async def get_orgs_from_user_id(user_id: int):
    """Fetch the organisations a user belongs to from the ``org`` service.

    Args:
        user_id: Identifier of the user.

    Returns:
        The decoded payload; its ``"organisation"`` key holds the list of
        organisations (each with an ``org_id``).

    Raises:
        HTTPException: ``503`` if ``org`` is unreachable, otherwise the
            upstream status code.
    """
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
