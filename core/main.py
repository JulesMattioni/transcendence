from fastapi import FastAPI

from app.routers import health

app = FastAPI(title="core")
app.include_router(health.router)
