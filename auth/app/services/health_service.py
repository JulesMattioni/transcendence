from shared.base_service import BaseService


class HealthService(BaseService):
    """
    Service exposing a basic health status for the auth service.
    """

    def __init__(self, service_name: str) -> None:
        """
        Initialize the health service with its service name.

        Args:
            service_name: Name of the service reported in health checks.
        """

        super().__init__()
        self._service_name = service_name

    def check(self) -> dict[str, str]:
        """
        Build the current health status of the service.

        Returns:
            A dictionary with the service status ("status": "ok") and its name
            ("service").
        """

        return {"status": "ok", "service": self._service_name}
