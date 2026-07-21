# Transcendence / Keepr

_A secure, multi-tenant document vault with a built-in AI assistant — 42 School's `ft_transcendence`, built as a modular web application._

> **⚠️ Work in progress.** This project is under active development. Some
> features are complete, others are partial or still being wired together.
> See [Project status](#project-status) below.

## What it does

Keepr is a team document vault. An organisation stores its documents, access is
controlled by role, every action is streamed to a live audit feed, and an
**AI assistant (RAG)** answers questions grounded in the organisation's own
documents — with source citations.

Typical flow:

1. A user signs up (email/password), optionally enables **2FA (TOTP)**, or logs
   in through **OAuth** (Google / 42).
2. They create an **organisation** and invite colleagues with a **role**
   (admin / editor / reader).
3. Members upload **documents** into the organisation's shared space.
4. **Role-based access control (RBAC)** decides who can see or change what.
5. A **real-time audit feed** (WebSockets) shows who did what.
6. Members ask the **RAG assistant** questions about the organisation's content;
   answers are built only from the documents they can access, and every answer
   cites its sources.

The link between the documents and the RAG assistant is the heart of the
product: uploading a document automatically ingests it into the AI pipeline, so
what you store is immediately what you can ask about.

## Architecture

A single HTTPS entrypoint (**gateway**: Nginx + ModSecurity WAF) routes to
decoupled backend services. The database and its schema are shared across
services and managed by a dedicated migrations service.

```
                         ┌───────────────────────────┐
   Browser  ──HTTPS──▶   │  gateway (Nginx + WAF/TLS) │
                         └─────────────┬─────────────┘
                                       │
        ┌──────────┬──────────┬────────┼────────┬──────────┐
        ▼          ▼          ▼        ▼        ▼          ▼
     frontend    auth        org      core     rag      realtime
     (React)   (FastAPI)  (FastAPI)(FastAPI)(FastAPI)  (FastAPI/WS)
                                       │        │
                                       ▼        ▼
                          PostgreSQL 16 + pgvector   ◀── migrations (Alembic)
                                       ▲
                                 Vault (secrets)
```

| Service       | Responsibility                                                        |
| ------------- | --------------------------------------------------------------------- |
| **gateway**   | Reverse proxy, TLS termination, WAF (OWASP Core Rule Set / ModSecurity)|
| **auth**      | Sign-up / login, JWT (access + refresh), 2FA (TOTP), OAuth            |
| **org**       | Organisations, members, roles (RBAC)                                  |
| **core**      | Document management: upload, storage, metadata                        |
| **rag**       | AI pipeline: ingestion, embeddings, retrieval, generation            |
| **realtime**  | Live audit feed over WebSockets                                       |
| **frontend**  | React single-page app                                                 |
| **migrations**| Dedicated Alembic service; applies the shared DB schema on every launch|

## Tech stack

| Layer            | Choice                                                             |
| ---------------- | ----------------------------------------------------------------- |
| Frontend         | React 19, Vite, TypeScript (strict), Tailwind CSS                 |
| Backend          | Python, FastAPI (async)                                           |
| ORM / migrations | SQLAlchemy, Alembic                                              |
| Database         | PostgreSQL 16 + **pgvector** (vector search)                     |
| AI / RAG         | sentence-transformers (embeddings), LangChain text splitters, RRF fusion, cross-encoder re-ranking, OpenAI-compatible LLM (streaming) |
| Real-time        | WebSockets, Server-Sent Events (chat streaming)                 |
| Gateway / security | Nginx, ModSecurity + OWASP CRS, HashiCorp Vault                |
| Containerisation | Docker, Docker Compose (dev / prod profiles)                     |

## Getting started

### Prerequisites

- Docker + Docker Compose
- A `.env` file at the project root — copy `.env.example` and fill it in:

  ```bash
  cp .env.example .env
  ```

### Launch — one command

```bash
make run
```

This builds and starts the whole stack in the **dev** profile (foreground):

1. **postgres** starts and waits until it is healthy.
2. **migrations** runs `alembic upgrade head`, creating/updating every table,
   then exits — nothing to run by hand.
3. The services start once migrations complete: **auth, org, core, rag,
   realtime**, plus **vault**, **frontend**, **gateway**.

The app is then reachable through the gateway:

- HTTPS: <https://localhost:8443>
- HTTP: <http://localhost:8080>

### Common commands

| Command      | What it does                                                    |
| ------------ | --------------------------------------------------------------- |
| `make run`   | Build + start everything (dev profile, foreground).            |
| `make up`    | Same, but detached (background).                               |
| `make prod`  | Build + start in the prod profile.                            |
| `make down`  | Stop and remove containers + networks.                        |
| `make logs`  | Follow the logs of all services.                              |
| `make ps`    | Show the state of the services.                               |
| `make fclean`| Remove everything **including the Postgres volume** (wipes DB).|

`make run` also generates a self-signed TLS certificate and clones the OWASP
Core Rule Set for the gateway on first use.

## Project status

Keepr is a **work in progress**. The overall architecture, the document/RAG
core, and the frontend shell are in place; several modules (RBAC enforcement,
realtime audit wiring, GDPR export) are partial or ongoing. Expect breaking
changes.

## Documentation

- **[docs/DEV_DOC.md](docs/DEV_DOC.md)** — developer guide: launch details and
  the database migration workflow.
- **[migrations/README.md](migrations/README.md)** — how the shared Alembic
  migrations work.

## Repository layout

```
.
├── gateway/       # Nginx + ModSecurity (WAF), TLS
├── auth/          # FastAPI — auth, JWT, 2FA, OAuth
├── org/           # FastAPI — organisations, RBAC
├── core/          # FastAPI — documents, upload, storage
├── rag/           # FastAPI — ingestion, embeddings, retrieval, generation
├── realtime/      # FastAPI — WebSockets (live audit)
├── frontend/      # React + Vite + TypeScript + Tailwind CSS
├── migrations/    # Shared Alembic migrations (dedicated service)
├── shared/        # Code shared across services (Base, DB engine, ...)
├── docs/          # Project documentation
├── docker-compose.yml
├── Makefile
└── .env.example
```
