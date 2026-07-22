import httpx
from fastapi import HTTPException


async def get_current_user(token: str):
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
