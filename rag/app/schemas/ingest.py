from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    """
    Ingestion request sent by the core service after an upload.

    filepath points to the binary on the uploads volume shared with core;
    content_type drives which extractor is used to read the text.
    """

    file_id: int
    organisation_id: int
    filepath: str = Field(min_length=1, max_length=1024)
    content_type: str = Field(min_length=1, max_length=100)


class IngestResponse(BaseModel):
    """
    Result of an ingestion, returned to the caller.

    chunks_created is how many embedded chunks were persisted for the
    file; it is 0 when the file yielded no text.
    """

    file_id: int
    chunks_created: int
