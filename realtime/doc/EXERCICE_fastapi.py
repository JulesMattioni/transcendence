"""
=============================================================================
 EXERCICE FastAPI — à trous. Remplis les TODO, puis vérifie dans /docs.
=============================================================================

Lance :
    cd realtime
    uv run uvicorn EXERCICE_fastapi:app --reload --port 8002

Teste :  http://localhost:8002/docs   (clique "Try it out" sur chaque endpoint)

Corrigé : EXERCICE_fastapi_corrige.py  (ne l'ouvre qu'après avoir essayé !)

Barème mental : si /docs charge sans erreur ET que chaque endpoint renvoie
ce qui est décrit dans son commentaire, c'est gagné.
=============================================================================
"""

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel


# TODO 1 --------------------------------------------------------------------
# Crée l'objet application FastAPI avec le titre "exercice".
# Souviens-toi : uvicorn cherche la variable "app".
app = FastAPI(title="exercice")


# TODO 2 --------------------------------------------------------------------
# Un endpoint GET /ping qui renvoie {"pong": True}.
# Question : sync `def` ou `async def` ? (indice : y a-t-il un await ?)
# Écris le décorateur ET la fonction ci-dessous.
#
# @app.???("/ping")
# ??? def ping() -> dict:
#     return ...


# TODO 3 --------------------------------------------------------------------
# Un endpoint GET /wait qui fait `await asyncio.sleep(1)` puis renvoie
# {"done": True}. Ici tu ES OBLIGÉ d'un style précis à cause du await.
# Lequel ? Écris-le.


# TODO 4 --------------------------------------------------------------------
# PATH param. Endpoint GET /square/{n} qui renvoie {"n": n, "square": n*n}.
# Fais en sorte que passer /square/abc renvoie une erreur automatique
# (indice : c'est le TYPE de l'argument qui déclenche la validation).


# TODO 5 --------------------------------------------------------------------
# QUERY param. Endpoint GET /greet qui lit ?name=... (obligatoire) et
# ?excited=... (booléen, défaut False). Renvoie {"msg": "Hello NAME!"} ou
# "Hello NAME" sans "!" selon excited.
# Rappel : un paramètre qui n'est PAS dans le chemin est lu dans la query.


# TODO 6 --------------------------------------------------------------------
# BODY Pydantic. Complète EventIn pour matcher ton MODULE.md :
#   event_type : str
#   actor_id   : int
#   target     : Target ou None (défaut None)
#   payload    : dict (défaut vide)
class Target(BaseModel):
    type: str
    id: int


class EventIn(BaseModel):
    ...  # <-- remplace par les 4 champs


class EventOut(BaseModel):
    event_id: str
    event_type: str
    actor_id: int
    target: Target | None
    timestamp: str
    payload: dict


# TODO 7 --------------------------------------------------------------------
# Complète enrich() : construis un EventOut à partir d'un EventIn.
# - event_id  : un uuid4 en str
# - timestamp : datetime.now(timezone.utc).isoformat()
# - les autres champs : recopiés depuis event_in
def enrich(event_in: EventIn) -> EventOut:
    ...  # <-- remplace


# TODO 8 --------------------------------------------------------------------
# Complète le ConnectionManager. Attention au sync/async :
# - connect  : DOIT await ws.accept() puis ajouter à la liste  -> async
# - disconnect : simple retrait mémoire                        -> sync
# - broadcast : DOIT await ws.send_json(...) pour chaque ws    -> async
class ConnectionManager:
    def __init__(self) -> None:
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        ...  # await accept, puis append

    def disconnect(self, ws: WebSocket) -> None:
        ...  # retirer ws de self.active si présent

    async def broadcast(self, message: dict) -> None:
        ...  # pour chaque ws de la liste : await ws.send_json(message)


manager = ConnectionManager()


# TODO 9 --------------------------------------------------------------------
# Endpoint d'ingestion : POST /internal/events
# - reçoit un EventIn (body JSON, validé tout seul)
# - l'enrichit avec enrich()
# - le broadcast à tous les WS  (await !)  -> donc quel style de def ?
# - renvoie l'EventOut
#
# @app.post("/internal/events")
# ??? def ingest(event: EventIn) -> EventOut:
#     ...


# TODO 10 -------------------------------------------------------------------
# WebSocket : /ws/audit
# - décorateur @app.websocket("/ws/audit")   (PAS @app.get !)
# - async obligatoire
# - await manager.connect(ws)
# - boucle while True: await ws.receive_text()  (pour rester connecté)
# - en cas de WebSocketDisconnect : manager.disconnect(ws)
#
# @app.websocket("/ws/audit")
# async def ws_audit(ws: WebSocket) -> None:
#     ...


# ---------------------------------------------------------------------------
# Une fois tout rempli, teste dans /docs. Pour le WebSocket, le plus simple :
# ouvre la console du navigateur (F12) sur n'importe quelle page et fais
#
#   const s = new WebSocket("ws://localhost:8002/ws/audit");
#   s.onmessage = (e) => console.log("reçu:", e.data);
#
# puis, depuis /docs, envoie un POST /internal/events : tu dois voir
# l'événement arriver dans la console. C'est ton flux ingestion -> diffusion !
# ---------------------------------------------------------------------------
