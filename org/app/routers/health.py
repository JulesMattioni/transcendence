"""Health-check router of the org service."""

from fastapi import APIRouter
from app.services.health_service import HealthService

router = APIRouter()
_service = HealthService(service_name="org")


@router.get("/health")
def health() -> dict[str, str]:
    """Return the liveness status of the service.

    Returns:
        A mapping with a ``status`` key set to ``"ok"`` and a ``service``
        key naming the service, suitable for orchestrator probes.
    """
    return _service.check()
