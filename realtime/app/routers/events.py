from fastapi import APIRouter
from app.schemas.event_in import EventIn
from app.schemas.event_out import EventOut
from app.services.event_dispatcher import dispatcher

router = APIRouter()


@router.post("/internal/events", status_code=202)
async def ingest(event: EventIn) -> dict:
    await dispatcher.publish_event(event)
    return "OK"
