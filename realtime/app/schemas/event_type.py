from enum import StrEnum


class EventType(StrEnum):
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    FILE_CREATED = "file.created"
    FILE_ACCESSED = "file.accessed"
    FILE_UPDATED = "file.updated"
    FILE_DELETED = "file.deleted"
    ROLE_CHANGED = "role.changed"
    PRESENCE_ONLINE = "presence.online"
    PRESENCE_OFFLINE = "presence.offline"


