import asyncio
import logging

import httpx

from app.config import RAG_BASE_URL

logger = logging.getLogger(__name__)


class RagClient:
    """
    Outbound HTTP client triggering document ingestion in the rag
    service.
    """

    def __init__(self, base_url: str = RAG_BASE_URL) -> None:
        """
        Initialize the client with the rag service base URL.

        Args:
            base_url: Base URL of the rag service.
        """

        self._base_url = base_url

    def trigger_ingest(
        self,
        file_id: int,
        organisation_id: int,
        filepath: str,
        content_type: str,
    ) -> None:
        """
        Schedule the ingestion request without awaiting its result.

        Args:
            file_id: Id of the uploaded file.
            organisation_id: Organisation owning the file.
            filepath: Storage path of the binary, shared with rag
            through the common uploads volume.
            content_type: MIME type of the binary.
        """

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
        """
        POST the ingestion payload to rag; failures are only logged.

        Args:
            file_id: Id of the uploaded file.
            organisation_id: Organisation owning the file.
            filepath: Storage path of the binary.
            content_type: MIME type of the binary.
        """

        payload = {
            "file_id": file_id,
            "organisation_id": organisation_id,
            "filepath": filepath,
            "content_type": content_type,
        }
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(30.0)
            ) as client:
                await client.post(f"{self._base_url}/ingest", json=payload)
        except Exception as exc:
            logger.warning(
                "rag ingestion trigger failed for file %s: %s", file_id, exc
            )
