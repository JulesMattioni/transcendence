from fastapi import APIRouter
from app.services.health_service import HealthService

router = APIRouter()
_service = HealthService(service_name="auth")


@router.get("/health")
def health() -> dict[str, str]:
    """
    Health check endpoint for the auth service.

    Returns:
        A dictionary with the service status ("status") and its name
        ("service").
    """

    return _service.check()
