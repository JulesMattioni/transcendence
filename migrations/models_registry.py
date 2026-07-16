"""Import every model so it registers on Base.metadata for autogenerate.

Add a model -> import it here -> make migration -> make migrate.
"""

from core_models.models import file  # noqa: F401  (File -> table "files")
from auth_models.models import (
    auth,
)  # noqa: F401
from rag_models.models import chunk, conversation, message  # noqa: F401
