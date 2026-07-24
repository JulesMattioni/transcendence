from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class FileCreate(BaseModel):
    """
    Metadata sent by the client when creating a file.

    Technical fields (filepath, size_bytes, content_type, filename) are
    filled in by the service from the uploaded binary, not by the client.
    owner_id comes from the authenticated user, not from the body.
    """

    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=512)
    organisation_id: int


class FileRead(BaseModel):
    """
    What the API returns to the client.

    Reads its values directly from the ORM object (from_attributes).
    filepath is intentionally NOT exposed: it is an internal storage
    path and has no meaning for the client.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    filename: str
    description: str | None
    organisation_id: int
    content_type: str
    size_bytes: int
    owner_id: int
    created_at: datetime


class FileUpdate(BaseModel):
    """
    Partial update of a file's metadata.

    The binary content is immutable, so only title and description can
    change. Every field is optional: the client sends only what it wants
    to modify.
    """

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=512)


class FilePage(BaseModel):
    """
    A single page of files plus the total count.

    total is the number of files matching the query (all pages combined),
    so the client can compute how many pages exist.
    """

    items: list[FileRead]
    total: int
    page: int
    page_size: int


class FileTypeStat(BaseModel):
    """
    File count and storage for one human-readable file category.

    category is a coarse group (image, pdf, document, video, audio,
    archive, other) derived from raw MIME types by the service, so the
    client can render a legible chart instead of dozens of MIME strings.
    """

    category: str
    file_count: int
    total_bytes: int


class FileBucketStat(BaseModel):
    """
    Number of files uploaded during one fixed-width time bucket.

    bucket_start is the ISO timestamp of the bucket's first instant
    (15-minute bins), letting the client plot an uploads-over-time
    series without re-bucketing timestamps itself. Buckets form a
    continuous series: empty intervals are present with a count of 0.
    """

    bucket_start: str
    file_count: int


class FileStats(BaseModel):
    """
    Aggregated analytics for one organisation over an optional range.

    Combines the headline totals with the per-category and per-bucket
    breakdowns needed by the analytics dashboard. The counts respect the
    requested date range; when no range is given they cover all files.
    """

    total_files: int
    total_bytes: int
    by_type: list[FileTypeStat]
    by_bucket: list[FileBucketStat]
