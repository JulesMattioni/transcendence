from fastapi import FastAPI

from app.routers import health

app = FastAPI(title="rag")
app.include_router(health.router)
