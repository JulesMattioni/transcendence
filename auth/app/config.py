import os
import secrets

SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_REDIRECT_URI = os.environ.get(
    "GOOGLE_REDIRECT_URI",
    "https://localhost:8443/api/auth/oauth/google/callback",
)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://localhost:8443")

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
    OAUTH_EXCHANGE_EXPIRE_SECONDS = int(
        os.environ.get("OAUTH_EXCHANGE_EXPIRE_SECONDS", 30)
    )
except ValueError:
    ACCESS_TOKEN_EXPIRE_MINUTES = 15
    TEMPORARY_TOKEN_EXPIRE_MINUTES = 5
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    OAUTH_EXCHANGE_EXPIRE_SECONDS = 30
