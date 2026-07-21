import os
import secrets

SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = os.environ.get("ALGORITHM", "HS256")

try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(
        os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 15)
    )
    TEMPORARY_TOKEN_EXPIRE_MINUTES = int(
        os.environ.get("TEMPORARY_TOKEN_EXPIRE_MINUTES", 5)
    )
    REFRESH_TOKEN_EXPIRE_DAYS = int(
        os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", 7)
    )
except ValueError:
    ACCESS_TOKEN_EXPIRE_MINUTES = 15
    TEMPORARY_TOKEN_EXPIRE_MINUTES = 5
    REFRESH_TOKEN_EXPIRE_DAYS = 7
