"""Internal router other services use to publish events."""

from fastapi import APIRouter
from app.schemas.event_in import EventIn
from app.services.event_dispatcher import dispatcher
from fastapi import HTTPException

router = APIRouter()


@router.post("/internal/events", status_code=202)
async def ingest(event: EventIn) -> str:
    """Ingest an event and hand it to the dispatcher for broadcasting.

    Args:
        event: The validated inbound event.

    Returns:
        The string ``"OK"`` with HTTP ``202 Accepted``.

    Raises:
        HTTPException: Re-raised as-is when the dispatcher rejects the
            event; any other error is wrapped into a ``422``.
    """
    try:
        await dispatcher.publish_event(event)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"An error occured {e}",
        )
    return "OK"
