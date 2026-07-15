"""
=============================================================================
 GUIDE FastAPI — comprendre les briques avant de coder ton module realtime
=============================================================================

À LIRE de haut en bas, puis à FAIRE TOURNER :

    cd realtime
    uv run uvicorn GUIDE_fastapi:app --reload --port 8001

Puis ouvre dans un navigateur :  http://localhost:8001/docs
FastAPI génère une doc interactive (Swagger) où tu peux tester chaque endpoint
en cliquant. C'est ton meilleur ami pour apprendre.

Ce fichier est un BAC À SABLE. Il ne fait pas partie de ton vrai service
(ton vrai service c'est main.py). Tu peux le supprimer quand tu as compris.
=============================================================================
"""

# -----------------------------------------------------------------------------
# 0. Les imports — d'où viennent les briques
# -----------------------------------------------------------------------------
# FastAPI       : l'application elle-même.
# APIRouter     : regroupe des endpoints dans un sous-fichier (comme ton health.py).
# WebSocket     : le type d'une connexion WS (pour /ws/audit).
# WebSocketDisconnect : l'exception levée quand un navigateur ferme l'onglet.
# HTTPException : pour renvoyer une erreur HTTP propre (404, 400...).
# BaseModel     : la brique Pydantic pour valider/décrire les données entrantes.

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel




# -----------------------------------------------------------------------------
# 1. L'objet application
# -----------------------------------------------------------------------------
# `app` est LA variable que uvicorn va chercher (le "app" dans "GUIDE_fastapi:app").
# Dans ton vrai code c'est dans main.py.
app = FastAPI(title="guide-fastapi")


# =============================================================================
# 2. sync `def` vs `async def` — LA question que tu poses
# =============================================================================
#
# Règle mentale simple :
#
#   - `async def`  => "je vais ATTENDRE quelque chose du réseau / d'un autre
#                      service / d'une socket, et pendant que j'attends, le
#                      serveur peut servir d'autres requêtes."
#                      Tu écris `await ...` à l'intérieur.
#
#   - `def` (sync) => "je fais un calcul rapide en mémoire, je ne bloque rien."
#                      C'est le cas de ton health.py actuel : il construit juste
#                      un dict et le renvoie. Pas besoin d'async.
#
# FastAPI accepte LES DEUX. Il est assez malin :
#   - un `async def` tourne directement dans la boucle d'événements ;
#   - un `def` normal est exécuté dans un thread à part pour ne pas bloquer.
#
# DANGER classique : mettre du code BLOQUANT (ex: time.sleep, requests.get,
# une grosse boucle CPU) DANS un `async def`. Ça gèle TOUT le serveur, car
# rien d'autre ne peut tourner tant que tu ne rends pas la main avec `await`.
# Si tu dois attendre, utilise la version async (`await asyncio.sleep`,
# un client HTTP async comme httpx, etc.).
#
# POUR TON MODULE realtime, concrètement :
#   - /health           -> `def`        (calcul instantané, comme aujourd'hui)
#   - POST /internal/events -> `async def` (tu vas `await manager.broadcast(...)`
#                                            qui écrit sur des sockets réseau)
#   - /ws/audit         -> `async def`   (OBLIGATOIRE, les WebSockets sont
#                                          intégralement asynchrones :
#                                          await ws.accept(), await ws.receive...)


# --- Exemple sync : rapide, en mémoire -> `def` suffit --------------------
@app.get("/sync-example")
def sync_example() -> dict[str, str]:
    # Pas d'await ici, juste un dict. Exactement comme ton health() actuel.
    return {"style": "sync", "hint": "aucun await -> def normal"}


# --- Exemple async : on "attend" (ici simulé par asyncio.sleep) -> `async def`
@app.get("/async-example")
async def async_example() -> dict[str, str]:
    # `await` = "mets ma requête en pause, laisse le serveur bosser ailleurs,
    #            et reviens quand c'est prêt". Pendant cette seconde, le serveur
    #            peut répondre à d'autres clients.
    await asyncio.sleep(1)
    return {"style": "async", "hint": "il y a un await -> async def"}


# =============================================================================
# 3. Les "variables" d'un endpoint : path, query, body
# =============================================================================
# FastAPI remplit les arguments de ta fonction TOUT SEUL selon leur nom/type.
# C'est le cœur de l'apprentissage. Trois sources :

# (a) PATH param : la valeur est DANS l'URL. Le nom {user_id} doit matcher
#     l'argument user_id. Le type `int` => FastAPI convertit "42" -> 42,
#     et renvoie une erreur 422 automatique si on passe "abc".
@app.get("/users/{user_id}")
def get_user(user_id: int) -> dict[str, int | str]:
    return {"user_id": user_id, "type": "path param (int auto-validé)"}


# (b) QUERY param : après le "?". Ici `limit` n'est PAS dans le chemin, donc
#     FastAPI le lit dans ?limit=... . La valeur par défaut le rend optionnel.
#     Teste : /search?q=chat&limit=5
@app.get("/search")
def search(q: str, limit: int = 10) -> dict[str, int | str]:
    return {"query": q, "limit": limit}


# (c) BODY (JSON) via Pydantic : c'est CE QUI T'INTÉRESSE pour /internal/events.
#     Tu déclares une classe qui décrit la forme attendue, et FastAPI :
#       - parse le JSON,
#       - VALIDE les types (int, str, structure imbriquée),
#       - renvoie une 422 claire si c'est mal formé,
#       - te donne un objet Python propre (event.actor_id, ...).

# Sous-structure imbriquée (le "target" de ton EventIn).
class Target(BaseModel):
    type: str
    id: int


