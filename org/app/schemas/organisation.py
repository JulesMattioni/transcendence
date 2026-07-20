from pydantic import BaseModel, ConfigDict


class OrganisationCreate(BaseModel):
    name: str


class OrganisationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class OrganisationUpdate(BaseModel):
    pass
