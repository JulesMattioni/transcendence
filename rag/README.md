# rag — Keepr AI assistant service

The **rag** service is the AI assistant of Keepr. It turns an organisation's
uploaded documents into a searchable knowledge base and answers questions
about them with a Retrieval-Augmented Generation pipeline: it ingests and
embeds documents, retrieves the passages relevant to a question, and asks a
Large Language Model to answer grounded in those passages, citing its sources.

It is a [FastAPI](https://fastapi.tiangolo.com/) application exposed inside
the Docker network on port `8000`, and reachable from the outside through the
gateway under the prefix **`/api/rag/`** (e.g. `POST /api/rag/query/stream`).

---

## Responsibilities

- **Document ingestion** — triggered by the **core** service after an upload
  (`POST /ingest`). The file is read from the `core_uploads` volume (mounted
  read-only), its text is extracted (PDF via `pypdf`, `text/*` decoded as
  UTF-8), split into overlapping chunks, embedded, and stored in PostgreSQL
  (`pgvector`). Ingestion is **idempotent**: a file's previous chunks are
  deleted before the new ones are written, so re-uploading never leaves stale
  data.
- **Retrieval** — for a question, a hybrid pipeline widens and sharpens the
  search:
  - **query expansion** — the LLM produces alternative phrasings plus a
    hypothetical answer paragraph (HyDE) to improve recall;
  - **vector search** — each expanded query is matched by cosine distance
    against the organisation's chunks (`pgvector`);
  - **reciprocal rank fusion (RRF)** — the ranked lists are merged into one
    candidate set;
  - **cross-encoder rerank** — candidates are re-scored by relevance and the
    best `TOP_K` are kept.
- **Answer generation** — the selected excerpts are sent to an
  OpenAI-compatible chat model with a grounding system prompt; the answer
  cites the excerpts with `[1]`, `[2]` markers. Available both as a one-shot
  response (`POST /query`) and as a token-by-token **SSE stream**
  (`POST /query/stream`).
- **Conversations** — the streaming endpoint persists the exchange
  (conversations + messages) so follow-up questions have context. Older turns
  are summarised and follow-ups are rewritten into standalone questions before
  retrieval. Conversations are managed through a small CRUD API, always scoped
  to their owner.
- **Provider resilience** — the LLM client works with any OpenAI-compatible
  API (Groq, OpenRouter, …), manages a pool of API keys, rotates on rate
  limits, marks rejected keys dead, and backs off on transient errors.
- **Authentication delegation** — the service does not decode JWTs itself; it
  forwards the `Authorization` header to the **auth** service
  (`GET {AUTH_BASE_URL}/me`) to resolve the current user id.

---

## Architecture

The code follows a strict layered layout (router → service → repository /
storage). Only the repository talks SQL; only the storage touches the
filesystem; only the LLM client performs outbound HTTP to the model provider.

```
rag/
├── main.py                          # FastAPI app, routers, model warm-up (lifespan)
├── Dockerfile                       # python:3.12-slim + uv, copies shared/
├── pyproject.toml / uv.lock         # dependencies (managed with uv)
└── app/
    ├── config.py                    # env-driven settings + prompts + tuning constants
    ├── exceptions.py                # business exceptions (UnsupportedFileType)
    ├── get_user.py                  # auth dependency (calls auth /me)
    ├── routers/
    │   ├── health.py                # GET /health
    │   ├── ingest.py                # POST /ingest
    │   ├── query.py                 # POST /query and POST /query/stream (SSE)
    │   └── conversation.py          # /conversations CRUD
    ├── services/
    │   ├── health_service.py        # HealthService (BaseService)
    │   ├── embedding_service.py     # bi-encoder embeddings (loaded once)
    │   ├── rerank_service.py        # cross-encoder rerank (loaded once)
    │   ├── ingest_service.py        # extract → chunk → embed → persist
    │   ├── query_service.py         # RAG pipeline: expand/retrieve/fuse/rerank/answer
    │   ├── conversation_service.py  # conversation & message lifecycle + transactions
    │   └── llm/
    │       ├── openai_compatible_service.py  # chat client (retries, key rotation)
    │       ├── key_manager.py       # API-key pool (rotation, dead-key tracking)
    │       └── model.py             # LlmResponse (content + token usage)
    ├── repositories/
    │   ├── chunk_repository.py      # chunk persistence + vector search (talks SQL)
    │   └── conversation_repository.py  # conversation & message persistence (talks SQL)
    ├── storage/
    │   └── reader_storage.py        # read-only access to the shared uploads volume
    ├── models/
    │   ├── chunk.py                 # ORM model (table "chunks", pgvector column)
    │   ├── conversation.py          # ORM model (table "conversations")
    │   └── message.py               # ORM model (table "messages")
    └── schemas/
        ├── ingest.py                # Pydantic schemas (IngestRequest/Response)
        ├── query.py                 # Pydantic schemas (QueryRequest/Response/Source)
        └── conversation.py          # Pydantic schemas (Create/Read/Detail/MessageRead)
```

Shared code (`shared/base_service.py`, `shared/database.py`) is copied into
the image at build time and provides the `BaseService` base class, the
declarative `Base` and the `get_session` async-session dependency. Database
migrations are **not** handled here: they live in the top-level `migrations/`
service (shared Alembic), which runs before rag starts and creates the
`vector` extension and the `chunks` / `conversations` / `messages` tables.

### Model warm-up

The embedding and rerank models are heavy to load, so they are loaded **once**
at application startup through the FastAPI `lifespan` (`main.py`) and reused
process-wide via the module-level `embedding_service` / `rerank_service`
singletons. Requests never pay the load cost.

### Request lifecycle & transactions

Each request builds its service through a `get_*_service` dependency (one
`AsyncSession` per request via `shared.database.get_session`). The service
owns the transaction boundary: repository methods only `flush`, and the
service commits or rolls back. Ingestion runs the "delete old chunks + insert
new chunks" pair in a single transaction so a file is never left partially
re-indexed.

### Error handling

Business exceptions are translated to HTTP responses inside the routers:

| Exception                    | HTTP status | Meaning                                          |
| ---------------------------- | ----------- | ------------------------------------------------ |
| `UnsupportedFileType`        | `415`       | The file's content type cannot be decoded to text |
| `FileNotFoundError`          | `404`       | The binary is missing from the shared uploads volume |
| `ConversationNotFoundError`  | `404`       | Conversation does not exist **or** belongs to another user/organisation (no information leak) |

---

## API reference

All routes below are served by rag on port `8000`; from the outside, prefix
them with `/api/rag` (gateway). Interactive docs are available at `/docs`
(Swagger UI) and `/redoc`.

### Health

#### `GET /health`

Liveness probe.

**Response `200`**

```json
{ "status": "ok", "service": "rag" }
```

### Ingest

#### `POST /ingest` — ingest a document

Called by the **core** service after a successful upload (internal, not meant
for end users). Extracts, chunks, embeds and stores the file's content;
replaces any previous chunks for the same file.

**Body** (`application/json`):

| Field             | Type   | Required | Constraints  |
| ----------------- | ------ | -------- | ------------ |
| `file_id`         | int    | yes      |              |
| `organisation_id` | int    | yes      |              |
| `filepath`        | string | yes      | 1–1024 chars |
| `content_type`    | string | yes      | 1–100 chars  |

**Response `200`** — an `IngestResponse`:

```json
{ "file_id": 1, "chunks_created": 12 }
```

`chunks_created` is `0` when the file yields no extractable text.

**Errors:** `415` unsupported content type, `404` binary missing from storage,
`422` invalid body.

### Query

#### `POST /query` — one-shot answer

Answers a question against an organisation's documents and returns the full
response at once (no conversation history).

**Body** (`application/json`):

| Field             | Type | Required | Constraints  |
| ----------------- | ---- | -------- | ------------ |
| `question`        | string | yes    | 1–2000 chars |
| `organisation_id` | int    | yes    |              |
| `conversation_id` | int \| null | no |              |

**Response `200`** — a `QueryResponse`:

```json
{
  "answer": "The agent is evaluated on … [1] … [2].",
  "sources": [
    { "file_id": 3, "chunk_index": 7, "excerpt": "…" },
    { "file_id": 3, "chunk_index": 8, "excerpt": "…" }
  ]
}
```

When no relevant document is found, `answer` is a fixed no-document message
and `sources` is empty. The `[n]` markers in `answer` line up with the order
of `sources`.

#### `POST /query/stream` — streamed answer (SSE)

Answers as a **Server-Sent Events** stream and persists the exchange.
Resolves or creates the conversation (a new one is titled after the first
question), loads prior messages as context, records the user's question, and
streams the answer token by token. The full assistant answer and its sources
are saved once the stream completes.

Requires an `Authorization` header (validated against the auth service; the
resolved user id owns the conversation).

**Body:** same shape as `POST /query`. Pass `conversation_id` to continue an
existing conversation; omit it to start a new one.

**Response `200`** (`text/event-stream`) — a sequence of frames:

| Event          | Data                                  | When            |
| -------------- | ------------------------------------- | --------------- |
| `conversation` | `{ "conversation_id": <id> }`         | once, first     |
| `sources`      | `{ "sources": [ Source, … ] }`        | once, before tokens |
| `token`        | `{ "text": "<fragment>" }`            | repeated        |
| `done`         | `{}`                                  | once, last      |

**Errors:** `401` missing/invalid token, `503` auth service unavailable,
`404` unknown `conversation_id` for this user/organisation.

### Conversations

All conversation routes require an `Authorization` header and are scoped to
their owner: a conversation belonging to another user or organisation returns
`404`, never `403`, so its existence is not leaked.

#### `POST /conversations` — create a conversation

**Body** (`application/json`):

| Field             | Type   | Constraints |
| ----------------- | ------ | ----------- |
| `organisation_id` | int    | required    |
| `title`           | string | 1–255 chars |

**Response `201`** — a `ConversationRead`:

```json
{
  "id": 1,
  "organisation_id": 4,
  "user_id": 7,
  "title": "Benchmarks",
  "created_at": "2026-07-24T10:12:03.512Z"
}
```

#### `GET /conversations?organisation_id=<id>` — list conversations

Lists the authenticated user's conversations in an organisation, newest first.

**Response `200`** — a list of `ConversationRead`.

#### `GET /conversations/{conversation_id}?organisation_id=<id>` — full history

**Response `200`** — a `ConversationDetail` (a `ConversationRead` plus its
ordered `messages`):

```json
{
  "id": 1,
  "organisation_id": 4,
  "user_id": 7,
  "title": "Benchmarks",
  "created_at": "2026-07-24T10:12:03.512Z",
  "messages": [
    { "id": 1, "role": "user", "content": "…", "sources": null, "created_at": "…" },
    { "id": 2, "role": "assistant", "content": "…", "sources": [ Source, … ], "created_at": "…" }
  ]
}
```

**Errors:** `404` unknown conversation for this user/organisation.

#### `DELETE /conversations/{conversation_id}?organisation_id=<id>` — delete

Deletes the conversation; its messages cascade in the database.

**Response `204`** — no content.
**Errors:** `404` unknown conversation for this user/organisation.

> ⚠️ `PATCH`/`PUT`/`DELETE` are blocked by the WAF's default CRS ruleset; the
> gateway image explicitly re-allows them (see `gateway/Dockerfile`).

---

## Data model

Migrated by the shared Alembic service (which also creates the `vector`
extension).

Table **`chunks`** (`app/models/chunk.py`):

| Column            | Type          | Notes                                     |
| ----------------- | ------------- | ----------------------------------------- |
| `id`              | int, PK       | auto-generated                            |
| `file_id`         | int, indexed  | source file (from core)                   |
| `organisation_id` | int, indexed  | scoping key for retrieval                 |
| `chunk_index`     | int           | position of the chunk within the file     |
| `content`         | text          | the chunk's text                          |
| `embedding`       | vector(384)   | normalized embedding (`pgvector`)         |
| `created_at`      | timestamptz   | server default `now()`                    |

Table **`conversations`** (`app/models/conversation.py`):

| Column            | Type          | Notes                                     |
| ----------------- | ------------- | ----------------------------------------- |
| `id`              | int, PK       | auto-generated                            |
| `organisation_id` | int, indexed  | scoping key                               |
| `user_id`         | int, indexed  | owner (from auth)                         |
| `title`           | varchar(255)  | truncated to `CONV_TITLE_MAX_LEN`         |
| `created_at`      | timestamptz   | server default `now()`                    |

Table **`messages`** (`app/models/message.py`):

| Column            | Type          | Notes                                     |
| ----------------- | ------------- | ----------------------------------------- |
| `id`              | int, PK       | auto-generated                            |
| `conversation_id` | int, indexed  | FK → `conversations.id`, `ON DELETE CASCADE` |
| `role`            | varchar(20)   | `"user"` or `"assistant"`                 |
| `content`         | text          | message text                              |
| `sources`         | jsonb, null   | cited excerpts for an assistant message   |
| `created_at`      | timestamptz   | server default `now()`                    |

---

## Configuration

Settings, prompts and tuning constants live in `app/config.py`. The
environment values are injected through the root `.env` via docker-compose:

| Variable         | Default                            | Purpose                                   |
| ---------------- | ---------------------------------- | ----------------------------------------- |
| `GROQ_BASE_URL`  | `https://api.groq.com/openai/v1`   | OpenAI-compatible chat endpoint           |
| `GROQ_MODEL`     | `llama-3.3-70b-versatile`          | model identifier sent on each request     |
| `AUTH_BASE_URL`  | `http://auth:8000`                 | auth service, token → user resolution     |

**LLM API keys** are read by `app/services/llm/key_manager.py`, which merges
two sources into one provider-agnostic pool: `API_KEYS` (comma-separated) and
any standard `*_API_KEY` variable (e.g. `GROQ_API_KEY`, `OPENROUTER_API_KEY`,
each itself possibly comma-separated). A key rejected by the provider
(`401`/`403`) is marked dead for the rest of the run.

Key tuning constants (also in `config.py`): `CHUNK_SIZE` / `CHUNK_OVERLAP`
(chunking), `TOP_K` / `RERANK_CANDIDATES` / `RRF_K` (retrieval),
`HISTORY_RAW_LIMIT` (how many recent turns are kept verbatim before older ones
are summarised), `EXCERPT_MAX_CHARS` (source snippet length). The embedding
and rerank model names are pinned there as well.

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
complete, and for `org` and `core` to start, then listens on port `8000`
inside the network (`expose`, not published — access goes through the
gateway). It mounts the `core_uploads` volume **read-only** at `/app/uploads`
to read documents that core has stored.

> Inference runs on CPU on the 42 workstation, so `torch` is pulled from the
> CPU-only PyTorch index (see `pyproject.toml`) to avoid the multi-gigabyte
> CUDA wheels. The first startup also downloads the embedding and rerank
> models.

### Locally

```bash
cd rag
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

