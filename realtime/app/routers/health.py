from fastapi import APIRouter
from app.services.health_service import HealthService

router = APIRouter()
_service = HealthService(service_name="realtime")


@router.get("/health")
def health() -> dict[str, str]:
    return _service.check()
