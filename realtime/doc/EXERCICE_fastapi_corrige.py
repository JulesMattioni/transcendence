"""
=============================================================================
 CORRIGÉ de EXERCICE_fastapi.py
=============================================================================
Lance-le pour comparer :
    cd realtime
    uv run uvicorn EXERCICE_fastapi_corrige:app --reload --port 8003
    http://localhost:8003/docs
=============================================================================
"""

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel


# 1. L'application (la variable que uvicorn charge).
app = FastAPI(title="exercice")


# 2. GET /ping : juste un dict en mémoire -> `def` normal, pas d'await.
@app.get("/ping")
def ping() -> dict:
    return {"pong": True}


# 3. GET /wait : il y a un `await` -> `async def` OBLIGATOIRE.
@app.get("/wait")
async def wait() -> dict:
    await asyncio.sleep(1)
    return {"done": True}


# 4. PATH param typé int : /square/abc -> 422 automatique.
@app.get("/square/{n}")
def square(n: int) -> dict:
    return {"n": n, "square": n * n}


# 5. QUERY params : name obligatoire, excited optionnel (défaut False).
#    name n'est pas dans le chemin -> lu dans ?name=... ; idem ?excited=...
@app.get("/greet")
def greet(name: str, excited: bool = False) -> dict:
    msg = f"Hello {name}" + ("!" if excited else "")
    return {"msg": msg}


# 6. Les schémas Pydantic (ton contrat EventIn / EventOut).
class Target(BaseModel):
    type: str
    id: int


class EventIn(BaseModel):
    event_type: str
    actor_id: int
    target: Target | None = None
    payload: dict = {}


class EventOut(BaseModel):
    event_id: str
    event_type: str
    actor_id: int
    target: Target | None
    timestamp: str
    payload: dict


# 7. enrich : calcul pur (uuid + horodatage) -> `def` suffit.
def enrich(event_in: EventIn) -> EventOut:
    return EventOut(
        event_id=str(uuid4()),
        event_type=event_in.event_type,
        actor_id=event_in.actor_id,
        target=event_in.target,
        timestamp=datetime.now(timezone.utc).isoformat(),
        payload=event_in.payload,
    )


# 8. ConnectionManager : les opérations réseau sont async.
class ConnectionManager:
    def __init__(self) -> None:
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, message: dict) -> None:
        for ws in list(self.active):
            await ws.send_json(message)


manager = ConnectionManager()


# 9. Ingestion : on `await broadcast(...)` -> `async def`.
@app.post("/internal/events")
async def ingest(event: EventIn) -> EventOut:
    enriched = enrich(event)
    await manager.broadcast(enriched.model_dump())
    return enriched


# 10. WebSocket : toujours async, @app.websocket.
@app.websocket("/ws/audit")
async def ws_audit(ws: WebSocket) -> None:
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
