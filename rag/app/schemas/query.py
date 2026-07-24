from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """
    A question asked against an organisation's documents.

    conversation_id ties the question to an existing conversation for
    follow-up context; when None a new conversation is started.
    """

    question: str = Field(min_length=1, max_length=2000)
    organisation_id: int
    conversation_id: int | None = None


class Source(BaseModel):
    """
    A document excerpt cited in an answer.

    excerpt is a short, truncated snippet of the chunk's content, enough
    for the client to display the citation without the full chunk.
    """

    file_id: int
    chunk_index: int
    excerpt: str


class QueryResponse(BaseModel):
    """
    A generated answer together with the sources it cites.

    sources is the ordered list of excerpts the answer's [n] markers
    refer to; it is empty when no relevant document was found.
    """

    answer: str
    sources: list[Source]
