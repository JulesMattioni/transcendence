from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.routers import health, files
from app.exceptions import FileNotFoundError, FileAccessDeniedError

app = FastAPI(title="core")
app.include_router(health.router)
app.include_router(files.router)


@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(
    request: Request, exc: FileNotFoundError
) -> JSONResponse:
    """
    Translate FileNotFoundError into an HTTP 404 response.

    Args:
        request: Incoming request that triggered the exception.
        exc: The raised FileNotFoundError.

    Returns:
        JSONResponse with status 404 and the error message as detail.
    """

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


@app.exception_handler(FileAccessDeniedError)
async def file_access_denied_handler(
    request: Request, exc: FileAccessDeniedError
) -> JSONResponse:
    """
    Translate FileAccessDeniedError into an HTTP 403 response.

    Args:
        request: Incoming request that triggered the exception.
        exc: The raised FileAccessDeniedError.

    Returns:
        JSONResponse with status 403 and the error message as detail.
    """

    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": str(exc)},
    )
