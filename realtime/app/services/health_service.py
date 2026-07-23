"""Health service returning the readiness status of a service."""

from shared.base_service import BaseService


class HealthService(BaseService):
    """Produce the health-check payload for a named service."""

    def __init__(self, service_name: str) -> None:
        """Store the ``service_name`` reported by :meth:`check`."""
        super().__init__()
        self._service_name = service_name

    def check(self) -> dict[str, str]:
        """Return ``{"status": "ok", "service": <service_name>}``."""
        return {"status": "ok", "service": self._service_name}
