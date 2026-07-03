from app.services.base import BaseService


class HealthService(BaseService):
    def __init__(self, service_name: str) -> None:
        super().__init__()
        self._service_name = service_name

    def check(self) -> dict[str, str]:
        return {"status": "ok", "service": self._service_name}
