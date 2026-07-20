from enum import Enum


class Role(int, str, Enum):
    ADMIN = 1,
    GUEST = 2
    MODERATOR = 3
