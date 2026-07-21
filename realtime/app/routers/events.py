from fastapi import APIRouter
from app.schemas.event_in import EventIn
from app.schemas.event_out import EventOut
from app.services.event_dispatcher import dispatcher

router = APIRouter()


@router.post("/events", status_code=202)
async def ingest(event: EventIn) -> dict:
    event_out = EventOut.from_event_in(event)
    await dispatcher.dispatch(event_out)
    return {"event_id": event_out.event_id}
