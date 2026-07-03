from fastapi import APIRouter
from app.services.health_service import HealthService

router = APIRouter()
_service = HealthService(service_name="rag")


@router.get("/health")
def health() -> dict[str, str]:
    return _service.check()
