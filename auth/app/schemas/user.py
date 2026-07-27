from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.core.password_policy import (
    validate_password_length,
    validate_password_strength,
)


class UserCreate(BaseModel):
    """
    Request body to register a new user.

    Attributes:
        first_name: User's first name.
        last_name: User's last name.
        email: User's email address, used for login.
        password: Plaintext password to hash and store.
    """

    model_config = ConfigDict(from_attributes=True)

    first_name: str = Field(min_length=1, max_length=255)
    last_name: str = Field(min_length=1, max_length=255)
    email: EmailStr = Field(max_length=255)
    password: str

    @field_validator("password")
    @classmethod
    def check_password_strength(cls, value: str) -> str:
        """
        Enforce the registration password rules server-side.

        Args:
            value: Plaintext password submitted by the client.

        Returns:
            The password unchanged when it satisfies every rule.

        Raises:
            ValueError: When any strength rule is unmet; FastAPI turns it
            into a 422 response.
        """

        return validate_password_strength(value)


class UserRead(BaseModel):
    """
    Public profile data of a user.

    Attributes:
        id: User's ID.
        first_name: User's first name.
        last_name: User's last name.
        email: User's email address.
        location: User's location, if set.
        avatar_id: ID of the user's selected avatar.
        is_2fa_enabled: Whether two-factor authentication is enabled.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    email: EmailStr
    location: str | None
    avatar_id: int
    is_2fa_enabled: bool


class UserLogin(BaseModel):
    """
    Request body to authenticate with email and password.

    Attributes:
        email: User's email address.
        password: User's plaintext password.
    """

    model_config = ConfigDict(from_attributes=True)

    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def check_password_length(cls, value: str) -> str:
        """
        Reject empty or over-long passwords before hashing.

        Only the bounds are enforced at login: applying the strength
        rules here would lock out accounts created before those rules
        existed, and would tell an attacker which passwords are plausible.

        Args:
            value: Plaintext password submitted by the client.

        Returns:
            The password unchanged when it fits the accepted bounds.

        Raises:
            ValueError: When the password is empty or exceeds bcrypt's
            72-byte limit.
        """

        return validate_password_length(value)


class UserUpdate(BaseModel):
    """
    Request body to update a user's profile.

    Attributes:
        location: New location value.
        avatar_id: ID of the new avatar.
    """

    model_config = ConfigDict(from_attributes=True)

    location: str
    avatar_id: int


class UserLookup(BaseModel):
    """
    Minimal public information about a user, used for lookups.

    Attributes:
        id: User's ID.
        email: User's email address.
        first_name: User's first name.
        last_name: User's last name.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    first_name: str
    last_name: str
