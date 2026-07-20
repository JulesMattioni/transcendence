from fastapi import FastAPI

from app.routers import health, audit

app = FastAPI(title="realtime")
app.include_router(health.router)
app.include_router(audit.router)
