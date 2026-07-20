from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    organisation_id: int
    conversation_id: int | None = None


class Source(BaseModel):
    file_id: int
    chunk_index: int
    excerpt: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]
