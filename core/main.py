from fastapi import FastAPI

from app.routers import health, files

app = FastAPI(title="core")
app.include_router(health.router)
app.include_router(files.router)
