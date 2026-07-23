import httpx
from fastapi import HTTPException


async def get_orgs_from_user_id(user_id: int):
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
