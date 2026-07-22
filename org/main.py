from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.routers import health, organisation, internal, invitation
from app.exceptions import (
    OrganisationNotFoundError,
    OrgnisationCreationError,
    UserNotInOrganisationError,
    InvitedUserNotFoundError,
    AuthServiceUnavailableError,
    AlreadyMemberError,
    InvitationAlreadyExistsError,
    InvitationNotFoundError,
)

app = FastAPI(title="org")
app.include_router(health.router)
app.include_router(organisation.router)
app.include_router(internal.router)
app.include_router(invitation.router)


@app.exception_handler(OrganisationNotFoundError)
async def organisation_not_found_error(
    request: Request, exc: OrganisationNotFoundError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)}
    )


@app.exception_handler(OrgnisationCreationError)
async def organisation_creation_error(
    request: Request, exc: OrgnisationCreationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)}
    )


@app.exception_handler(UserNotInOrganisationError)
async def user_not_found_error(
    request: Request, exc: UserNotInOrganisationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)}
    )


@app.exception_handler(InvitedUserNotFoundError)
async def invited_user_not_found_error(
    request: Request, exc: InvitedUserNotFoundError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "No user with this email"},
    )


@app.exception_handler(AlreadyMemberError)
async def already_member_error(
    request: Request, exc: AlreadyMemberError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "User is already a member of this organisation"},
    )


@app.exception_handler(InvitationAlreadyExistsError)
async def invitation_already_exists_error(
    request: Request, exc: InvitationAlreadyExistsError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "A pending invitation already exists"},
    )


@app.exception_handler(InvitationNotFoundError)
async def invitation_not_found_error(
    request: Request, exc: InvitationNotFoundError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Invitation not found"},
    )


@app.exception_handler(AuthServiceUnavailableError)
async def auth_service_unavailable_error(
    request: Request, exc: AuthServiceUnavailableError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Auth service unavailable"},
    )
