import asyncio
import logging

import httpx

from app.config import REALTIME_BASE_URL

logger = logging.getLogger(__name__)


class RealtimeClient:
    def __init__(self, base_url: str = REALTIME_BASE_URL) -> None:
        self._base_url = base_url

    def notify_file_event(
        self,
        event_type: str,
        org_id: int,
        file_name: str,
    ) -> None:
        asyncio.create_task(self._post_event(event_type, org_id, file_name))

    async def _post_event(
        self,
        event_type: str,
        org_id: int,
        file_name: str,
    ) -> None:
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
