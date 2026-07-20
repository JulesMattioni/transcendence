import httpx
from fastapi import Header, HTTPException
from app.config import AUTH_BASE_URL


async def get_current_user_id(
    authorization: str | None = Header(default=None),
) -> int:
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        try:
            response = await client.get(
                f"{AUTH_BASE_URL}/me",
                headers={"Authorization": authorization},
            )
        except httpx.HTTPError:
            raise HTTPException(
                status_code=503, detail="Auth service unavailable"
            )

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid token")

    return int(response.json()["id"])
