import httpx
from fastapi import HTTPException, Header, status
from app.config import AUTH_BASE_URL
from typing import Annotated
from app.schemas.user import User


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="missing header"
        )
    auth_url = f"{AUTH_BASE_URL}/me"
    header = {"Authorization": authorization}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(auth_url, headers=header)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                )
            user_data = response.json()
            return User.model_validate(user_data)
    except httpx.HTTPError:
        raise HTTPException(
                status_code=503, detail="Auth service unavailable"
            )
