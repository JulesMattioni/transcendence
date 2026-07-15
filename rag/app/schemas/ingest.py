from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    file_id: int
    organisation_id: int
    filepath: str = Field(min_length=1, max_length=1024)
    content_type: str = Field(min_length=1, max_length=100)


class IngestResponse(BaseModel):
    file_id: int
    chunks_created: int
