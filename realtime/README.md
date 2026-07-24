# realtime — Keepr live-events service

The **realtime** service is the live-events backbone of Keepr. It keeps a
persistent WebSocket open with every connected client and pushes them, in
real time, the events they are entitled to see: a colleague logging in or
out, a file created/updated/deleted in one of their organisations. It also
answers "who is online" queries so the UI can render presence.

It is a [FastAPI](https://fastapi.tiangolo.com/) application exposed inside
the Docker network on port `8000`. Its WebSocket endpoint is reachable from
the outside through the gateway under the prefix **`/ws/`**
(e.g. `wss://<host>/ws/audit`). Its HTTP endpoints are **internal only** —
they are not proxied by the gateway and are meant to be called by the other
backend services over the Docker network.

---

## Responsibilities

- **Presence tracking** — maintain an in-memory registry of every open
  connection, indexed by user id. A user connected from several tabs/devices
  holds several sockets. This registry is the single source of truth for
  "who is online".
- **Event fan-out** — receive an event from another service and deliver it
  only to the connections that should see it, resolving the recipient set
  from the `org` service:
  - **auth events** (`auth.login` / `auth.logout`) reach the **admins** of
    every organisation the acting user belongs to;
  - **file events** (`file.created` / `file.updated` / `file.deleted`) reach
    **all members** of the file's organisation.
- **Event enrichment** — turn a minimal inbound event into a fully-formed
  one: generate an id and timestamp, resolve the acting user's name and the
  organisation name before broadcasting.
- **Online-friends lookup** — given a user id, return the members of their
  organisations who are currently connected.
- **Authentication delegation** — the service does not decode JWTs itself; it
  forwards the token to the **auth** service (`GET auth:8000/me`) to resolve
  the current user.

---

## Architecture

The code follows a layered layout (router → service). Routers own the
HTTP/WebSocket surface and do no business logic; services own the state and
the fan-out rules; small HTTP clients isolate every outbound call to another
service.

```
realtime/
├── main.py                              # FastAPI app, registers the routers
├── Dockerfile                           # python:3.12-slim + uv, copies shared/
├── pyproject.toml / uv.lock             # dependencies (managed with uv)
└── app/
    ├── routers/
    │   ├── health.py                    # GET  /health
    │   ├── audit.py                     # WS   /audit         (client-facing)
    │   ├── events.py                    # POST /internal/events (internal)
    │   └── get_users.py                 # GET  /connected_friends (internal)
    ├── services/
    │   ├── health_service.py            # HealthService (BaseService)
    │   ├── connection_manager.py        # in-memory socket registry + broadcast
    │   ├── event_dispatcher.py          # enrich + resolve recipients + route
    │   ├── get_current_user.py          # token → user   (calls auth /me)
    │   ├── get_orgs_from_user_id.py     # user → orgs    (calls org)
    │   └── get_members_from_organisation_id.py  # org → members (calls org)
    └── schemas/
        ├── event_type.py                # EventType enum (<domain>.<action>)
        ├── event_in.py                  # EventIn  (inbound payload)
        ├── event_out.py                 # EventOut (broadcast payload)
        └── roles.py                     # Role enum (ADMIN/EDITOR/READER)
```

Shared code (`shared/base_service.py`) is copied into the image at build time
and provides the `BaseService` base class (logging, service name) used by the
health service and the connection manager.

### The two moving parts

- **`ConnectionManager`** (`connection_manager.py`, singleton `manager`) —
  the presence registry. It maps a `user_id` to a `User` holding the list of
  that user's open sockets, their name, and a first-connection timestamp.
  `connect` / `disconnect` maintain it; `broadcast_id` sends a JSON payload to
  every socket a user holds and prunes any socket that fails mid-send.

  > ⚠️ The registry lives **in memory, in a single process**. It is not
  > shared across replicas: running more than one instance of realtime would
  > split presence and break fan-out. Restarting the service drops all
  > connections and presence state.

- **`Dispatcher`** (`event_dispatcher.py`, singleton `dispatcher`) — the
  fan-out brain. `build_event_out` validates an inbound event against its
  per-type requirements and enriches it into an `EventOut`; `publish_event`
  then resolves the recipient set (querying `org`) and broadcasts through the
  `manager`.

### Request lifecycle

1. A client opens `WS /audit?token=<jwt>`. The token is validated against
   `auth`; on failure the socket is closed with code `1008`. On success the
   socket is registered with `manager`, and the handler loops as a keep-alive
   (any text it receives is echoed back).
2. Another service publishes an event via `POST /internal/events`.
3. The dispatcher enriches it, resolves recipients from `org`, and pushes the
   `EventOut` JSON to every matching socket.

---

## API reference

All routes are served on port `8000` inside the Docker network. Only the
WebSocket is reachable from the outside, through the gateway under `/ws/`
(the prefix is stripped, so `/ws/audit` maps to `/audit`). Interactive docs
are available at `/docs` (Swagger UI) and `/redoc`.

### Health

#### `GET /health`

Liveness probe.

**Response `200`**

```json
{ "status": "ok", "service": "realtime" }
```

### Audit stream (client-facing)

#### `WS /audit?token=<jwt>` — subscribe to your live events

The endpoint a browser client connects to. Externally: `/ws/audit?token=…`.

- **Authentication:** the `token` query parameter is a bearer JWT, validated
  against `auth`. If it is rejected (or `auth` is unreachable) the socket is
  closed with close code **`1008`** before any message is sent.
- **After connect:** the connection is registered under the resolved user id.
  The user is now "online" and will receive any event addressed to them.
- **Client → server:** the loop echoes back whatever text it receives; use it
  as a keep-alive/ping. No client message is required to receive events.
- **Server → client:** every delivered event is an `EventOut` JSON object
  (see [Event model](#event-model)).

Example (browser):

```js
const ws = new WebSocket(`wss://${location.host}/ws/audit?token=${jwt}`);
ws.onmessage = (e) => {
  const event = JSON.parse(e.data);
  // { event_type: "file.created", first_name: "...", org_name: "...", ... }
};
```

### Event ingestion (internal)

#### `POST /internal/events` — publish an event to be broadcast

Called **service-to-service** (core, auth). Not exposed by the gateway.

**Body** (`application/json`) — an `EventIn` (`extra="forbid"`, unknown fields
are rejected):

| Field        | Type         | Required                              |
| ------------ | ------------ | ------------------------------------- |
| `event_type` | `EventType`  | always                                |
| `user_id`    | int          | always                                |
| `first_name` | string       | auth events only                      |
| `last_name`  | string       | auth events only                      |
| `org_id`     | int          | file events only                      |
| `file_name`  | string       | file events only                      |

The required fields depend on `event_type` (see the table in
[Event model](#event-model)); they are validated by the dispatcher, not by
the schema.

**Response `202`** — the string `"OK"`. The status is `202 Accepted`: the
event is validated and dispatched within the request, but the endpoint does
not report per-recipient delivery.

**Errors:**

| Status | When                                                                    |
| ------ | ----------------------------------------------------------------------- |
| `422`  | unknown event type, or a required field for the type is missing         |
| `404`  | **file event whose `user_id` is not currently connected** (see note)    |
| `503`  | the `org` service is unreachable while resolving recipients             |

> ⚠️ A file event resolves the acting user's name from the in-memory registry
> (`manager.get_name_from_id`). If that user is **not currently online**, the
> dispatcher raises `404`. In practice the acting user is the one who just
> uploaded/edited a file, so they are normally connected — but keep it in mind
> when testing with `curl`.

**Examples:**

```jsonc
// auth.login  → delivered to the admins of the user's organisations
{ "event_type": "auth.login", "user_id": 7,
  "first_name": "Ada", "last_name": "Lovelace" }

// file.created → delivered to all members of organisation 4
{ "event_type": "file.created", "user_id": 7,
  "org_id": 4, "file_name": "report.pdf" }
```

### Presence lookup (internal)

#### `GET /connected_friends?user_id=<id>` — your online peers

Returns the members of `user_id`'s organisations who are currently connected,
de-duplicated across organisations. Each entry is a member record as returned
by the `org` service (`user_id`, `role_id`, …).

**Response `200`**

```json
[ { "user_id": 12, "role_id": 2, "...": "org member fields" } ]
```

**Errors:** `503` if `org` is unreachable, `422` on any other failure.

---

## Event model

### Event types (`EventType`)

`<domain>.<action>` strings, serialised as their value in JSON:

| Value           | Kind | Broadcast scope                                   |
| --------------- | ---- | ------------------------------------------------- |
| `auth.login`    | auth | admins of every org the user belongs to           |
| `auth.logout`   | auth | admins of every org the user belongs to           |
| `file.created`  | file | all members of `org_id`                           |
| `file.updated`  | file | all members of `org_id`                           |
| `file.deleted`  | file | all members of `org_id`                           |

### Inbound vs outbound

`EventIn` is the minimal payload a publisher sends. The dispatcher enriches it
into `EventOut`, the object broadcast to clients — it promotes the identity
fields to required, and adds server-generated metadata:

| Field        | In (`EventIn`) | Out (`EventOut`) | Notes                                   |
| ------------ | -------------- | ---------------- | --------------------------------------- |
| `event_id`   | —              | string (UUID4)   | generated server-side                   |
| `timestamp`  | —              | datetime (UTC)   | generated server-side                   |
| `event_type` | required       | required         |                                         |
| `user_id`    | optional\*     | required         | \*required at dispatch for every type   |
| `first_name` | optional       | required         | from payload (auth) or registry (file)  |
| `last_name`  | optional       | required         | from payload (auth) or registry (file)  |
| `org_id`     | optional       | optional         | required for file events                |
| `org_name`   | —              | optional         | resolved from `org` for file events     |
| `file_name`  | optional       | optional         | required for file events                |

Example `EventOut` pushed to a client:

```json
{
  "event_id": "6f1c2d0e-2a4b-4c8e-9f10-123456789abc",
  "timestamp": "2026-07-24T10:12:03.512Z",
  "event_type": "file.created",
  "user_id": 7,
  "first_name": "Ada",
  "last_name": "Lovelace",
  "org_id": 4,
  "org_name": "Analytics Team",
  "file_name": "report.pdf"
}
```

---

## Integrating with realtime (for other services)

To make connected users see something happen, `POST /internal/events` to
`http://realtime:8000/internal/events` with the matching payload — that is all.
Follow the fire-and-forget pattern used by **core**: publish asynchronously
and never let a realtime failure block or fail the originating request.

- **Publishing file events (core):** after a successful create/update/delete,
  send `file.created` / `file.updated` / `file.deleted` with `user_id` (the
  acting user), `org_id` and `file_name`.
- **Publishing auth events (auth):** on login/logout, send `auth.login` /
  `auth.logout` with `user_id`, `first_name`, `last_name`.

Recipient resolution and delivery are entirely realtime's job; publishers do
not need to know who is online or who the admins are.

---

## Configuration

The service currently has **no environment-driven settings**: the upstream
service URLs are hardcoded to their in-network hostnames.

| Upstream call                     | Target                                            |
| --------------------------------- | ------------------------------------------------- |
| token → user                      | `GET http://auth:8000/me`                         |
| user → organisations              | `GET http://org:8000/organisations/users/{id}/organisations` |
| org → members                     | `GET http://org:8000/internal/organisations/{id}/members` |
| org id → org details (name)       | `GET http://org:8000/organisations/{id}`          |

All outbound calls use a 10 s timeout and return `503` if the upstream is
unreachable. The `/ws/` WebSocket routing (including the `Upgrade`/`Connection`
headers) is configured on the gateway side (`gateway/conf/default.conf.template`).

---

## Running

### With Docker (recommended)

The service is part of the root `docker-compose.yml`:

```bash
make run          # or: docker compose up --build
```

It listens on port `8000` inside the network (`expose`, not published — the
WebSocket is reached through the gateway on `/ws/`).

### Locally

```bash
cd realtime
uv sync
uv run uvicorn main:app --reload
```

The `shared/` package must be importable (it sits at the repository root; in
Docker it is copied next to the app and `PYTHONPATH=/app`). Note that the
upstream hostnames (`auth`, `org`) only resolve inside the Docker network, so
a standalone local run cannot fully authenticate or resolve recipients.

## Code quality

The module is checked with **flake8** (default 79-char limit) and **mypy**:

```bash
flake8 main.py app/
mypy main.py app/
```
