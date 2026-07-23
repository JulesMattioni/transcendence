from fastapi import APIRouter
from app.services.health_service import HealthService

router = APIRouter()
_service = HealthService(service_name="core")


@router.get("/health")
def health() -> dict[str, str]:
    """
    Liveness probe reporting that the service is up.

    Returns:
        Dict with the service status and name.
    """

    return _service.check()
