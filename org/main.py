from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.routers import health, organisation

app = FastAPI(title="org")
app.include_router(health.router)
app.include_router(organisation.router)

