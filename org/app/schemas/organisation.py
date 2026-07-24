"""Request and response schemas for organisations, members, invitations."""

from pydantic import BaseModel, ConfigDict


class OrganisationCreate(BaseModel):
    """Payload to create an organisation."""

    name: str


class OrganisationRead(BaseModel):
    """Public representation of an organisation."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class OrganisationUpdate(BaseModel):
    """Partial update of an organisation; unset fields are ignored."""

    name: str | None = None


class OrganisationMemberRead(BaseModel):
    """Public representation of an organisation member."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    role_id: int
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class InvitationCreate(BaseModel):
    """Payload to invite a user, identified by email, with a role."""

    email: str
    role_id: int


class InvitationRead(BaseModel):
    """Public representation of an invitation and its status."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    org_id: int
    invited_user_id: int
    email: str
    first_name: str | None = None
    last_name: str | None = None
    role_id: int
    status: str
