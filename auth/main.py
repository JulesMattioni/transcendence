from fastapi import FastAPI

from app.routers import health

app = FastAPI(title="auth")
app.include_router(health.router)
