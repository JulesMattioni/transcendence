from enum import Enum


class EventType(str, Enum):
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    FILE_CREATED = "file.created"
    FILE_UPDATED = "file.updated"
    FILE_DELETED = "file.deleted"
