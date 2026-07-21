from enum import StrEnum


class EventType(StrEnum):
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    FILE_CREATED = "file.created"
    FILE_UPDATED = "file.updated"
    FILE_DELETED = "file.deleted"
