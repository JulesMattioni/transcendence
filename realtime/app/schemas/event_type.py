"""Event types handled by the realtime service."""

from enum import Enum


class EventType(str, Enum):
    """Event categories in ``<domain>.<action>`` string form.

    Subclassing :class:`str` lets each member serialise as its value
    (e.g. ``"auth.login"``) in the JSON exchanged between services.
    """

    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    FILE_CREATED = "file.created"
    FILE_UPDATED = "file.updated"
    FILE_DELETED = "file.deleted"
