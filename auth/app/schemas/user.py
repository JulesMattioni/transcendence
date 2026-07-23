from pydantic import BaseModel, ConfigDict, EmailStr, Field


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

    first_name: str = Field(max_length=255)
    last_name: str = Field(max_length=255)
    email: EmailStr = Field(max_length=255)
    password: str


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
