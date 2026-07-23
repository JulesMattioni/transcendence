from fastapi import APIRouter
from app.schemas.event_in import EventIn
from app.services.event_dispatcher import dispatcher
from fastapi import HTTPException

router = APIRouter()


@router.post("/internal/events", status_code=202)
async def ingest(event: EventIn) -> str:
    try:
        await dispatcher.publish_event(event)

    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"An error occured {e}",
        )
    return "OK"
