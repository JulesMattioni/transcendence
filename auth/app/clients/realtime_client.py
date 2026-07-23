import asyncio
import logging

import httpx

from app.config import REALTIME_BASE_URL

logger = logging.getLogger(__name__)


class RealtimeClient:
    """
    Outbound HTTP client notifying the realtime service of auth events
    (login, logout).
    """

    def __init__(self, base_url: str = REALTIME_BASE_URL) -> None:
        """
        Initialize the client with the realtime service base URL.

        Args:
            base_url: Base URL of the realtime service.
        """

        self._base_url = base_url

    def notify_log_event(
        self, event_type: str, user_id: int, first_name: str, last_name: str
    ) -> None:
        """
        Schedule the auth event broadcast without awaiting its result.

        Args:
            event_type: Event name (auth.login, auth.logout).
            user_id: ID of the user the event concerns.
            first_name: User's first name.
            last_name: User's last name.
        """

        asyncio.create_task(
            self._post_event(
                event_type=event_type,
                user_id=user_id,
                first_name=first_name,
                last_name=last_name,
            )
        )

    async def _post_event(
        self, event_type: str, user_id: int, first_name: str, last_name: str
    ) -> None:
        """
        POST the auth event to the realtime service; failures are only
        logged.

        Args:
            event_type: Event name (auth.login, auth.logout).
            user_id: ID of the user the event concerns.
            first_name: User's first name.
            last_name: User's last name.
        """

        payload = {
            "event_type": event_type,
            "user_id": user_id,
            "first_name": first_name,
            "last_name": last_name,
        }
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(2.0)) as client:
                await client.post(
                    f"{self._base_url}/internal/events", json=payload
                )
        except Exception as exc:
            logger.warning(
                "realtime event %s failed for user %s %s: %s",
                event_type,
                first_name,
                last_name,
                exc,
            )
