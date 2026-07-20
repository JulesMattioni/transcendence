import asyncio
import logging

import httpx

from app.config import RAG_BASE_URL

logger = logging.getLogger(__name__)


class RagClient:
    """Client fire-and-forget vers le service rag pour l'ingestion.

    Un échec (rag down, timeout) est logué mais ne remonte jamais à
    l'appelant : l'upload doit réussir même si l'ingestion échoue.
    """

    def __init__(self, base_url: str = RAG_BASE_URL) -> None:
        self._base_url = base_url

    def trigger_ingest(
        self,
        file_id: int,
        organisation_id: int,
        filepath: str,
        content_type: str,
    ) -> None:
        """Lance l'ingestion en tâche de fond, sans attendre la réponse."""
        asyncio.create_task(
            self._post_ingest(file_id, organisation_id, filepath, content_type)
        )

    async def _post_ingest(
        self,
        file_id: int,
        organisation_id: int,
        filepath: str,
        content_type: str,
    ) -> None:
        payload = {
            "file_id": file_id,
            "organisation_id": organisation_id,
            "filepath": filepath,
            "content_type": content_type,
        }
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
                await client.post(f"{self._base_url}/ingest", json=payload)
        except Exception as exc:
            logger.warning("rag ingestion trigger failed for file %s: %s", file_id, exc)
