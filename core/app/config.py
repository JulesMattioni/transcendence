import os

# Root directory where uploaded binaries are stored on disk.
# In the container this points to the mounted Docker volume core_uploads.
UPLOAD_ROOT = os.environ.get("UPLOAD_ROOT", "/app/uploads")

# Maximum accepted size for a single uploaded file (100 MB).
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024

# Base URL of the rag service, called fire-and-forget after each upload
# to trigger ingestion. Overridable via env; defaults to the compose name.
RAG_BASE_URL = os.environ.get("RAG_BASE_URL", "http://rag:8000")

AUTH_BASE_URL = os.environ.get("AUTH_BASE_URL", "http://auth:8000")