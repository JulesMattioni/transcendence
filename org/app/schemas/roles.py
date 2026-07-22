from enum import Enum


class Role(int, Enum):
    ADMIN = 1
    EDITOR = 2
    READER = 3
