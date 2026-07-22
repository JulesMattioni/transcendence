from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.routers import health, organisation, internal
from app.exceptions import (
    OrganisationNotFoundError,
    OrgnisationCreationError,
    UserNotInOrganisationError
)

app = FastAPI(title="org")
app.include_router(health.router)
app.include_router(organisation.router)
app.include_router(internal.router)


@app.exception_handler(OrganisationNotFoundError)
async def organisation_not_found_error(
        request: Request, exc: OrganisationNotFoundError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)}
    )


@app.exception_handler(OrgnisationCreationError)
async def organisation_creation_error(
        request: Request, exc: OrgnisationCreationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )


@app.exception_handler(UserNotInOrganisationError)
async def user_not_found_error(
        request: Request, exc: UserNotInOrganisationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)}
    )
