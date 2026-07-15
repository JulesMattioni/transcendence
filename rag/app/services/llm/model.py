from pydantic import BaseModel


class LlmResponse(BaseModel):
    content: str
    model_name: str
    input_tokens: int = 0
    output_tokens: int = 0
