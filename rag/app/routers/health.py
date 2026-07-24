from fastapi import APIRouter
from app.services.health_service import HealthService

router = APIRouter()
_service = HealthService(service_name="rag")


@router.get("/health")
def health() -> dict[str, str]:
    """
    Report that this service is alive.

    Returns:
        Dict with the service status and name.
    """

    return _service.check()
