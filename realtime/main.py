"""Entry point of the realtime application.

This module builds the FastAPI instance of the "realtime" service and
registers every router that makes up its API:

- ``health``    : liveness/readiness probe (health-check) of the service;
- ``audit``     : WebSocket endpoint clients subscribe to in order to
                  receive, in real time, the events that concern them;
- ``events``    : internal HTTP endpoint through which the other services
                  publish the events to be broadcast;
- ``get_users`` : internal HTTP endpoint returning the users who are
                  currently connected (online friends).

The ``app`` object exposed here is the one loaded by the ASGI server
(for example ``uvicorn main:app``).
"""

from fastapi import FastAPI

from app.routers import health, audit, events, get_users

app = FastAPI(title="realtime")
app.include_router(health.router)
app.include_router(audit.router)
app.include_router(events.router)
app.include_router(get_users.router)
