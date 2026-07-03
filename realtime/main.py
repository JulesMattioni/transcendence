from fastapi import FastAPI

from app.routers import health

app = FastAPI(title="realtime")
app.include_router(health.router)
