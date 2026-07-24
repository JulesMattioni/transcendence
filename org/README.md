# org — Keepr organisations & RBAC service

The **org** service owns the organisational layer of Keepr. It manages
organisations, their members, the role each member holds
(**admin / editor / reader**), and the invitation flow that lets an admin
bring new users in. It is also the authority the other services query to
answer "who belongs to this organisation and with what role" — the input to
realtime's event fan-out and to core's file scoping.

It is a [FastAPI](https://fastapi.tiangolo.com/) application exposed inside
the Docker network on port `8000`, and reachable from the outside through the
gateway under the prefix **`/api/org/`** (e.g. `POST /api/org/organisations`).
Its `/internal/` routes are **not** proxied by the gateway (it returns `404`
for `/api/org/internal/`); they are meant for service-to-service calls over
the Docker network.

---

## Responsibilities

- **Organisations** — create, read, update and delete organisations. The
  user who creates an organisation is automatically registered as its first
  **admin**.
- **Membership & RBAC** — add or remove members, read a member's role, and
  change it. Every role-guarded route resolves the caller's role for the
  target organisation and rejects the request with `403` if it is not
  allowed. Roles are ordered **admin > editor > reader**.
- **Invitations** — an admin invites a user *by email*; the service resolves
  that email against **auth**, refuses duplicates and existing members, and
  stores a **pending** invitation. The invited user can then list, **accept**
  (which creates the membership) or **decline** it.
- **Membership lookups for other services** — expose a user's organisations
  (with roles) and an organisation's members, consumed by **realtime** to
  resolve event recipients.
- **Authentication delegation** — the service does not decode JWTs itself; it
  forwards the `Authorization` header to the **auth** service
  (`GET {AUTH_BASE_URL}/me` to resolve the caller, `GET
  {AUTH_BASE_URL}/users/by-email` to resolve an invitee).

---

## Architecture

The code follows a strict layered layout (router → service → repository →
model). Routers own the HTTP surface and the permission dependencies;
services own the business rules and the transaction boundary; only the
repositories talk SQL.

```
org/
├── main.py                          # FastAPI app, routers, exception handlers
├── Dockerfile                       # python:3.12-slim + uv, copies shared/
├── pyproject.toml / uv.lock         # dependencies + tooling (managed with uv)
└── app/
    ├── config.py                    # env-driven settings (auth base URL)
    ├── exceptions.py                # business exceptions (OrgError family)
    ├── get_user.py                  # auth calls: /me and /users/by-email
    ├── dependancies.py              # DI factories + RoleChecker guards
    ├── routers/
    │   ├── health.py                # GET  /health
    │   ├── organisation.py          # /organisations CRUD + members
    │   ├── invitation.py            # invitations: issue/list/accept/decline
    │   └── internal.py              # GET /internal/.../members (internal)
    ├── services/
    │   ├── health_service.py        # HealthService (BaseService)
    │   ├── organisation_service.py  # orgs + members orchestration
    │   └── invitation_service.py    # invitation lifecycle
    ├── repositories/                # data access, the ONLY layer that talks SQL
    │   ├── organisation_repository.py
    │   ├── member_org_repository.py
    │   └── invitation_repository.py
    ├── models/
    │   └── organisation.py          # SQLAlchemy models (3 tables)
    └── schemas/
        ├── organisation.py          # Pydantic schemas (Create/Read/Update)
        ├── roles.py                 # Role enum (ADMIN/EDITOR/READER)
        └── user.py                  # User (identity resolved from auth)
```

Shared code (`shared/base_service.py`, `shared/database.py`) is copied into
the image at build time and provides the `BaseService` base class, the
declarative `Base` and the `get_session` async-session dependency. Database
migrations are **not** handled here: they live in the top-level `migrations/`
service (shared Alembic), which runs before org starts.

### Request lifecycle & transactions

Each request builds its service through a dependency in `dependancies.py`
(one `AsyncSession` per request via `shared.database.get_session`). The
service owns the transaction boundary: repository methods only `flush`, and
the service `commit`s (or `rollback`s on failure). Multi-step operations —
creating an organisation and its first admin, or accepting an invitation and
creating the membership — commit as a single transaction.

### Roles & authorisation

Roles live in `app/schemas/roles.py` and map to the `role_id` stored on each
membership:

| Role     | `role_id` |
| -------- | --------- |
| `ADMIN`  | `1`       |
| `EDITOR` | `2`       |
| `READER` | `3`       |

`RoleChecker` (`dependancies.py`) is the guard used as a FastAPI dependency.
It reads the `{org_id}` path parameter, resolves the caller's role in that
organisation, and raises `403` unless the role is in the allowed set. Three
ready-made guards are exposed: `required_admin_role`, `required_editor_role`
and `required_reader_role` (each allows its role **and every stronger one**).

### Error handling

Business exceptions are defined in `app/exceptions.py` (all subclass
`OrgError`) and translated to HTTP responses by handlers registered in
`main.py`:

| Exception                      | HTTP status | Meaning                                    |
| ------------------------------ | ----------- | ------------------------------------------ |
| `OrganisationNotFoundError`    | `404`       | Organisation does not exist                |
| `OrgnisationCreationError`     | `400`       | Organisation could not be created          |
| `UserNotInOrganisationError`   | `404`       | Target member does not exist in the org    |
| `InvitedUserNotFoundError`     | `404`       | No user matches the invited email          |
| `AlreadyMemberError`           | `409`       | Invited user is already a member           |
| `InvitationAlreadyExistsError` | `409`       | A pending invitation already exists        |
| `InvitationNotFoundError`      | `404`       | Invitation missing, not owned, or not pending |
| `AuthServiceUnavailableError`  | `503`       | The auth service could not be reached      |

Permission failures (`RoleChecker`) return `403` directly; a missing or
invalid `Authorization` header returns `401`.

---

## API reference

All routes below are served by org on port `8000`; from the outside, prefix
them with `/api/org` (gateway). Interactive docs are available at `/docs`
(Swagger UI) and `/redoc`.

The **Auth** column indicates the guard: _public_ (no check), _authenticated_
(any valid token), or a **role** (checked against the `{org_id}` in the path).

### Health

#### `GET /health`

Liveness probe.

**Response `200`**

```json
{ "status": "ok", "service": "org" }
```

### Organisations

| Method & path                          | Auth            | Purpose                             |
| -------------------------------------- | --------------- | ----------------------------------- |
| `POST /organisations/`                 | authenticated   | create an org (caller → admin)      |
| `GET /organisations/{org_id}`          | public       | read one organisation               |
| `PATCH /organisations/{org_id}`        | admin           | rename an organisation              |
| `DELETE /organisations/{org_id}`       | admin           | delete an organisation              |

#### `POST /organisations/` — create an organisation

Requires an `Authorization` header. The caller becomes the organisation's
first member with the **admin** role.

**Body** (`application/json`): `{ "name": "Analytics Team" }`

**Response `201`** — an `OrganisationRead`:

```json
{ "id": 4, "name": "Analytics Team" }
```

**Errors:** `401` missing/invalid token, `400` creation failure.

#### `GET /organisations/{org_id}` — read an organisation

**Response `200`** — an `OrganisationRead`. **Errors:** `404` unknown org.

#### `PATCH /organisations/{org_id}` — rename (admin)

Partial update; send only the fields to change.

**Body:** `{ "name": "New name" }` → **Response `200`** the updated
`OrganisationRead`. **Errors:** `403` not admin, `404` unknown org.

#### `DELETE /organisations/{org_id}` — delete (admin)

**Response `204`** — no content. Deleting an organisation cascades to its
members and invitations (`ON DELETE CASCADE`). **Errors:** `403`, `404`.

### Members

| Method & path                                     | Auth     | Purpose                          |
| ------------------------------------------------- | -------- | -------------------------------- |
| `POST /organisations/{org_id}/users/{user_id}`    | admin    | add a member with a role         |
| `GET /organisations/{org_id}/users`               | reader+  | list members                     |
| `PATCH /organisations/{org_id}/users/{user_id}`   | admin    | change a member's role           |
| `DELETE /organisations/{org_id}/users/{user_id}`  | admin    | remove a member                  |
| `GET /organisations/users/{user_id}/organisations`| public| a user's orgs and roles          |

#### `POST /organisations/{org_id}/users/{user_id}?role_id=<n>` — add a member (admin)

Adds `user_id` to the organisation directly (bypassing the invitation flow).

**Response `201`** — the created membership.
**Errors:** `403` not admin.

#### `GET /organisations/{org_id}/users` — list members (reader+)

**Response `200`** — a list of `OrganisationMemberRead`:

```json
[ { "user_id": 7, "role_id": 1, "email": "ada@ex.com",
    "first_name": "Ada", "last_name": "Lovelace" } ]
```

**Errors:** `403` insufficient role, `404` unknown org.

#### `PATCH /organisations/{org_id}/users/{user_id}?new_role=<n>` — change role (admin)

**Response `200`** — `true` on success.
**Errors:** `403` not admin, `404` member not in the org.

#### `DELETE /organisations/{org_id}/users/{user_id}` — remove a member (admin)

**Response `204`** — no content. **Errors:** `403`, `404` member not found.

#### `GET /organisations/users/{user_id}/organisations` — a user's memberships

**Response `200`**

```json
{ "user_id": 7,
  "organisation": [ { "org_id": 4, "name": "Analytics Team", "role": 1 } ] }
```

> ⚠️ No authentication/role check (see the caveat above).

### Invitations

An admin invites a user by **email**; org resolves the email against auth,
refuses duplicates/existing members, and stores a **pending** invitation. The
invited user lists their pending invitations and accepts (→ becomes a member)
or declines.

| Method & path                                    | Auth            | Purpose                       |
| ------------------------------------------------ | --------------- | ----------------------------- |
| `POST /organisations/{org_id}/invitations`       | admin           | invite a user by email        |
| `GET /organisations/{org_id}/invitations`        | admin           | list an org's invitations     |
| `GET /invitations/me`                            | authenticated   | my pending invitations        |
| `POST /invitations/{invitation_id}/accept`       | authenticated   | accept (→ join the org)       |
| `POST /invitations/{invitation_id}/decline`      | authenticated   | decline                       |

#### `POST /organisations/{org_id}/invitations` — invite (admin)

Requires an `Authorization` header (forwarded to auth to resolve the invitee).

**Body** (`application/json`): an `InvitationCreate`

```json
{ "email": "grace@ex.com", "role_id": 2 }
```

**Response `201`** — an `InvitationRead`:

```json
{ "id": 12, "org_id": 4, "invited_user_id": 9, "email": "grace@ex.com",
  "first_name": "Grace", "last_name": "Hopper", "role_id": 2,
  "status": "pending" }
```

**Errors:** `403` not admin, `404` unknown org / unknown email, `409` already
a member or a pending invitation exists, `503` auth unavailable.

#### `GET /organisations/{org_id}/invitations` — list (admin)

**Response `200`** — a list of `InvitationRead` (any status).
**Errors:** `403` not admin.

#### `GET /invitations/me` — my pending invitations

**Response `200`** — a list of `InvitationRead` in `pending` status addressed
to the caller.

#### `POST /invitations/{invitation_id}/accept` — accept

The caller must be the invited user and the invitation must still be pending.
Accepting creates the membership with the offered role and sets the
invitation to `accepted`.

**Response `200`** — the updated `InvitationRead`.
**Errors:** `404` if the invitation is missing, not owned by the caller, or
no longer pending.

#### `POST /invitations/{invitation_id}/decline` — decline

Same ownership/state rules; sets the invitation to `declined`.

**Response `200`** — the updated `InvitationRead`. **Errors:** `404`.

> ⚠️ `PATCH` and `DELETE` are blocked by the WAF's default CRS ruleset; the
> gateway image explicitly re-allows them (see `gateway/Dockerfile`).

### Internal (service-to-service)

#### `GET /internal/organisations/{org_id}/members` — an org's members

Called by **realtime** to resolve event recipients. Not exposed through the
gateway (`/api/org/internal/` returns `404`).

**Response `200`** — a list of `OrganisationMemberRead` (same shape as
`GET /organisations/{org_id}/users`).

---

## Data model

Three tables (SQLAlchemy models in `app/models/organisation.py`, migrated by
the shared Alembic service).

Table **`organisation`**

| Column       | Type         | Notes                    |
| ------------ | ------------ | ------------------------ |
| `id`         | int, PK      | auto-generated           |
| `name`       | varchar(255) |                          |
| `created_at` | timestamptz  | server default `now()`   |

Table **`organisation_member`** — a user's membership and role in an org

| Column       | Type          | Notes                                        |
| ------------ | ------------- | -------------------------------------------- |
| `id`         | int, PK       | auto-generated                               |
| `org_id`     | int, FK       | → `organisation.id`, `ON DELETE CASCADE`     |
| `user_id`    | int, indexed  | id of the user (from auth)                   |
| `role_id`    | int           | `1` admin / `2` editor / `3` reader          |
| `email`      | varchar(255)  | nullable, denormalised from auth             |
| `first_name` | varchar(255)  | nullable                                     |
| `last_name`  | varchar(255)  | nullable                                     |

Table **`invitation`** — a pending/accepted/declined invitation

| Column            | Type         | Notes                                       |
| ----------------- | ------------ | ------------------------------------------- |
| `id`              | int, PK      | auto-generated                              |
| `org_id`          | int, FK      | → `organisation.id`, `ON DELETE CASCADE`, indexed |
| `invited_user_id` | int, indexed | id of the invited user (from auth)          |
| `email`           | varchar(255) | invited email                               |
| `first_name`      | varchar(255) | nullable                                    |
| `last_name`       | varchar(255) | nullable                                    |
| `role_id`         | int          | role offered to the invitee                 |
| `status`          | varchar(20)  | `pending` (default) / `accepted` / `declined` |
| `invited_by`      | int          | id of the issuing admin                     |
| `created_at`      | timestamptz  | server default `now()`                      |

---

## Configuration

Settings live in `app/config.py` and are read from the environment (injected
through the root `.env` via docker-compose):

| Variable        | Default            | Purpose                             |
| --------------- | ------------------ | ----------------------------------- |
| `AUTH_BASE_URL` | `http://auth:8000` | auth service, token → user and email → user resolution |

The database connection is configured by `shared/database.py` (common to all
Python services).

---

## Running

### With Docker (recommended)

The service is part of the root `docker-compose.yml`:

```bash
make run          # or: docker compose up --build
```

It waits for PostgreSQL to be healthy and for the shared `migrations` service
to complete, then listens on port `8000` inside the network (`expose`, not
published — access goes through the gateway).

### Locally

```bash
cd org
uv sync
uv run uvicorn main:app --reload
```

The `shared/` package must be importable (it sits at the repository root; in
Docker it is copied next to the app and `PYTHONPATH=/app`). The `auth`
hostname only resolves inside the Docker network, so a standalone local run
cannot authenticate or resolve invitees.

## Code quality

The module is checked with **flake8** (default 79-char limit) and **mypy**:

```bash
flake8 main.py app/
mypy main.py app/
```
