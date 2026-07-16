from shared.base_service import BaseService
from auth.app.models.auth import User
from typing import Dict, Any

class CrudUser(BaseService):
    def __init__(self, service_name: str = "org", database) -> None:
        super().__init__()
        self._service_name = service_name
        self.database = database

    def check_service(self) -> dict[str, str]:
        return {"status": "ok", "service": self._service_name}

    def create(self, user_table: Dict[str, Any]) -> User:
        pass

    def read(self):
        pass

    def update(self):
        pass

    def delete(self, user_id: int) -> bool:
        pass