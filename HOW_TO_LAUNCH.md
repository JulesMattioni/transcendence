# How to launch Keepr

## Prerequisites

- Docker + Docker Compose
- A `.env` file at the project root (copy `.env.example` and fill it in).

## Launch — one command

```bash
make run
```

This builds and starts the whole stack in the **dev** profile, in the foreground:

1. **postgres** starts and waits until it is healthy.
2. **migrations** runs `alembic upgrade head` — it creates/updates every table,
   then exits. Nothing to do by hand.
3. The services start once migrations have completed successfully:
   **auth, org, core, rag, realtime**, plus **vault**, **frontend**, **gateway**.

The app is reachable through the gateway:

- HTTPS: https://localhost:8443
- HTTP:  http://localhost:8080

### Other launch commands

| Command | What it does |
|---|---|
| `make run` | Build + start everything (dev profile, foreground). |
| `make up` | Same, but detached (background). |
| `make prod` | Build + start in the prod profile. |
| `make down` | Stop and remove containers + networks. |
| `make logs` | Follow the logs of all services. |
| `make ps` | Show the state of the services. |
| `make fclean` | Remove everything **including the Postgres volume** (wipes the DB). |

## Why migrations run automatically

The database schema is managed by Alembic (see [`migrations/`](migrations/README.md)).
The `migrations` service applies all committed migrations on every launch, so the
schema is always up to date without anyone running a command by hand. This is what
keeps "launch the whole project with one command" true.

- **Applying migrations** (`alembic upgrade head`) is part of launching — it runs
  automatically and is idempotent (does nothing if the DB is already up to date).
- **Generating migrations** (`alembic revision --autogenerate`) is a dev action —
  it only happens when *you* change a model, never at launch.

Migration files live in `migrations/alembic/versions/` and are **committed to git**.
When a teammate clones the repo, they already have every migration; `make run`
applies them. They never generate anything unless they change a model.

## Workflow: putting something in the database

You only touch this when you add or change an ORM model (a table or a column).

1. **Edit the model** under `<service>/app/models/` (e.g. `core/app/models/file.py`).
2. **Register a new model** (only the first time): import it in
   `migrations/models_registry.py`.
3. **Rebuild the migrations image** so it sees your updated model — the model is
   baked into the image, not mounted:
   ```bash
   docker compose build migrations
   ```
4. **Generate the migration:**
   ```bash
   make migration m="add xxx to files"
   ```
   The generated file appears in `migrations/alembic/versions/` on your machine.
5. **Re-read the generated file.** This is not optional:
   - the `create_table` / `add_column` is what you expect,
   - there is **no unexpected `drop_table` or `drop_column`**,
   - a **rename** shows up as drop + add (Alembic can't tell) — fix it by hand
     with `op.alter_column(..., new_column_name=...)` or you lose the data.
6. **Apply it** (or just `make run` again — launch applies it too):
   ```bash
   make migrate
   ```
7. **Commit the migration file** — it is source code:
   ```bash
   git add migrations/alembic/versions/
   ```

### Rolling back

```bash
make migrate-down    # undoes the last migration
```

## Inspecting the database

```bash
# list tables
docker compose exec postgres psql -U keepr -d keepr -c "\dt"

# describe a table
docker compose exec postgres psql -U keepr -d keepr -c "\d files"

# interactive shell (\dt, \d files, SELECT ..., \q to quit)
docker compose exec postgres psql -U keepr -d keepr
```

See [`migrations/README.md`](migrations/README.md) for more detail on the
migrations setup.
