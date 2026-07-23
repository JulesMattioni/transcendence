from shared.base_service import BaseService


class HealthService(BaseService):
    """
    Service reporting the liveness of this application.
    """

    def __init__(self, service_name: str) -> None:
        """
        Initialize the service with its public name.

        Args:
            service_name: Name reported in the health payload.
        """

        super().__init__()
        self._service_name = service_name

    def check(self) -> dict[str, str]:
        """
        Build the health payload for this service.

        Returns:
            Dict with the service status and name.
        """

        return {"status": "ok", "service": self._service_name}
