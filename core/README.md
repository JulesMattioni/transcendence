# core — Keepr documents service

The **core** service is the document backbone of Keepr. It owns the upload,
storage, listing, metadata management and deletion of the files belonging to
an organisation, and it notifies the other services (RAG ingestion, realtime
events) whenever a file changes.

It is a [FastAPI](https://fastapi.tiangolo.com/) application exposed inside
the Docker network on port `8000`, and reachable from the outside through the
gateway under the prefix **`/api/core/`** (e.g. `POST /api/core/files`).

---

## Responsibilities

- **File upload** — receive multipart uploads, stream them to disk in 1 MB
  chunks, and persist their metadata in PostgreSQL.
- **File storage** — binaries are written to the `core_uploads` Docker volume
  (mounted at `/app/uploads`), partitioned by organisation
  (`org_<id>/<uuid>.<ext>`). The stored name is a random UUID so original
  filenames never touch the filesystem. File content is **immutable**: only
  metadata (title, description) can be edited after upload.
- **Metadata API** — list (paginated), read, update and delete file records,
  always scoped to an `organisation_id`.
- **Content download** — serve the raw binary back with its original filename
  and content type.
- **Cross-service notifications** (fire-and-forget, never block the request):
  - **rag** — after a successful upload, `POST {RAG_BASE_URL}/ingest` so the
    document gets chunked/embedded for the AI assistant. The `rag` service
    mounts the same `core_uploads` volume read-only and reads the file
    directly from the shared path.
  - **realtime** — after create/update/delete, `POST
    {REALTIME_BASE_URL}/internal/events` so connected clients of the
    organisation receive a live `file.created` / `file.updated` /
    `file.deleted` event.
- **Authentication delegation** — the service does not decode JWTs itself; it
  forwards the `Authorization` header to the **auth** service (`GET
  {AUTH_BASE_URL}/me`) to resolve the current user id.

---

## Architecture

The code follows a strict layered layout (router → service → repository /
storage / clients). Only the repository talks SQL; only the storage touches
the filesystem; only the clients perform outbound HTTP.

```
core/
├── main.py                          # FastAPI app, routers, exception handlers
├── Dockerfile                       # python:3.12-slim + uv, copies shared/
├── pyproject.toml / uv.lock         # dependencies (managed with uv)
└── app/
    ├── config.py                    # env-driven settings (paths, base URLs)
    ├── exceptions.py                # business exceptions (FileServiceError…)
    ├── get_user.py                  # auth dependency (calls auth /me)
    ├── routers/
    │   ├── health.py                # GET /health
    │   └── files.py                 # /files CRUD + content download
    ├── services/
    │   ├── health_service.py        # HealthService (BaseService)
    │   └── file_service.py          # FileService: orchestration + transactions
    ├── repositories/
    │   └── file_repository.py       # data access, the ONLY layer that talks SQL
    ├── storage/
    │   └── file_storage.py          # disk I/O: build_path / save / delete
    ├── clients/
    │   ├── rag_client.py            # async trigger of RAG ingestion
    │   └── realtime_client.py       # async push of file events to realtime
    ├── models/
    │   └── file.py                  # SQLAlchemy ORM model (table "files")
    └── schemas/
        └── file.py                  # Pydantic schemas (Create/Read/Update/Page)
```

Shared code (`shared/base_service.py`, `shared/database.py`) is copied into
the image at build time and provides the `BaseService` base class, the
declarative `Base` and the `get_session` async-session dependency. Database
migrations are **not** handled here: they live in the top-level `migrations/`
service (shared Alembic), which runs before core starts.

### Request lifecycle & transactions

Each request builds a `FileService` through the `get_file_service` dependency
(one `AsyncSession` per request via `shared.database.get_session`). The
service owns the transaction boundary: repository methods only `flush`, and
the service commits or rolls back. On upload, if the DB insert fails after the
binary was written, the file is removed from disk (compensation) so storage
and database never diverge.

### Error handling

Business exceptions are defined in `app/exceptions.py` and translated to HTTP
responses by handlers registered in `main.py`:

| Exception               | HTTP status | Meaning                                        |
| ----------------------- | ----------- | ---------------------------------------------- |
| `FileNotFoundError`     | `404`       | File does not exist **or** belongs to another organisation (no information leak) |
| `FileAccessDeniedError` | `403`       | The user is not allowed to act on this file    |

---

## API reference

All routes below are served by core on port `8000`; from the outside, prefix
them with `/api/core` (gateway). Interactive docs are available at `/docs`
(Swagger UI) and `/redoc`.

### Health

#### `GET /health`

Liveness probe.

**Response `200`**

```json
{ "status": "ok", "service": "core" }
```

### Files

All file routes are scoped by `organisation_id`: a file is only visible
through the organisation it belongs to. A lookup with the wrong organisation
returns `404`, never `403`, so the existence of the file is not leaked.

#### `POST /files` — upload a file

Requires an `Authorization` header (validated against the auth service; the
resolved user id becomes `owner_id`).

**Body** (`multipart/form-data`):

| Field             | Type   | Required | Constraints            |
| ----------------- | ------ | -------- | ---------------------- |
| `upload`          | file   | yes      | the binary content     |
| `title`           | string | yes      | 1–255 chars            |
| `organisation_id` | int    | yes      |                        |
| `description`     | string | no       | ≤ 512 chars            |

**Response `201`** — a `FileRead` object:

```json
{
  "id": 1,
  "title": "Q3 report",
  "filename": "report.pdf",
  "description": null,
  "organisation_id": 4,
  "content_type": "application/pdf",
  "size_bytes": 348211,
  "owner_id": 7,
  "created_at": "2026-07-23T10:12:03.512Z"
}
```

`filepath` (the internal storage path) is intentionally never exposed.

**Errors:** `401` missing/invalid token, `503` auth service unavailable,
`422` invalid form fields.

Side effects: triggers RAG ingestion and broadcasts a `file.created` realtime
event (both asynchronous; the response does not wait for them).

#### `GET /files?organisation_id=<id>&page=<n>&page_size=<n>` — list files

Paginated listing of an organisation's files, newest first (ties broken by
descending id).

