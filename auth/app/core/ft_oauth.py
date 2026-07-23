import httpx

from typing import Any

from app.exceptions import FtAuthError
from app.config import FT_CLIENT_ID, FT_CLIENT_SECRET, FT_REDIRECT_URI


async def get_ft_profile(code: str) -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://api.intra.42.fr/oauth/token",
            data={
                "code": code,
                "client_id": FT_CLIENT_ID,
                "client_secret": FT_CLIENT_SECRET,
                "redirect_uri": FT_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )

        try:
            token_response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise FtAuthError() from e

        ft_access_token = token_response.json()["access_token"]

        profile_reponse = await client.get(
            "https://api.intra.42.fr/v2/me",
            headers={"Authorization": f"Bearer {ft_access_token}"},
        )

        try:
            profile_reponse.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise FtAuthError() from e

        return profile_reponse.json()
