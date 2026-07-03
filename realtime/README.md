# realtime

> _README to be completed at the end of the project (see `MODULE.md` for the module work notes)._

SecureVault real-time service (WebSockets: presence & live audit feed).

## Setup

```bash
uv sync
uv run uvicorn main:app --reload
```

## Endpoints

- `GET /health` — health check.
