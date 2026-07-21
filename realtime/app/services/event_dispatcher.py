from app.services.connection_manager import manager
from app.schemas.event_in import EventOut
from app.services.get_current_user import get_current_user


def mock_org():
    return {
        "user_id": 42,
        "organisations": [
            {"org_id": 1, "name": "Belle Organisation", "role": "admin"},
            {"org_id": 2, "name": "Magnifique Organisation", "role": "reader"},
        ],
    }


class Dispatcher:
    async def dispatch(event: EventOut):
        pass
        # manager.broadcast_all(event, id)
        # manager.broadcast_id(event, id)


dispatcher = Dispatcher()
