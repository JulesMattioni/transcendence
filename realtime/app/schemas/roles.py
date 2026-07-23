"""Membership roles inside an organisation."""

from enum import Enum


class Role(int, Enum):
    """Role of a user within an organisation.

    Values mirror the ``role_id`` returned by the ``org`` service, so a
    member can be compared directly against the raw payload.
    """

    ADMIN = 1
    EDITOR = 2
    READER = 3
