from pydantic import BaseModel, ConfigDict


class OrganisationCreate(BaseModel):
    name: str


class OrganisationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class OrganisationUpdate(BaseModel):
    name: str | None = None


class OrganisationMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    role_id: int
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class InvitationCreate(BaseModel):
    email: str
    role_id: int


class InvitationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    org_id: int
    invited_user_id: int
    email: str
    first_name: str | None = None
    last_name: str | None = None
    role_id: int
    status: str