**Query parameters:**

| Param             | Type | Default | Constraints |
| ----------------- | ---- | ------- | ----------- |
| `organisation_id` | int  | —       | required    |
| `page`            | int  | `1`     | ≥ 1         |
| `page_size`       | int  | `9`     | 1–100       |

**Response `200`** — a `FilePage`:

```json
{
  "items": [ { "...": "FileRead objects" } ],
  "total": 42,
  "page": 1,
  "page_size": 9
}
```

`total` is the count across all pages, so the client can compute the number
of pages.

#### `GET /files/{file_id}?organisation_id=<id>` — file metadata

**Response `200`** — a `FileRead` object.
**Errors:** `404` if the file does not exist in this organisation.

#### `GET /files/{file_id}/content?organisation_id=<id>` — download the binary

Streams the file back with its stored `content_type` and the **original**
filename as the download name (`Content-Disposition`).

**Errors:** `404` if the file does not exist in this organisation.

#### `PATCH /files/{file_id}?organisation_id=<id>` — update metadata

Partial update. The binary content is immutable — only `title` and
`description` may change. Send only the fields you want to modify.

**Body** (`application/json`):

```json
{ "title": "New title", "description": "New description" }
```

| Field         | Type           | Constraints |
| ------------- | -------------- | ----------- |
| `title`       | string \| null | 1–255 chars |
| `description` | string \| null | ≤ 512 chars |

**Response `200`** — the updated `FileRead`.
**Errors:** `404` unknown file, `422` invalid body.

Side effect: broadcasts a `file.updated` realtime event.

> ⚠️ `PATCH`/`PUT`/`DELETE` are blocked by the WAF's default CRS ruleset; the
> gateway image explicitly re-allows them (see `gateway/Dockerfile`).

#### `DELETE /files/{file_id}?organisation_id=<id>` — delete a file

Deletes the database record first (transactional), then removes the binary
from disk and broadcasts a `file.deleted` realtime event.

**Response `204`** — no content.
**Errors:** `404` unknown file.

---

## Data model

Table **`files`** (SQLAlchemy model `app/models/file.py`, migrated by the
shared Alembic service):

| Column            | Type            | Notes                                    |
| ----------------- | --------------- | ---------------------------------------- |
| `id`              | int, PK         | auto-generated                           |
| `filepath`        | varchar(1024)   | internal storage path, never exposed     |
| `title`           | varchar(255)    | user-facing title                        |
| `filename`        | varchar(255)    | original upload filename                 |
| `description`     | varchar(512)    | nullable                                 |
| `organisation_id` | int             | scoping key for all queries              |
| `content_type`    | varchar(100)    | MIME type (`application/octet-stream` fallback) |
| `size_bytes`      | int             | computed while streaming to disk         |
| `owner_id`        | int             | id of the uploading user (from auth)     |
| `created_at`      | timestamptz     | server default `now()`                   |

---

## Configuration

All settings live in `app/config.py` and are read from the environment
(injected through the root `.env` via docker-compose):

| Variable            | Default                  | Purpose                                   |
| ------------------- | ------------------------ | ----------------------------------------- |
| `UPLOAD_ROOT`       | `/app/uploads`           | root of the binary storage (the `core_uploads` volume in Docker) |
| `RAG_BASE_URL`      | `http://rag:8000`        | RAG service, ingestion trigger            |
| `AUTH_BASE_URL`     | `http://auth:8000`       | auth service, token → user resolution     |
| `REALTIME_BASE_URL` | `http://realtime:8000`   | realtime service, file event broadcast    |

`MAX_FILE_SIZE_BYTES` (100 MB) is defined alongside them as the accepted
upload ceiling.

The database connection is configured by `shared/database.py` (common to all
Python services).

---

## Running

### With Docker (recommended)

The service is part of the root `docker-compose.yml`:

```bash
make run          # or: docker compose up --build
```

It waits for PostgreSQL to be healthy, for the shared `migrations` service to
complete, and for `org` to start, then listens on port `8000` inside the
network (`expose`, not published — access goes through the gateway).

### Locally

```bash
cd core
uv sync
uv run uvicorn main:app --reload
```

The `shared/` package must be importable (it sits at the repository root; in
Docker it is copied next to the app and `PYTHONPATH=/app`).

## Code quality

The module is checked with **flake8** (default 79-char limit) and **mypy**:

```bash
flake8 main.py app/
mypy main.py app/
```