# Ceci est ton EventIn du MODULE.md, en vrai code.
class EventIn(BaseModel):
    event_type: str          # "document.accessed"
    actor_id: int            # 42
    target: Target | None = None   # peut être null (ex: un simple login)
    payload: dict = {}       # dict libre


# Et voici ton EventOut : l'événement enrichi que realtime rediffuse.
class EventOut(BaseModel):
    event_id: str
    event_type: str
    actor_id: int
    target: Target | None
    timestamp: str
    payload: dict


# =============================================================================
# 4. Le pattern router + service (comme ton health.py / health_service.py)
# =============================================================================
# Ton projet sépare :
#   - le ROUTER  = la "prise réseau" (quelle URL, quel verbe HTTP)  -> app/routers/
#   - le SERVICE = la logique métier, testable sans réseau          -> app/services/
#
# On reproduit ça ici en petit pour l'ingestion d'événements.

class EventService:
    """Logique métier : transformer un EventIn en EventOut enrichi.

    Note : cette méthode est du calcul pur (uuid + horodatage), donc un `def`
    normal suffit. Le broadcast réseau, lui, sera async (voir ConnectionManager).
    """

    def enrich(self, event_in: EventIn) -> EventOut:
        return EventOut(
            event_id=str(uuid4()),                              # généré par realtime
            event_type=event_in.event_type,
            actor_id=event_in.actor_id,
            target=event_in.target,
            timestamp=datetime.now(timezone.utc).isoformat(),   # horodaté par realtime
            payload=event_in.payload,
        )


# =============================================================================
# 5. Le ConnectionManager — le cœur de la partie WebSocket
# =============================================================================
# Il garde la liste des navigateurs connectés et sait diffuser à tous.
# Toutes les opérations réseau sont `async` (await ws.accept / send / ...).

class ConnectionManager:
    def __init__(self) -> None:
        # Liste des connexions WS ouvertes. En mémoire (V1 : pas de DB).
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()          # on DOIT accepter la poignée de main WS
        self.active.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        # Retirer de la liste : simple opération mémoire -> pas besoin d'async.
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, message: dict) -> None:
        # Envoyer à TOUT le monde. On itère sur une copie car un envoi peut
        # échouer et modifier la liste.
        for ws in list(self.active):
            await ws.send_json(message)


manager = ConnectionManager()
event_service = EventService()


# =============================================================================
# 6. Les endpoints réels de ton module, en version démo
# =============================================================================

# --- (1) INGESTION : POST /internal/events -----------------------------------
# async car on `await manager.broadcast(...)` (écriture réseau sur N sockets).
# L'argument `event` de type EventIn => FastAPI valide le JSON entrant tout seul.
@app.post("/internal/events")
async def ingest_event(event: EventIn) -> EventOut:
    enriched = event_service.enrich(event)          # calcul sync
    await manager.broadcast(enriched.model_dump())  # diffusion async
    return enriched   # renvoyé à l'appelant (core/auth) pour confirmation


# --- (2) DIFFUSION : WebSocket /ws/audit -------------------------------------
# OBLIGATOIREMENT async. Le décorateur est @app.websocket, PAS @app.get.
@app.websocket("/ws/audit")
async def ws_audit(ws: WebSocket) -> None:
    await manager.connect(ws)
    try:
        # Boucle : on reste connecté tant que le navigateur ne ferme pas.
        # Ici on lit ce qu'il envoie juste pour détecter la déconnexion ;
        # dans ton vrai flux, le navigateur ne fait que RECEVOIR des events.
        while True:
            await ws.receive_text()   # bloque proprement jusqu'à message OU close
    except WebSocketDisconnect:
        # Le navigateur a fermé l'onglet -> on nettoie.
        manager.disconnect(ws)


# =============================================================================
# 7. APIRouter : pourquoi ton health est dans un fichier séparé
# =============================================================================
# Au lieu de tout mettre sur `app`, on regroupe des endpoints dans un router,
# puis on le "branche" sur l'app avec include_router. C'est ce que fait ton
# main.py avec health.router. Démo :

demo_router = APIRouter(prefix="/demo", tags=["demo"])


@demo_router.get("/ping")
def demo_ping() -> dict[str, str]:
    return {"pong": "depuis un APIRouter"}


# HTTPException : lever une vraie erreur HTTP proprement.
@demo_router.get("/items/{item_id}")
def get_item(item_id: int) -> dict[str, int]:
    if item_id > 100:
        raise HTTPException(status_code=404, detail="item introuvable")
    return {"item_id": item_id}


app.include_router(demo_router)   # sans ça, /demo/ping n'existe pas.


# =============================================================================
# RÉCAP — ce que tu dois retenir pour coder realtime
# =============================================================================
# 1. `app = FastAPI()` : la variable que uvicorn lance. (dans main.py)
# 2. `def` = calcul rapide en mémoire (health).  `async def` = tu fais `await`
#    (réseau, sockets, broadcast). WebSocket => TOUJOURS async.
# 3. Ne JAMAIS bloquer (time.sleep, boucle CPU lourde) dans un async def.
# 4. Les arguments d'un endpoint se remplissent tout seuls selon leur source :
#    {dans_url} = path, ?apres=le?point = query, un modèle Pydantic = body JSON.
# 5. Pydantic (BaseModel) = ton EventIn/EventOut : validation gratuite du JSON.
# 6. Pattern router (URL) + service (logique), déjà en place dans ton projet.
# 7. ConnectionManager (connect/disconnect/broadcast) = le cœur du temps réel.
# 8. http://localhost:8001/docs = teste TOUT sans écrire de curl.
# =============================================================================
