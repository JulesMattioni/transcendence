"""HTTP client resolving a bearer token to its user."""

import httpx
from fastapi import HTTPException


async def get_current_user(token: str):
    """Resolve the user behind a bearer token via the ``auth`` service.

    Args:
        token: Bearer token to validate.

    Returns:
        The decoded user JSON (``id``, ``first_name``, ``last_name``, ...).

    Raises:
        HTTPException: ``503`` if ``auth`` is unreachable, ``401`` if the
            token is rejected.
    """
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        try:
            response = await client.get(
                "http://auth:8000/me",
                headers={"Authorization": f"Bearer {token}"},
            )
        except httpx.HTTPError:
            raise HTTPException(
                status_code=503, detail="Auth service unavailable"
            )

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid token")
    response = response.json()
    return response
