from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.services.embedding_service import embedding_service
from app.routers import health, ingest, query


@asynccontextmanager
async def lifespan(app: FastAPI):
    embedding_service.load()
    yield


app = FastAPI(title="rag", lifespan=lifespan)
app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(query.router)
