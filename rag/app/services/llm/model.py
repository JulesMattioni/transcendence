from pydantic import BaseModel


class LlmResponse(BaseModel):
    """
    A completed LLM reply with its content and token usage.

    Token counts default to 0 when the provider omits usage data.
    """

    content: str
    model_name: str
    input_tokens: int = 0
    output_tokens: int = 0
