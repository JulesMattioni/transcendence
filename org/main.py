from fastapi import FastAPI

from app.routers import health, simulate_auth

app = FastAPI(title="org")
app.include_router(health.router)
app.include_router(simulate_auth.router)  # sim logAUTH
