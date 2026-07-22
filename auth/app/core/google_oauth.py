import httpx

from typing import Any

from app.exceptions import GoogleAuthError
from app.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_REDIRECT_URI,
    GOOGLE_CLIENT_SECRET,
)


async def get_google_profile(code: str) -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )

        try:
            token_response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise GoogleAuthError() from e

        google_access_token = token_response.json()["access_token"]

        profile_reponse = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {google_access_token}"},
        )

        try:
            profile_reponse.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise GoogleAuthError() from e

        return profile_reponse.json()
