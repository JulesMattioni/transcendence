from fastapi import APIRouter
from app.services.health_service import HealthService

router = APIRouter()
_service = HealthService(service_name="core")


@router.get("/health")
def health() -> dict[str, str]:
    return _service.check()
