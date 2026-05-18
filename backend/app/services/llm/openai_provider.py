import os
import time
from typing import Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from app.services.llm.base import BaseLLMProvider, LLMResponse

try:
    import openai
    _openai_available = True
except ImportError:
    _openai_available = False


class OpenAIProvider(BaseLLMProvider):
    provider_name = "openai"
    default_model = "gpt-4o-mini"

    def __init__(self, model: Optional[str] = None):
        self.model = model or self.default_model
        self._client: Optional["openai.AsyncOpenAI"] = None

    def _get_client(self) -> "openai.AsyncOpenAI":
        if self._client is None:
            if not _openai_available:
                raise ImportError("openai package is not installed")
            self._client = openai.AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        return self._client

    def is_available(self) -> bool:
        return _openai_available and bool(os.environ.get("OPENAI_API_KEY"))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        model = kwargs.get("model", self.model)
        start = time.time()
        try:
            client = self._get_client()
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **{k: v for k, v in kwargs.items() if k != "model"},
            )
            latency_ms = int((time.time() - start) * 1000)
            response_text = response.choices[0].message.content or ""
            tokens_used = (
                response.usage.total_tokens if response.usage else None
            )
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
