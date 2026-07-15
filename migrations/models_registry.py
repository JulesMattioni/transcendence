"""Import every model so it registers on Base.metadata for autogenerate.

Add a model -> import it here -> make migration -> make migrate.
"""

from core_models.models import file  # noqa: F401  (File -> table "files")
from auth_models.models import (
    user,
)  # noqa: F401  (File -> table "users, tokens")
from rag_models.models import chunk  # noqa: F401  (Chunk -> table "chunks")
