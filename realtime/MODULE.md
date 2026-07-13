# realtime — Temps réel (WebSockets)

Gère la **présence en ligne** et le **flux d'audit live** : affiche qui fait quoi en
temps réel (connexions, consultations de documents, changements de rôle).

**Module :** Temps réel (WebSockets) — Web — *Majeur (2 pts)*
**Stack :** Python + FastAPI + WebSockets

---

## Architecture — deux flux distincts

Le service a **deux surfaces**, avec des rôles opposés :

```
        (1) INGESTION  (service → realtime)          (2) DIFFUSION  (realtime → navigateurs)
        ─────────────────────────────────           ──────────────────────────────────────
  ┌──────┐  POST      ┌───────────────────────┐   broadcast   ┌─────────────┐
  │ core │ ─────────► │                       │ ────────────► │ browser A   │  WS sur /ws/
  └──────┘  /internal │      realtime         │               ├─────────────┤
  ┌──────┐  /events   │  (ConnectionManager)  │ ────────────► │ browser B   │
  │ auth │ ─────────► │                       │               ├─────────────┤
  └──────┘            └───────────────────────┘ ────────────► │ browser C   │
                                                              └─────────────┘
```

### (1) Ingestion — comment les autres services publient un événement

- Les services (core, auth, org…) appellent l'endpoint HTTP interne
  **`POST http://realtime:8000/internal/events`**.
- Cet appel se fait **de container à container** sur le réseau Docker interne,
  **PAS via la gateway** (donc pas de `/ws/`, pas de ModSecurity sur du trafic interne).
- L'endpoint `/internal/events` n'est **jamais exposé** dans la gateway : il reste privé
  au réseau Docker.

### (2) Diffusion — comment les navigateurs reçoivent le flux

- Le navigateur ouvre une connexion WebSocket persistante sur **`wss://localhost:8443/ws/…`**.
- La gateway route déjà `/ws/` → `realtime:8000` avec les headers `Upgrade`/`Connection`
  (voir `gateway/conf/default.conf.template`). **Rien à toucher côté nginx.**
- Le `ConnectionManager` garde la liste des WS connectés et fait un `broadcast()`
  à chaque événement reçu en (1).

> **À retenir :** l'ingestion (1) ≠ la diffusion (2). Un service qui veut publier un
> événement fait un **POST HTTP interne**, il n'ouvre jamais de WebSocket.

---

## Schéma d'un événement

Deux formes du même événement : ce que l'émetteur envoie, et ce que realtime rediffuse.

**`EventIn`** — ce que core/auth envoient à `POST /internal/events` :

```json
{
  "event_type": "document.accessed",
  "actor_id": 42,
  "target": { "type": "document", "id": 108 },
  "payload": { "filename": "rapport.pdf" }
}
```

**`EventOut`** — ce que realtime diffuse sur `/ws/` (enrichi) :

```json
{
  "event_id": "3f9c…-uuid4",
  "event_type": "document.accessed",
  "actor_id": 42,
  "target": { "type": "document", "id": 108 },
  "timestamp": "2026-07-13T09:20:00Z",
  "payload": { "filename": "rapport.pdf" }
}
```

| Champ        | Type                        | Qui le pose | Détail |
|--------------|-----------------------------|-------------|--------|
| `event_id`   | `str` (uuid4)               | **realtime** | Identifiant unique, généré à la réception. |
| `event_type` | `str` `"domaine.action"`    | émetteur    | Hiérarchique, filtrable. Ex : `auth.login`, `document.accessed`, `role.changed`. |
| `actor_id`   | `int`                       | émetteur    | L'utilisateur qui déclenche l'action. |
| `target`     | `{ "type": str, "id": int }` ou `null` | émetteur | Objet concerné. `null` pour un simple login. |
| `timestamp`  | `str` (ISO 8601 UTC)        | **realtime** | Heure de réception. |
| `payload`    | `dict` libre                | émetteur    | Détails spécifiques à l'événement. |

**Convention `event_type` :** `domaine.action`, ex.
`auth.login`, `auth.logout`, `document.accessed`, `document.created`, `role.changed`.

**Décision V1 :** realtime **rediffuse sans persister** (pas de table DB, pas de
migration). L'historique (`audit_events` + rejeu au chargement de page) pourra être
ajouté plus tard sans changer le flux de diffusion.

---

## À faire (ordre de dev)

1. **WebSocket echo** — `@app.websocket("/ws/audit")` : accepter la connexion et
   renvoyer un message. Valider de bout en bout via `wss://localhost:8443/ws/audit`
   (prouve que le tunnel WS marche à travers la gateway).
2. **`ConnectionManager`** — classe qui garde la liste des WS connectés
   (`connect` / `disconnect` / `broadcast`). → présence en ligne.
3. **Schémas Pydantic** — `EventIn` (entrée) et `EventOut` (sortie enrichie).
4. **Endpoint d'ingestion** — `POST /internal/events` : reçoit un `EventIn`, l'enrichit
   (`event_id` + `timestamp`), puis `broadcast()` le `EventOut` à tous les WS.
   Tester seul avec un `curl` qui simule core.
5. **Auth JWT des connexions WS** — d'abord une dependency `get_current_user` **mockée**
   (token factice), rebranchée sur le vrai JWT quand le module auth est prêt.

**Dépendances (ne bloquent pas le démarrage) :**
- *JWT auth* (module auth, en cours) → mocké au début, comme le pattern déjà retenu pour core.
- *Émission des événements* par core/auth/org → ils s'y brancheront plus tard ; le contrat
  ci-dessus (`EventIn`) suffit pour qu'ils sachent quoi envoyer.
