# Migrations

Shared [Alembic](https://alembic.sqlalchemy.org/) migrations for the whole
Keepr Postgres database. **One migration chain for every service** — not
one per service — because the database is shared and foreign keys will cross
service boundaries (e.g. `files.owner_id -> users.id`).

## How it works

- All ORM models inherit from the shared `Base` in `shared/database.py`.
- `models_registry.py` imports every model so it registers on `Base.metadata`.
- `alembic/env.py` reuses the shared `Base` and async `engine` (no hard-coded
  URL) and compares the models against the live database to generate migrations.
- The `migrations` Docker service runs `alembic upgrade head` on every `make up`,
  so the schema is always applied automatically. Nobody has to run migrations by
  hand just to launch the project.

## Namespace note

Each service ships its own `app/` package. To avoid collisions inside the
migrations image, the Dockerfile copies each one under a distinct top-level name:

- `core/app/` -> `core_models/`
- `auth/app/` -> `auth_models/` (uncomment in the Dockerfile when auth has models)

## Adding or changing a model

1. Edit or create the model under `<service>/app/models/`.
2. Import it in `models_registry.py` (once, if it is a new model).
3. Rebuild the migrations image so it sees the updated model:
   ```
   docker compose build migrations
   ```
4. Generate the migration:
   ```
   make migration m="describe the change"
   ```
5. **Re-read the generated file** in `alembic/versions/`:
   - the `create_table` / `add_column` matches what you expect,
   - there is **no unexpected `drop_table` or `drop_column`**,
   - a rename shows up as drop+add — fix it by hand with `op.alter_column`
     to avoid losing data.
6. Apply it:
   ```
   make migrate
   ```
7. Commit the generated file — it is source code:
   ```
   git add migrations/alembic/versions/
   ```

## Commands

| Command | What it does |
|---|---|
| `make migration m="..."` | Generate a migration from model changes (DEV). |
| `make migrate` | Apply pending migrations (also runs automatically on `make up`). |
| `make migrate-down` | Roll back the last migration. |

## Inspecting the database

```bash
docker compose exec postgres psql -U keepr -d keepr -c "\dt"
docker compose exec postgres psql -U keepr -d keepr -c "\d files"
```
