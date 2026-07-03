from fastapi import FastAPI

from app.routers import health

app = FastAPI(title="org")
app.include_router(health.router)
