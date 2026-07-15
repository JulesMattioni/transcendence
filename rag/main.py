from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.services.embedding_service import embedding_service
from app.routers import health


@asynccontextmanager
async def lifespan(app: FastAPI):
    embedding_service.load()
    yield


app = FastAPI(title="rag", lifespan=lifespan)
app.include_router(health.router)
