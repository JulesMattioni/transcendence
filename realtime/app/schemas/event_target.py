from pydantic import BaseModel, ConfigDict, Field

class EventTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: str = Field(min_length=1)
    id: int