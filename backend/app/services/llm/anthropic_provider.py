import os
import time
from typing import Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from app.services.llm.base import BaseLLMProvider, LLMResponse

try:
    import anthropic
    _anthropic_available = True
except ImportError:
    _anthropic_available = False


class AnthropicProvider(BaseLLMProvider):
    provider_name = "anthropic"
    default_model = "claude-haiku-4-5-20251001"

    def __init__(self, model: Optional[str] = None):
        self.model = model or self.default_model
        self._client: Optional["anthropic.AsyncAnthropic"] = None

    def _get_client(self) -> "anthropic.AsyncAnthropic":
        if self._client is None:
            if not _anthropic_available:
                raise ImportError("anthropic package is not installed")
            self._client = anthropic.AsyncAnthropic(
                api_key=os.environ.get("ANTHROPIC_API_KEY")
            )
        return self._client

    def is_available(self) -> bool:
        return _anthropic_available and bool(os.environ.get("ANTHROPIC_API_KEY"))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        model = kwargs.get("model", self.model)
        max_tokens = kwargs.get("max_tokens", 2048)
        start = time.time()
        try:
            client = self._get_client()
            response = await client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            latency_ms = int((time.time() - start) * 1000)
            response_text = response.content[0].text if response.content else ""
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            return LLMResponse(
                provider=self.provider_name,
                model=model,
                prompt_text=prompt,
                response_text=response_text,
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                success=True,
            )
        except Exception as e:
            latency_ms = int((time.time() - start) * 1000)
            return LLMResponse(
                provider=self.provider_name,
                model=model,
                prompt_text=prompt,
                response_text="",
                tokens_used=None,
                latency_ms=latency_ms,
                error=str(e),
                success=False,
            )
