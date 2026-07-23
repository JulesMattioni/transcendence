import asyncio
import logging

import httpx

from app.config import REALTIME_BASE_URL

logger = logging.getLogger(__name__)


class RealtimeClient:
    """
    Outbound HTTP client pushing file events to the realtime service.
    """

    def __init__(self, base_url: str = REALTIME_BASE_URL) -> None:
        """
        Initialize the client with the realtime service base URL.

        Args:
            base_url: Base URL of the realtime service.
        """

        self._base_url = base_url

    def notify_file_event(
        self,
        event_type: str,
        org_id: int,
        file_name: str,
    ) -> None:
        """
        Schedule the event broadcast without awaiting its result.

        Args:
            event_type: Event name (file.created, file.updated,
            file.deleted).
            org_id: Organisation whose clients receive the event.
            file_name: Original filename shown in the event.
        """

        asyncio.create_task(self._post_event(event_type, org_id, file_name))

    async def _post_event(
        self,
        event_type: str,
        org_id: int,
        file_name: str,
    ) -> None:
        """
        POST the event to realtime; failures are only logged.

        Args:
            event_type: Event name (file.created, file.updated,
            file.deleted).
            org_id: Organisation whose clients receive the event.
            file_name: Original filename shown in the event.
        """

        payload = {
            "event_type": event_type,
            "org_id": org_id,
            "file_name": file_name,
        }
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(10.0)
            ) as client:
                await client.post(
                    f"{self._base_url}/internal/events", json=payload
                )
        except Exception as exc:
            logger.warning(
                "realtime event %s failed for file %s: %s",
                event_type,
                file_name,
                exc,
            )
