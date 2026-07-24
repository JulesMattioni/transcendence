import asyncio
import json
import re
from typing import Any, AsyncIterator
import httpx
from pydantic import ValidationError
from shared.base_service import BaseService
from .key_manager import KeyManager
from .model import LlmResponse


class OpenAICompatibleService(BaseService):
    """LLM service for any OpenAI-compatible chat-completions API.

    Works with any provider exposing ``/chat/completions`` (Groq,
    OpenRouter, etc.); the target is selected purely by ``base_url``.
    """

    RATE_LIMIT_MAX_WAIT = 120

    def __init__(self, model_name: str, base_url: str) -> None:
        """
        Initialize the client for one model on one provider.

        Args:
            model_name: Model identifier sent in each request.
            base_url: Provider base URL exposing /chat/completions.
        """

        super().__init__()
        self._key_manager = KeyManager()
        self.model_name = model_name
        self.base_url = base_url

    async def generate(
        self,
        messages: list[dict[str, Any]],
        stop_sequences: list[str] | None = None,
        max_tokens: int | None = None,
    ) -> LlmResponse:
        """
        Send a chat-completion request and return the model's reply.

        Retries around transient failures: rate limits rotate through the
        key pool before backing off, network and 5xx errors back off with
        capped exponential delay, and 400/401/403 marks the current key
        dead and rotates to the next.

        Args:
            messages: Chat messages to send.
            stop_sequences: Optional strings that stop generation.
            max_tokens: Optional cap on generated tokens.

        Returns:
            LlmResponse with the content and token usage.

        Raises:
            ValueError: When retries are exhausted, every key is rejected
            or rate-limited, or the response cannot be parsed.
        """

        max_rate_limit_retries = 6
        max_server_retries = 4

        rate_limit_retries = 0
        rate_limit_sweep = 0
        server_retries = 0

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(120.0, connect=10.0)
        ) as client:
            while True:
                payload: dict[str, Any] = {
                    "messages": messages,
                    "model": self.model_name,
                    "tool_choice": "none",
                }
                if stop_sequences:
                    payload["stop"] = stop_sequences
                if max_tokens:
                    payload["max_tokens"] = max_tokens
                headers = {
                    "Authorization": f"Bearer {self._key_manager.current_key}",
                    "Content-Type": "application/json",
                }

                try:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        content=json.dumps(payload),
                    )
                except httpx.RequestError as e:
                    server_retries += 1
                    if server_retries > max_server_retries:
                        raise ValueError(f"Network error: {e}")
                    backoff = min(2**server_retries, 30)
                    await asyncio.sleep(backoff)
                    continue

                if response.status_code == 200:
                    data = response.json()
                    message = data["choices"][0]["message"]
                    content = (
                        message.get("content")
                        or message.get("reasoning_content")
                        or message.get("reasoning")
                        or ""
                    )
                    usage = data.get("usage") or {}

                    try:
                        return LlmResponse(
                            content=content,
                            model_name=self.model_name,
                            input_tokens=usage.get("prompt_tokens", 0),
                            output_tokens=usage.get("completion_tokens", 0),
                        )
                    except ValidationError as e:
                        raise ValueError(f"Error in response format: {e}")

                elif response.status_code == 429 or (
                    response.status_code == 413
                    and "rate_limit_exceeded" in (response.text or "")
                ):
                    rate_limit_sweep += 1
                    if rate_limit_sweep < self._key_manager.live_count:
                        self._key_manager.rotate_key()
                        continue
                    rate_limit_sweep = 0
                    rate_limit_retries += 1
                    if rate_limit_retries > max_rate_limit_retries:
                        raise ValueError("All API keys rate limit used.")
                    wait = self._parse_retry_after(response, 5)
                    if wait > self.RATE_LIMIT_MAX_WAIT:
                        raise ValueError(
                            f"Rate limit requires waiting {wait}s, over the "
                            f"{self.RATE_LIMIT_MAX_WAIT}s cap; aborting."
                        )
                    self._key_manager.rotate_key()
                    await asyncio.sleep(wait)

                elif response.status_code in [400, 401, 403]:
                    self._key_manager.mark_current_dead()
                    if self._key_manager.rotate_key() is None:
                        raise ValueError(
                            f"Request rejected by provider ({self.base_url}) "
                            f"with all available keys: {response.text}"
                        )

                elif response.status_code >= 500:
                    server_retries += 1
                    if server_retries > max_server_retries:
                        raise ValueError(
                            f"Server error {response.status_code} persisted."
                        )
                    backoff = min(2**server_retries, 30)
                    await asyncio.sleep(backoff)

                else:
                    raise ValueError(
                        (
                            f"Unknown error {response.status_code}: "
                            f"{response.text}"
                        )
                    )

    async def generate_stream(
        self,
        messages: list[dict[str, Any]],
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """
        Stream a chat completion token by token.

        Opens a streaming request and yields each content delta as it
        arrives, stopping at the [DONE] sentinel. Unlike generate, this
        path does not rotate keys or retry: it is used for the final
        answer where partial output has already been sent.

        Args:
            messages: Chat messages to send.
            max_tokens: Optional cap on generated tokens.

        Yields:
            Content fragments in arrival order.

        Raises:
            ValueError: If the provider returns a non-200 status.
        """

        payload: dict[str, Any] = {
            "messages": messages,
            "model": self.model_name,
            "stream": True,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        headers = {
            "Authorization": f"Bearer {self._key_manager.current_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(120.0, connect=10.0)
        ) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                content=json.dumps(payload),
            ) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    raise ValueError(
                        f"LLM stream error {response.status_code}: "
                        f"{body.decode()}"
                    )

                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[len("data:"):].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    delta = chunk["choices"][0].get("delta", {})
                    token = delta.get("content")
                    if token:
                        yield token

    def _parse_retry_after(
        self, response: httpx.Response, default: float
    ) -> float:
        """
        Extract how long to wait before retrying a rate-limited request.

        Reads the provider's hint from the standard Retry-After headers
        (Groq-style, seconds or milliseconds) or from the response body
        (Gemini-style retryDelay / "retry in Ns"), falling back to a
        default when none is present or parseable.

        Args:
            response: The rate-limited HTTP response.
            default: Seconds to wait when no hint is found.

        Returns:
            The number of seconds to wait before retrying.
        """

        # Groq-style
        retry_after = response.headers.get("retry-after")
        if retry_after is not None:
            try:
                return float(retry_after)
            except ValueError:
                pass

        retry_after_ms = response.headers.get("retry-after-ms")
        if retry_after_ms is not None:
            try:
                return float(retry_after_ms) / 1000.0
            except ValueError:
                pass

        # Gemini-style
        body = response.text or ""
        match = re.search(r'"retryDelay"\s*:\s*"([0-9.]+)s"', body)
        if not match:
            match = re.search(r"retry in ([0-9.]+)s", body)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass

        return default
