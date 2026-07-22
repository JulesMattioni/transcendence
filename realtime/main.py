from fastapi import FastAPI

from app.routers import health, audit, events

app = FastAPI(title="realtime")
app.include_router(health.router)
app.include_router(audit.router)
app.include_router(events.router)
