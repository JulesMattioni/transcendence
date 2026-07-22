import os

AUTH_BASE_URL = os.environ.get("AUTH_BASE_URL", "http://auth:8000")

INTERNAL_SERVICE_SECRET = os.environ.get("INTERNAL_SERVICE_SECRET", "")
